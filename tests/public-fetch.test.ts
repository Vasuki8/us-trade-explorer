import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import type { Release } from '../packages/contracts/trade.ts';

const boundary = await import(
  new URL('../src/lib/public-fetch.ts', import.meta.url).href
).catch(() => ({}));
type FetchRelease = (
  manifest: unknown,
  releaseURL: string,
  pageURL: string,
  fetcher?: typeof fetch,
) => Promise<Release>;
function load(
  manifest: unknown,
  fetcher: typeof fetch,
  url = '/data/sample-2026-07-v1.json',
  page = 'https://sample.test/compare/',
): Promise<Release> {
  const fn = (boundary as Record<string, unknown>).fetchPublicRelease;
  assert.equal(typeof fn, 'function', 'Missing bounded public fetch interface');
  return (fn as FetchRelease)(manifest, url, page, fetcher);
}
const sample = JSON.parse(
  readFileSync(
    new URL('./fixtures/sample-release.json', import.meta.url),
    'utf8',
  ),
);
const manifest = JSON.parse(
  readFileSync(
    new URL('../releases/sample-2026-07-v1.manifest.json', import.meta.url),
    'utf8',
  ),
);
const bytes = new TextEncoder().encode(JSON.stringify(sample));
const fetching =
  (response: Response): typeof fetch =>
  async () =>
    response;
function streamed(chunks: Uint8Array[], headers?: HeadersInit) {
  let cancelled = 0;
  let reads = 0;
  const body = new ReadableStream<Uint8Array>(
    {
      pull(controller) {
        if (reads === chunks.length) controller.close();
        else controller.enqueue(chunks[reads++]);
      },
      cancel() {
        cancelled++;
      },
    },
    { highWaterMark: 0 },
  );
  return {
    response: new Response(body, { headers }),
    body,
    cancellations: () => cancelled,
    reads: () => reads,
  };
}

for (const headers of [
  undefined,
  { 'content-length': '1432', 'content-encoding': 'gzip' },
  { 'content-length': '999999999', 'content-encoding': 'br' },
])
  test(`authentic multichunk decoded bytes load with ${headers?.['content-encoding'] || 'absent'} length metadata`, async () => {
    const transport = streamed(
      [bytes.slice(0, 11), bytes.slice(11, 65537), bytes.slice(65537)],
      headers,
    );
    assert.deepEqual(
      await load(manifest, fetching(transport.response)),
      sample,
    );
    assert.equal(transport.body.locked, false);
    assert.equal(transport.cancellations(), 0);
  });

test('requests bind to the page origin without credentials or redirects', async () => {
  let signal: AbortSignal | null | undefined;
  const fetcher: typeof fetch = async (url, options) => {
    assert.equal(
      String(url),
      'https://sample.test/data/sample-2026-07-v1.json',
    );
    assert.equal(options?.credentials, 'omit');
    assert.equal(options?.mode, 'same-origin');
    assert.equal(options?.redirect, 'error');
    signal = options?.signal;
    assert.ok(signal instanceof AbortSignal);
    return new Response(bytes);
  };
  assert.deepEqual(await load(manifest, fetcher), sample);
  assert.equal(signal?.aborted, false);
});

test('copies mutable stream chunks before another read can reuse their storage', async () => {
  const buffer = new Uint8Array(bytes.length);
  let reads = 0;
  const body = new ReadableStream<Uint8Array>(
    {
      pull(controller) {
        if (reads++ === 0) {
          buffer.set(bytes.subarray(0, 100));
          controller.enqueue(buffer.subarray(0, 100));
        } else if (reads === 2) {
          buffer.fill(0);
          buffer.set(bytes.subarray(100));
          controller.enqueue(buffer.subarray(0, bytes.length - 100));
        } else {
          buffer.fill(0);
          controller.close();
        }
      },
    },
    { highWaterMark: 0 },
  );
  assert.deepEqual(await load(manifest, fetching(new Response(body))), sample);
  assert.equal(body.locked, false);
});

test('invalid official or private metadata rejects before any network callback', async () => {
  let fetched = 0;
  const fetcher: typeof fetch = async () => {
    fetched++;
    return new Response(bytes);
  };
  for (const input of [
    null,
    { ...manifest, mode: 'official', source: 'census' },
    { ...manifest, artifact: 'private-candidate' },
    { ...manifest, rawHash: 'private' },
    { ...manifest, contentBytes: 512 * 1024 + 1 },
  ])
    await assert.rejects(() => load(input, fetcher));
  assert.equal(fetched, 0);
});

test('rejects off-origin, credentials, non-HTTP and mutable URL components before fetch', async () => {
  let fetched = 0;
  const fetcher: typeof fetch = async () => {
    fetched++;
    return new Response(bytes);
  };
  for (const url of [
    'https://other.test/release.json',
    '//other.test/release.json',
    'https://user:secret@sample.test/release.json',
    'data:application/json,{}',
    'file:///release.json',
    '/data/release.json?unreviewed=1',
    '/data/release.json#other',
  ])
    await assert.rejects(() => load(manifest, fetcher, url));
  await assert.rejects(() =>
    load(manifest, fetcher, '/data/release.json', 'file:///compare/'),
  );
  assert.equal(fetched, 0);
});

for (const size of [bytes.length + 1, 512 * 1024 + 1])
  test(`rejects ${size}-byte overflow before accumulating and cancels remaining data`, async () => {
    const transport = streamed([new Uint8Array(size), bytes]);
    let signal: AbortSignal | null | undefined;
    await assert.rejects(
      () =>
        load(manifest, async (_url, options) => {
          signal = options?.signal;
          return transport.response;
        }),
      /size|byte|oversized|overflow/i,
    );
    assert.equal(transport.reads(), 1);
    assert.equal(transport.cancellations(), 1);
    assert.equal(transport.body.locked, false);
    assert.equal(signal?.aborted, true);
  });

test('failed status cancels its unread body', async () => {
  const transport = streamed([bytes]);
  const response = new Response(transport.body, { status: 503 });
  await assert.rejects(() => load(manifest, fetching(response)));
  assert.equal(transport.reads(), 0);
  assert.equal(transport.cancellations(), 1);
  assert.equal(transport.body.locked, false);
});

test('absent response body rejects', async () => {
  await assert.rejects(() => load(manifest, fetching(new Response(null))));
});

for (const chunks of [[], [bytes.slice(0, -1)]])
  test(`rejects ${chunks.length ? 'truncated' : 'empty'} bodies and releases the reader`, async () => {
    const transport = streamed(chunks);
    let signal: AbortSignal | null | undefined;
    await assert.rejects(() =>
      load(manifest, async (_url, options) => {
        signal = options?.signal;
        return transport.response;
      }),
    );
    assert.equal(transport.body.locked, false);
    assert.equal(signal?.aborted, true);
  });

test('read failures abort transport and release the reader', async () => {
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      controller.error(new Error('read failure'));
    },
  });
  let signal: AbortSignal | null | undefined;
  await assert.rejects(() =>
    load(manifest, async (_url, options) => {
      signal = options?.signal;
      return new Response(body);
    }),
  );
  assert.equal(body.locked, false);
  assert.equal(signal?.aborted, true);
});

test('otherwise-valid changed bytes reject through the pinned loader', async () => {
  const altered = structuredClone(sample);
  altered.partners[0].name = 'Altered public description';
  const transport = streamed([
    new TextEncoder().encode(JSON.stringify(altered)),
  ]);
  await assert.rejects(() => load(manifest, fetching(transport.response)));
  assert.equal(transport.body.locked, false);
});

test('equal-size tampering fails checksum and aborts transport', async () => {
  const altered = bytes.slice();
  altered[new TextDecoder().decode(bytes).indexOf('Canada')] = 'K'.charCodeAt(
    0,
  );
  let signal: AbortSignal | null | undefined;
  const transport = streamed([altered]);
  await assert.rejects(
    () =>
      load(manifest, async (_url, options) => {
        signal = options?.signal;
        return transport.response;
      }),
    /checksum/i,
  );
  assert.equal(transport.body.locked, false);
  assert.equal(signal?.aborted, true);
});

test('deadline covers a stalled successful response body and cancels/releases it', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] });
  let started!: () => void;
  const reading = new Promise<void>((resolve) => {
    started = resolve;
  });
  let cancelled = 0;
  const body = new ReadableStream<Uint8Array>(
    {
      pull() {
        started();
      },
      cancel() {
        cancelled++;
      },
    },
    { highWaterMark: 0 },
  );
  let signal: AbortSignal | null | undefined;
  const pending = load(manifest, async (_url, options) => {
    signal = options?.signal;
    return new Response(body);
  });
  const rejection = assert.rejects(pending, /timeout|deadline|abort/i);
  await reading;
  context.mock.timers.tick(14999);
  assert.equal(signal?.aborted, false);
  context.mock.timers.tick(1);
  await rejection;
  assert.equal(signal?.aborted, true);
  assert.equal(cancelled, 1);
  assert.equal(body.locked, false);
});

test('deadline also bounds a fetch callback that never resolves', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] });
  let signal: AbortSignal | null | undefined;
  const pending = load(manifest, async (_url, options) => {
    signal = options?.signal;
    return new Promise<Response>(() => {});
  });
  const rejection = assert.rejects(pending, /timeout|deadline|abort/i);
  context.mock.timers.tick(15000);
  await rejection;
  assert.equal(signal?.aborted, true);
});

test('successful completion clears the deadline so it cannot abort later', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] });
  let signal: AbortSignal | null | undefined;
  assert.deepEqual(
    await load(manifest, async (_url, options) => {
      signal = options?.signal;
      return new Response(bytes);
    }),
    sample,
  );
  context.mock.timers.tick(15000);
  assert.equal(signal?.aborted, false);
});

test('failed completion clears the deadline timer', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] });
  const cleared = context.mock.method(globalThis, 'clearTimeout');
  await assert.rejects(() =>
    load(manifest, async () => {
      throw new Error('fetch failure');
    }),
  );
  assert.equal(cleared.mock.callCount(), 1);
});
