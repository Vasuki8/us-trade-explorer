import { constants } from 'node:fs';
import { lstat, open } from 'node:fs/promises';
import {
  createServer,
  type IncomingMessage,
  type Server,
  type ServerResponse,
} from 'node:http';
import { isAbsolute, join, parse, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  loadResearchCandidate,
  validateResearchManifest,
  type ResearchCandidate,
} from '../../packages/contracts/research-candidate.ts';
import { renderReview } from './view.ts';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));
const MAX_INPUT_BYTES = 72 * 1024;
const FIXTURE_LABEL = 'fabricated-for-contract-tests-not-official-data';
const INPUT_ERROR = 'Review input rejected.';
const START_ERROR = 'Review server could not start.';
const HEADERS = {
  'Content-Security-Policy':
    "default-src 'none'; style-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'",
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Cross-Origin-Resource-Policy': 'same-origin',
  Connection: 'close',
};

export type ReviewServerOptions = {
  candidatePath?: string;
  fixture?: boolean;
  port?: number;
  repositoryRoot?: string;
};

function requireInput(condition: unknown): asserts condition {
  if (!condition) throw new Error(INPUT_ERROR);
}

function fields(
  input: unknown,
  names: string[],
): asserts input is Record<string, unknown> {
  requireInput(
    input !== null && typeof input === 'object' && !Array.isArray(input),
  );
  const keys = Object.keys(input);
  requireInput(
    keys.length === names.length &&
      names.every((key) => Object.hasOwn(input, key)),
  );
}

// Reject duplicate names before JSON.parse can silently discard earlier values.
// The fixture permits indentation; real candidates additionally require exact canonical bytes.
function parseInput(bytes: Buffer): unknown {
  requireInput(!(bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf));
  const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  let position = 0;
  let nodes = 0;
  const whitespace = () => {
    while (/[\t\n\r ]/.test(text[position] ?? '\0')) position++;
  };
  function string(): string {
    requireInput(text[position] === '"');
    const start = position++;
    while (position < text.length) {
      const c = text[position++];
      if (c === '\\') position++;
      else if (c === '"') return JSON.parse(text.slice(start, position));
    }
    throw new Error(INPUT_ERROR);
  }
  function value(depth: number): void {
    requireInput(++nodes <= 2500 && depth <= 16);
    whitespace();
    const c = text[position];
    if (c === '{') {
      position++;
      whitespace();
      const names = new Set<string>();
      if (text[position] === '}') {
        position++;
        return;
      }
      while (true) {
        whitespace();
        const key = string();
        requireInput(!names.has(key));
        names.add(key);
        whitespace();
        requireInput(text[position++] === ':');
        value(depth + 1);
        whitespace();
        const separator = text[position++];
        if (separator === '}') return;
        requireInput(separator === ',');
      }
    }
    if (c === '[') {
      position++;
      whitespace();
      if (text[position] === ']') {
        position++;
        return;
      }
      while (true) {
        value(depth + 1);
        whitespace();
        const separator = text[position++];
        if (separator === ']') return;
        requireInput(separator === ',');
      }
    }
    if (c === '"') {
      string();
      return;
    }
    const token = /^[^\s,\]}]+/.exec(text.slice(position));
    requireInput(token);
    JSON.parse(token[0]);
    position += token[0].length;
  }
  value(0);
  whitespace();
  requireInput(position === text.length);
  return JSON.parse(text);
}

// Independent producer-compatible encoding, before delegating checksum/schema checks
// to the contract. Numbers in a valid candidate are small schema/byte-count integers.
function canonical(input: unknown): string {
  if (Array.isArray(input)) return `[${input.map(canonical).join(',')}]`;
  if (input !== null && typeof input === 'object') {
    const object = input as Record<string, unknown>;
    return `{${Object.keys(object)
      .sort()
      .map((key) => `${canonical(key)}:${canonical(object[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(input).replace(
    /[\u007f-\uffff]/g,
    (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`,
  );
}

async function inspectPath(path: string) {
  const root = parse(path).root;
  const parts = path.slice(root.length).split(sep).filter(Boolean);
  let current = root;
  let last = await lstat(current);
  for (let index = 0; index < parts.length; index++) {
    requireInput(!parts[index].includes(':'));
    current = join(current, parts[index]);
    last = await lstat(current);
    requireInput(!last.isSymbolicLink());
    requireInput(
      index === parts.length - 1 ? last.isFile() : last.isDirectory(),
    );
  }
  requireInput(last.isFile());
  return last;
}

async function readBoundedFile(path: string): Promise<Buffer> {
  const before = await inspectPath(path);
  requireInput(before.size > 0 && before.size <= MAX_INPUT_BYTES);
  const handle = await open(
    path,
    constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0),
  );
  try {
    const opened = await handle.stat();
    requireInput(
      opened.isFile() && opened.size > 0 && opened.size <= MAX_INPUT_BYTES,
    );
    requireInput(opened.dev === before.dev && opened.ino === before.ino);
    const afterOpen = await inspectPath(path);
    requireInput(afterOpen.dev === opened.dev && afterOpen.ino === opened.ino);
    // Allocate one bounded extra byte so growth after stat cannot turn this into
    // an unbounded read or silently truncate an oversized file.
    const buffer = Buffer.alloc(MAX_INPUT_BYTES + 1);
    let length = 0;
    while (length < buffer.length) {
      const { bytesRead } = await handle.read(
        buffer,
        length,
        buffer.length - length,
        length,
      );
      if (bytesRead === 0) break;
      length += bytesRead;
    }
    requireInput(length > 0 && length <= MAX_INPUT_BYTES);
    return buffer.subarray(0, length);
  } finally {
    await handle.close();
  }
}

async function loadSnapshot(options: ReviewServerOptions): Promise<{
  data: ResearchCandidate;
  css: string;
  mode: 'candidate' | 'fixture';
  port: number;
}> {
  requireInput(
    options !== null && typeof options === 'object' && !Array.isArray(options),
  );
  requireInput(
    Object.keys(options).every((key) =>
      ['candidatePath', 'fixture', 'port', 'repositoryRoot'].includes(key),
    ),
  );
  requireInput(
    options.fixture === undefined || typeof options.fixture === 'boolean',
  );
  const mode = options.fixture === true ? 'fixture' : 'candidate';
  requireInput(
    mode === 'fixture'
      ? options.candidatePath === undefined
      : typeof options.candidatePath === 'string' &&
          options.candidatePath.length > 0,
  );
  const port = options.port ?? 4322;
  requireInput(Number.isInteger(port) && port >= 0 && port <= 65535);
  requireInput(
    options.repositoryRoot === undefined ||
      (typeof options.repositoryRoot === 'string' &&
        options.repositoryRoot.length > 0),
  );
  const root = resolve(options.repositoryRoot ?? ROOT);
  let path: string;
  if (mode === 'fixture')
    path = join(root, 'tests/fixtures/research-candidate.example.json');
  else {
    path = resolve(root, options.candidatePath!);
    const withinLocal = relative(join(root, '.local'), path);
    requireInput(
      withinLocal.length > 0 &&
        withinLocal !== '..' &&
        !withinLocal.startsWith(`..${sep}`) &&
        !isAbsolute(withinLocal),
    );
  }
  const bytes = await readBoundedFile(path);
  let bundle = parseInput(bytes);
  if (mode === 'fixture') {
    fields(bundle, ['fixtureType', 'bundle']);
    requireInput(bundle.fixtureType === FIXTURE_LABEL);
    bundle = bundle.bundle;
  } else requireInput(bytes.equals(Buffer.from(canonical(bundle), 'ascii')));
  fields(bundle, ['manifest', 'data']);
  const manifest = validateResearchManifest(bundle.manifest);
  const dataBytes = Buffer.from(canonical(bundle.data), 'ascii');
  const data = await loadResearchCandidate(manifest, () => dataBytes);
  const css = new TextDecoder('utf-8', { fatal: true }).decode(
    await readBoundedFile(
      fileURLToPath(new URL('./review.css', import.meta.url)),
    ),
  );
  return { data, css, mode, port };
}

function send(
  req: IncomingMessage,
  res: ServerResponse,
  status: number,
  body: string,
  type = 'text/plain; charset=utf-8',
  extra: Record<string, string> = {},
) {
  res.writeHead(status, {
    ...HEADERS,
    'Content-Type': type,
    'Content-Length': Buffer.byteLength(body),
    ...extra,
  });
  res.end(req.method === 'HEAD' ? undefined : body);
}

function headerCount(req: IncomingMessage, name: string): number {
  let count = 0;
  for (let index = 0; index < req.rawHeaders.length; index += 2)
    if (req.rawHeaders[index].toLowerCase() === name) count++;
  return count;
}

export async function startReviewServer(
  options: ReviewServerOptions,
): Promise<Server> {
  let snapshot: Awaited<ReturnType<typeof loadSnapshot>>;
  try {
    snapshot = await loadSnapshot(options);
  } catch {
    throw new Error(INPUT_ERROR);
  }
  const { data, css, mode, port } = snapshot;
  const server = createServer(
    {
      maxHeaderSize: 8192,
      requireHostHeader: false,
      headersTimeout: 5000,
      requestTimeout: 5000,
      connectionsCheckingInterval: 1000,
    },
    (req, res) => {
      try {
        const address = server.address();
        if (!address || typeof address === 'string')
          return send(req, res, 503, 'Review unavailable.');
        const host = `127.0.0.1:${address.port}`;
        if (req.rawHeaders.length > 64)
          return send(req, res, 431, 'Request rejected.');
        if (
          headerCount(req, 'host') !== 1 ||
          req.headers.host !== host ||
          headerCount(req, 'origin') > 1 ||
          (req.headers.origin !== undefined &&
            req.headers.origin !== `http://${host}`) ||
          headerCount(req, 'sec-fetch-site') > 1 ||
          (req.headers['sec-fetch-site'] !== undefined &&
            !['none', 'same-origin'].includes(
              String(req.headers['sec-fetch-site']),
            ))
        )
          return send(req, res, 403, 'Request rejected.');
        if (req.method !== 'GET' && req.method !== 'HEAD')
          return send(req, res, 405, 'Method not allowed.', undefined, {
            Allow: 'GET, HEAD',
          });
        if (
          (req.headers['content-length'] !== undefined &&
            req.headers['content-length'] !== '0') ||
          req.headers['transfer-encoding'] !== undefined
        )
          return send(req, res, 400, 'Request rejected.');
        const target = req.url ?? '';
        if (target.length > 2048)
          return send(req, res, 414, 'Request rejected.');
        if (!target.startsWith('/') || target.startsWith('//'))
          return send(req, res, 400, 'Request rejected.');
        if (target === '/review.css')
          return send(req, res, 200, css, 'text/css; charset=utf-8');
        const page = renderReview(data, target, mode);
        return send(
          req,
          res,
          page.status,
          page.html,
          'text/html; charset=utf-8',
          page.location ? { Location: page.location } : {},
        );
      } catch {
        return send(req, res, 500, 'Review unavailable.');
      }
    },
  );
  server.maxHeadersCount = 0; // Inspect every name; bytes and the handler bound their count.
  server.maxConnections = 32;
  server.keepAliveTimeout = 1000;
  server.setTimeout(5000, (socket) => socket.destroy());
  // Do not let Node emit automatic 100/417 responses ahead of our fixed policy.
  server.on('checkContinue', (req, res) =>
    send(req, res, 400, 'Request rejected.'),
  );
  server.on('checkExpectation', (req, res) =>
    send(req, res, 400, 'Request rejected.'),
  );
  server.on('clientError', (error: NodeJS.ErrnoException, socket) => {
    if (!socket.writable) return socket.destroy();
    const status =
      error.code === 'HPE_HEADER_OVERFLOW'
        ? '431 Request Header Fields Too Large'
        : '400 Bad Request';
    const headers = Object.entries({
      ...HEADERS,
      'Content-Type': 'text/plain; charset=utf-8',
      'Content-Length': '17',
    })
      .map(([name, value]) => `${name}: ${value}`)
      .join('\r\n');
    socket.end(`HTTP/1.1 ${status}\r\n${headers}\r\n\r\nRequest rejected.`);
  });
  try {
    await new Promise<void>((done, reject) => {
      server.once('error', reject);
      server.listen({ host: '127.0.0.1', port, exclusive: true }, () => {
        server.off('error', reject);
        done();
      });
    });
  } catch {
    server.close();
    throw new Error(START_ERROR);
  }
  return server;
}

function cliOptions(args: string[]): ReviewServerOptions {
  const options: ReviewServerOptions = {};
  const seen = new Set<string>();
  for (let index = 0; index < args.length; index++) {
    const flag = args[index];
    requireInput(!seen.has(flag));
    seen.add(flag);
    if (flag === '--fixture') options.fixture = true;
    else if (flag === '--candidate') {
      requireInput(
        Boolean(args[index + 1]) && !args[index + 1].startsWith('--'),
      );
      options.candidatePath = args[++index];
    } else if (flag === '--port') {
      const value = args[++index];
      requireInput(
        typeof value === 'string' && /^[1-9][0-9]{0,4}$/.test(value),
      );
      options.port = Number(value);
      requireInput(options.port <= 65535);
    } else throw new Error(INPUT_ERROR);
  }
  return options;
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const server = await startReviewServer(cliOptions(process.argv.slice(2)));
    const address = server.address();
    if (!address || typeof address === 'string') throw new Error(START_ERROR);
    process.stdout.write(`http://127.0.0.1:${address.port}\n`);
  } catch (error) {
    process.stderr.write(
      `${error instanceof Error && error.message === START_ERROR ? START_ERROR : INPUT_ERROR}\n`,
    );
    process.exitCode = 1;
  }
}
