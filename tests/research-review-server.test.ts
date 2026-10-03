import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';
import {
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import { request, type Server } from 'node:http';
import { connect, createServer } from 'node:net';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { startReviewServer } from '../tools/research-review/server.ts';

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));
const fixturePath = join(
  repositoryRoot,
  'tests/fixtures/research-candidate.example.json',
);
const fixture = JSON.parse(await readFile(fixturePath, 'utf8'));
// Independent test serialization of the producer's documented Python format.
const canonical = (value: any): string => {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object')
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${canonical(key)}:${canonical(value[key])}`)
      .join(',')}}`;
  return JSON.stringify(value).replace(
    /[\u007f-\uffff]/g,
    (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`,
  );
};
const validBytes = canonical(fixture.bundle);

test('CSV attachments preserve context and HEAD metadata without bypassing request controls', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    const path = '/products/09.csv?flow=exports';
    const csv = await http(server, path);
    assert.equal(csv.status, 200);
    assert.equal(csv.headers['content-type'], 'text/csv; charset=utf-8');
    assert.match(
      csv.headers['content-disposition']!,
      /^attachment; filename="[a-z0-9._-]+\.csv"$/,
    );
    assert.match(csv.headers['content-disposition']!, /exports/);
    assert.match(csv.body, /fabricated/i);
    assert.match(csv.body, /unpublished/i);
    assert.match(csv.body, /ALL_VAL_MO/);
    assert.equal(
      Number(csv.headers['content-length']),
      Buffer.byteLength(csv.body),
    );
    assert.equal(csv.headers['cache-control'], 'no-store');
    assert.equal(csv.headers['x-content-type-options'], 'nosniff');
    assert.match(
      String(csv.headers['content-security-policy']),
      /default-src 'none'/,
    );
    const head = await http(server, path, {}, 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.body, '');
    assert.equal(head.headers['content-length'], csv.headers['content-length']);
    assert.equal(
      head.headers['content-disposition'],
      csv.headers['content-disposition'],
    );
    for (const headers of [
      { Host: 'evil.example' },
      { Origin: 'https://evil.example' },
      { 'Sec-Fetch-Site': 'cross-site' },
    ]) {
      const denied = await http(server, path, headers);
      assert.equal(denied.status, 403);
      assert.equal(denied.headers['content-disposition'], undefined);
      assert.doesNotMatch(denied.body, /ALL_VAL_MO/);
    }
    assert.equal((await http(server, path, {}, 'POST')).status, 405);
  } finally {
    await close(server);
  }
});

test('failed download routes return recoverable errors without attachment headers', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    for (const [path, status] of [
      ['/products/09.csv?flow=imports&flow=exports', 400],
      ['/countries/india.csv?flow=other', 400],
      ['/products/09.csv?filename=secret.csv', 400],
      ['/products/10.csv', 404],
      ['/sources.csv', 404],
      ['/.local/public-candidate/fresh.json.csv', 404],
      ['/countries/india/print.csv', 404],
    ] as const) {
      const response = await http(server, path);
      assert.equal(response.status, status, path);
      assert.equal(response.headers['content-disposition'], undefined);
      assert.match(response.headers['content-type']!, /^text\/html/);
      assert.match(response.body, /Reset view/);
    }
    const print = await http(server, '/countries/india/print?flow=exports');
    assert.equal(print.status, 200);
    assert.equal(print.headers['content-disposition'], undefined);
    assert.match(print.body, /summary/i);
    assert.match(print.body, /unpublished/i);
    assert.doesNotMatch(print.body, /<script\b/);
  } finally {
    await close(server);
  }
});
const portOf = (server: Server) => {
  const address = server.address();
  assert(address && typeof address === 'object');
  assert.equal(address.address, '127.0.0.1');
  return address.port;
};
async function close(server: Server) {
  server.closeAllConnections();
  await new Promise<void>((done, reject) =>
    server.close((error) => (error ? reject(error) : done())),
  );
}
async function temporaryRepository() {
  const parent = join(repositoryRoot, '.local');
  await mkdir(parent, { recursive: true });
  const root = await mkdtemp(join(parent, 'review-server-test-'));
  await mkdir(join(root, '.local'));
  return {
    root,
    path: join(root, '.local/candidate.json'),
    cleanup: async () => {
      assert(
        resolve(root).startsWith(resolve(parent) + '/review-server-test-') ||
          resolve(root).startsWith(resolve(parent) + '\\review-server-test-'),
      );
      await rm(root, { recursive: true, force: true });
    },
  };
}
async function http(
  server: Server,
  path = '/products/09',
  headers: Record<string, string | undefined> = {},
  method = 'GET',
) {
  return await new Promise<{
    status: number;
    headers: import('node:http').IncomingHttpHeaders;
    body: string;
  }>((done, reject) => {
    const req = request(
      {
        hostname: '127.0.0.1',
        port: portOf(server),
        path,
        method,
        headers,
        agent: false,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () =>
          done({
            status: res.statusCode!,
            headers: res.headers,
            body: Buffer.concat(chunks).toString('utf8'),
          }),
        );
      },
    );
    req.on('error', reject);
    req.end();
  });
}
async function raw(server: Server, message: string) {
  return await new Promise<string>((done, reject) => {
    const socket = connect(portOf(server), '127.0.0.1');
    let response = '';
    socket.setTimeout(3000, () =>
      socket.destroy(new Error('test socket timeout')),
    );
    socket.on('connect', () => socket.write(message));
    socket.on('data', (chunk) => (response += chunk.toString('utf8')));
    socket.on('end', () => done(response));
    socket.on('error', reject);
  });
}

test('explicit fabricated fixture starts a loopback server with a labelled HTML review', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    const response = await http(server);
    assert.equal(response.status, 200);
    assert.match(response.body, /fabricated/i);
    assert.match(response.body, /unpublished/i);
    assert.match(
      response.headers['content-type']!,
      /^text\/html; charset=utf-8$/,
    );
    assert.doesNotMatch(response.body, /<script\b/i);
  } finally {
    await close(server);
  }
});

test('every HTTP response uses restrictive browser and cache headers', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    for (const [path, headers, method] of [
      ['/products/09', {}, 'GET'],
      ['/', {}, 'GET'],
      ['/missing', {}, 'GET'],
      ['/review.css', {}, 'HEAD'],
      ['/products/09', { Origin: 'null' }, 'GET'],
      ['/products/09', {}, 'POST'],
    ] as const) {
      const response = await http(server, path, headers, method);
      assert.equal(response.headers['cache-control'], 'no-store');
      assert.equal(response.headers['x-robots-tag'], 'noindex, nofollow');
      assert.equal(response.headers['x-content-type-options'], 'nosniff');
      assert.equal(response.headers['x-frame-options'], 'DENY');
      assert.equal(response.headers['referrer-policy'], 'no-referrer');
      assert.equal(
        response.headers['cross-origin-resource-policy'],
        'same-origin',
      );
      assert.equal(
        response.headers['content-security-policy'],
        "default-src 'none'; style-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'",
      );
      assert.equal(response.headers['access-control-allow-origin'], undefined);
    }
  } finally {
    await close(server);
  }
});

test('only exact loopback Host and absent or same-origin Origin/Fetch-Metadata are allowed', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    const origin = `http://127.0.0.1:${portOf(server)}`;
    for (const headers of [
      { Host: 'evil.invalid' },
      { Host: `localhost:${portOf(server)}` },
      { Host: '127.0.0.1' },
      { Host: '127.0.0.1:1' },
      { Origin: 'https://evil.invalid' },
      { Origin: 'null' },
      { Origin: origin + '/' },
      { 'Sec-Fetch-Site': 'cross-site' },
      { 'Sec-Fetch-Site': 'same-site' },
    ])
      assert.equal((await http(server, '/products/09', headers)).status, 403);
    for (const headers of [
      {},
      { Origin: origin },
      { 'Sec-Fetch-Site': 'none' },
      { 'Sec-Fetch-Site': 'same-origin', Origin: origin },
    ])
      assert.equal((await http(server, '/products/09', headers)).status, 200);
    for (const block of [
      `Host: 127.0.0.1:${portOf(server)}\r\nHost: evil.invalid`,
      `Host: 127.0.0.1:${portOf(server)}\r\nOrigin: ${origin}\r\nOrigin: ${origin}`,
      `Host: 127.0.0.1:${portOf(server)}\r\nSec-Fetch-Site: none\r\nSec-Fetch-Site: none`,
      'User-Agent: test',
    ])
      assert.match(
        await raw(
          server,
          `GET /products/09 HTTP/1.1\r\n${block}\r\nConnection: close\r\n\r\n`,
        ),
        /^HTTP\/1\.1 (400|403) /,
      );
  } finally {
    await close(server);
  }
});

test('GET and HEAD serve a fixed stylesheet and no filesystem or dataset endpoints', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    const page = await http(server);
    const head = await http(server, '/products/09', {}, 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.body, '');
    assert.equal(
      head.headers['content-length'],
      String(Buffer.byteLength(page.body)),
    );
    const css = await http(server, '/review.css');
    assert.equal(css.status, 200);
    assert.equal(css.headers['content-type'], 'text/css; charset=utf-8');
    assert.match(css.body, /body/);
    for (const path of [
      '/review.css?file=candidate.json',
      '/candidate.json',
      '/api/data',
      '/.local/candidate.json',
      '/tests/fixtures/research-candidate.example.json',
      '/../package.json',
      '/%2e%2e/package.json',
    ]) {
      const response = await http(server, path);
      assert(response.status === 400 || response.status === 404);
      assert.doesNotMatch(
        response.body,
        /contentHash|fixtureType|devDependencies/,
      );
    }
    for (const method of ['POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE']) {
      const response = await http(server, '/products/09', {}, method);
      assert.equal(response.status, 405);
      assert.equal(response.headers.allow, 'GET, HEAD');
    }
  } finally {
    await close(server);
  }
});

test('oversized request targets, headers, absolute targets and request bodies fail without reflecting input', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    const secret = 'request-private-marker';
    const target = await http(server, '/' + secret.repeat(120));
    assert.equal(target.status, 414);
    assert.doesNotMatch(target.body, new RegExp(secret));
    const oversized = await raw(
      server,
      `GET /products/09 HTTP/1.1\r\nHost: 127.0.0.1:${portOf(server)}\r\nX-Long: ${secret.repeat(500)}\r\nConnection: close\r\n\r\n`,
    );
    assert.match(oversized, /^HTTP\/1\.1 431 /);
    assert.doesNotMatch(oversized, new RegExp(secret));
    assert.equal(
      (await http(server, `http://127.0.0.1:${portOf(server)}/products/09`))
        .status,
      400,
    );
    assert.equal(
      (await http(server, '/products/09', { 'Content-Length': '1' })).status,
      400,
    );
    assert.equal(
      (await http(server, '/products/09', { 'Transfer-Encoding': 'chunked' }))
        .status,
      400,
    );
  } finally {
    await close(server);
  }
});

test('idle incomplete requests are disconnected within the local server time bound', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    await new Promise<void>((done, reject) => {
      const socket = connect(portOf(server), '127.0.0.1');
      const deadline = setTimeout(
        () => socket.destroy(new Error('incomplete request was not bounded')),
        8000,
      );
      socket.on('connect', () => socket.write('GET /products/09 HTTP/1.1\r\n'));
      socket.on('data', () => {});
      socket.on('close', () => {
        clearTimeout(deadline);
        done();
      });
      socket.on('error', reject);
    });
  } finally {
    await close(server);
  }
});

test('HTTP expectations cannot trigger automatic unguarded responses', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  try {
    for (const expectation of ['100-continue', 'private-expectation-marker']) {
      const response = await raw(
        server,
        `GET /products/09 HTTP/1.1\r\nHost: 127.0.0.1:${portOf(server)}\r\nExpect: ${expectation}\r\nConnection: close\r\n\r\n`,
      );
      assert.match(response, /^HTTP\/1\.1 400 /);
      assert.match(response, /Cache-Control: no-store/i);
      assert.match(response, /Content-Security-Policy:/i);
      assert.doesNotMatch(
        response,
        /private-expectation-marker|100 Continue|fabricated/,
      );
    }
  } finally {
    await close(server);
  }
});

test('excess simultaneous connections are dropped while existing requests stay bounded', async () => {
  const server = await startReviewServer({ fixture: true, port: 0 });
  const sockets: ReturnType<typeof connect>[] = [];
  try {
    for (let index = 0; index < 32; index++) {
      const socket = connect(portOf(server), '127.0.0.1');
      sockets.push(socket);
      await new Promise<void>((done, reject) => {
        socket.once('connect', done);
        socket.once('error', reject);
      });
    }
    await new Promise<void>((done, reject) => {
      const extra = connect(portOf(server), '127.0.0.1');
      sockets.push(extra);
      const deadline = setTimeout(
        () => extra.destroy(new Error('excess connection was not bounded')),
        2000,
      );
      extra.once('close', () => {
        clearTimeout(deadline);
        done();
      });
      extra.once('error', reject);
    });
    assert(sockets.slice(0, 32).every((socket) => !socket.destroyed));
  } finally {
    sockets.forEach((socket) => socket.destroy());
    await close(server);
  }
});

test('a validated real candidate remains an immutable startup snapshot after its file changes', async () => {
  const temp = await temporaryRepository();
  let server: Server | undefined;
  try {
    await writeFile(temp.path, validBytes);
    server = await startReviewServer({
      candidatePath: '.local/candidate.json',
      repositoryRoot: temp.root,
      port: 0,
    });
    const first = await http(server);
    assert.equal(first.status, 200);
    assert.doesNotMatch(first.body, /fabricated/i);
    await writeFile(temp.path, '{"secret":"changed-after-startup"}');
    assert.equal((await http(server)).body, first.body);
  } finally {
    if (server) await close(server);
    await temp.cleanup();
  }
});

test('candidate parsing rejects noncanonical bytes, duplicate/extra keys, bad hashes and invalid contracts', async () => {
  const temp = await temporaryRepository();
  try {
    const rehash = (bundle: any) => {
      const bytes = Buffer.from(canonical(bundle.data));
      bundle.manifest.contentHash = createHash('sha256')
        .update(bytes)
        .digest('hex');
      bundle.manifest.contentBytes = bytes.length;
      return canonical(bundle);
    };
    const invalidData = structuredClone(fixture.bundle);
    invalidData.data.flows[0].countries[0].value = '11';
    const privateData = structuredClone(fixture.bundle);
    privateData.data.privateValue = 'sensitive-local-marker';
    const mutations = [
      Buffer.from(''),
      Buffer.from('null'),
      Buffer.from('{'),
      Buffer.from('[1]'),
      Buffer.from('\ufeff' + validBytes),
      Buffer.from(validBytes + '\n'),
      Buffer.from(JSON.stringify(fixture.bundle, null, 2)),
      Buffer.from(validBytes.replace('mat\\u00e9', 'maté')),
      Buffer.from(validBytes.replace('"data":', '"data":{},"data":')),
      Buffer.from(
        validBytes.replace(
          '"source":"census"',
          '"source":"census","source":"census"',
        ),
      ),
      Buffer.from(
        validBytes.replace('"data":', '"sensitive-local-marker":true,"data":'),
      ),
      Buffer.from(
        validBytes.replace(fixture.bundle.manifest.contentHash, '0'.repeat(64)),
      ),
      Buffer.from(rehash(invalidData)),
      Buffer.from(rehash(privateData)),
      Buffer.from(fixturePath),
      Buffer.alloc(72 * 1024 + 1, 32),
      Buffer.from([0xff, 0xfe]),
    ];
    for (const bytes of mutations) {
      await writeFile(temp.path, bytes);
      await assert.rejects(
        startReviewServer({
          candidatePath: temp.path,
          repositoryRoot: temp.root,
          port: 0,
        }),
        { message: 'Review input rejected.' },
      );
    }
  } finally {
    await temp.cleanup();
  }
});

test('fixture mode enforces its exact label and wrapper fields, including duplicate fields', async () => {
  const temp = await temporaryRepository();
  try {
    const path = join(
      temp.root,
      'tests/fixtures/research-candidate.example.json',
    );
    await mkdir(dirname(path), { recursive: true });
    const valid = JSON.stringify(fixture, null, 2);
    for (const value of [
      valid.replace(fixture.fixtureType, 'official-data'),
      valid.replace('"fixtureType":', '"extra":true,"fixtureType":'),
      valid.replace(
        '"fixtureType":',
        `"fixtureType":"${fixture.fixtureType}","fixtureType":`,
      ),
      valid.replace('"bundle":', '"bundle":{},"bundle":'),
      '\ufeff' + valid,
    ]) {
      await writeFile(path, value);
      await assert.rejects(
        startReviewServer({
          fixture: true,
          repositoryRoot: temp.root,
          port: 0,
        }),
        { message: 'Review input rejected.' },
      );
    }
  } finally {
    await temp.cleanup();
  }
});

test('candidate loading requires one explicit input and a regular file beneath repository .local', async () => {
  const temp = await temporaryRepository();
  try {
    await writeFile(temp.path, validBytes);
    await writeFile(join(temp.root, 'outside.json'), validBytes);
    await mkdir(join(temp.root, '.local/directory'));
    for (const options of [
      {},
      { fixture: false },
      { fixture: true, candidatePath: temp.path },
      { candidatePath: '' },
      { candidatePath: '.local/missing.json' },
      { candidatePath: 'outside.json' },
      { candidatePath: '.local/../outside.json' },
      { candidatePath: '.local/directory' },
      { candidatePath: '.local' },
      { candidatePath: temp.path, port: -1 },
      { candidatePath: temp.path, port: 65536 },
      { candidatePath: temp.path, port: 1.2 },
      { candidatePath: temp.path, port: NaN },
    ])
      await assert.rejects(
        startReviewServer({ repositoryRoot: temp.root, port: 0, ...options }),
        { message: 'Review input rejected.' },
      );
  } finally {
    await temp.cleanup();
  }
});

test('linked candidate directories, .local roots and repository roots are rejected', async () => {
  const temp = await temporaryRepository();
  try {
    await mkdir(join(temp.root, 'real'));
    await writeFile(join(temp.root, 'real/candidate.json'), validBytes);
    await symlink(
      join(temp.root, 'real'),
      join(temp.root, '.local/link'),
      process.platform === 'win32' ? 'junction' : 'dir',
    );
    await assert.rejects(
      startReviewServer({
        repositoryRoot: temp.root,
        candidatePath: '.local/link/candidate.json',
        port: 0,
      }),
      { message: 'Review input rejected.' },
    );
    const linkedRoot = join(temp.root, 'linked-repository');
    await symlink(
      temp.root,
      linkedRoot,
      process.platform === 'win32' ? 'junction' : 'dir',
    );
    await writeFile(temp.path, validBytes);
    await assert.rejects(
      startReviewServer({
        repositoryRoot: linkedRoot,
        candidatePath: '.local/candidate.json',
        port: 0,
      }),
      { message: 'Review input rejected.' },
    );
    const child = join(temp.root, 'child');
    await mkdir(child);
    await symlink(
      join(temp.root, 'real'),
      join(child, '.local'),
      process.platform === 'win32' ? 'junction' : 'dir',
    );
    await assert.rejects(
      startReviewServer({
        repositoryRoot: child,
        candidatePath: '.local/candidate.json',
        port: 0,
      }),
      { message: 'Review input rejected.' },
    );
  } finally {
    await temp.cleanup();
  }
});

test('a linked candidate file is rejected where file symlinks are supported', async (t) => {
  const temp = await temporaryRepository();
  try {
    await writeFile(join(temp.root, 'outside.json'), validBytes);
    try {
      await symlink(join(temp.root, 'outside.json'), temp.path, 'file');
    } catch (error: any) {
      if (error.code === 'EPERM') {
        t.skip('Windows file symlinks require developer mode or privilege');
        return;
      }
      throw error;
    }
    await assert.rejects(
      startReviewServer({
        repositoryRoot: temp.root,
        candidatePath: temp.path,
        port: 0,
      }),
      { message: 'Review input rejected.' },
    );
  } finally {
    await temp.cleanup();
  }
});

test('invalid input rejects before opening a listener and bind failures have a fixed message', async () => {
  const occupied = createServer();
  await new Promise<void>((done) => occupied.listen(0, '127.0.0.1', done));
  const address = occupied.address();
  assert(address && typeof address === 'object');
  try {
    await assert.rejects(startReviewServer({ port: address.port }), {
      message: 'Review input rejected.',
    });
    await assert.rejects(
      startReviewServer({ fixture: true, port: address.port }),
      { message: 'Review server could not start.' },
    );
  } finally {
    await new Promise<void>((done) => occupied.close(() => done()));
  }
});

test('CLI rejects missing/conflicting input, unsupported host options and invalid ports without leaking arguments', () => {
  const script = join(repositoryRoot, 'tools/research-review/server.ts');
  for (const args of [
    [],
    ['--fixture', '--candidate', 'private-marker'],
    ['--candidate'],
    ['--fixture', '--port', '0'],
    ['--fixture', '--port', '65536'],
    ['--fixture', '--port', '2.5'],
    ['--fixture', '--host', '0.0.0.0'],
    ['--fixture', '--fixture'],
    ['--candidate', 'private-marker'],
  ]) {
    const result = spawnSync(process.execPath, [script, ...args], {
      cwd: repositoryRoot,
      encoding: 'utf8',
      timeout: 5000,
    });
    assert.equal(result.status, 1);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr, 'Review input rejected.\n');
  }
});

test('CLI startup prints only its local URL and never logs request paths', async () => {
  const reservation = createServer();
  await new Promise<void>((done) => reservation.listen(0, '127.0.0.1', done));
  const address = reservation.address();
  assert(address && typeof address === 'object');
  const port = address.port;
  await new Promise<void>((done) => reservation.close(() => done()));
  const child = spawn(
    process.execPath,
    [
      join(repositoryRoot, 'tools/research-review/server.ts'),
      '--fixture',
      '--port',
      String(port),
    ],
    { cwd: repositoryRoot, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => (stdout += chunk.toString()));
  child.stderr.on('data', (chunk) => (stderr += chunk.toString()));
  const ended = new Promise<void>((done) => child.once('exit', () => done()));
  try {
    await new Promise<void>((done, reject) => {
      const deadline = setTimeout(
        () => reject(new Error('CLI did not start')),
        5000,
      );
      child.stdout.once('data', () => {
        clearTimeout(deadline);
        done();
      });
      child.once('error', (error) => {
        clearTimeout(deadline);
        reject(error);
      });
      child.once('exit', () => {
        clearTimeout(deadline);
        reject(new Error('CLI exited before startup'));
      });
    });
    assert.equal(stdout, `http://127.0.0.1:${port}\n`);
    await new Promise<void>((done, reject) => {
      const req = request(
        {
          hostname: '127.0.0.1',
          port,
          path: '/private-request-marker',
          agent: false,
        },
        (res) => {
          res.resume();
          res.on('end', done);
        },
      );
      req.on('error', reject);
      req.end();
    });
  } finally {
    child.kill();
    await ended;
  }
  assert.equal(stdout, `http://127.0.0.1:${port}\n`);
  assert.equal(stderr, '');
});
