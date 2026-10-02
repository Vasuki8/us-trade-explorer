import {
  loadPublicRelease,
  validatePublicManifest,
} from '../../packages/contracts/public-release.ts';
import type { Release } from '../../packages/contracts/trade.ts';

/** Fetch only bounded same-origin bytes, then let the public loader verify them. */
export async function fetchPublicRelease(
  manifest: unknown,
  releaseURL: string,
  pageURL: string,
  fetcher: typeof fetch = fetch,
): Promise<Release> {
  const pin = validatePublicManifest(manifest);
  const page = new URL(pageURL),
    url = new URL(releaseURL, page);
  if (
    !['http:', 'https:'].includes(page.protocol) ||
    !['http:', 'https:'].includes(url.protocol) ||
    page.username ||
    page.password ||
    url.username ||
    url.password ||
    url.origin !== page.origin ||
    url.search ||
    url.hash
  )
    throw new Error('Invalid public release URL');

  const controller = new AbortController();
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let timer: ReturnType<typeof setTimeout>;
  const deadline = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new Error('Public release deadline exceeded'));
    }, 15000);
  });
  try {
    const response = await Promise.race([
      fetcher(url.href, {
        signal: controller.signal,
        credentials: 'omit',
        mode: 'same-origin',
        redirect: 'error',
      }),
      deadline,
    ]);
    reader = response.body?.getReader();
    if (!response.ok || !reader) throw new Error('Unavailable public release');

    // The validated pin is at most 512 KiB. Content-Length may describe
    // compressed transfer bytes, so only actual decoded chunks count here.
    const bytes = new Uint8Array(pin.contentBytes);
    let received = 0;
    for (;;) {
      const chunk = await Promise.race([reader.read(), deadline]);
      if (chunk.done) break;
      if (
        !(chunk.value instanceof Uint8Array) ||
        chunk.value.byteLength > bytes.byteLength - received
      )
        throw new Error('Public release byte overflow');
      // Copy before requesting another chunk: a source can reuse its buffer.
      bytes.set(chunk.value, received);
      received += chunk.value.byteLength;
    }
    return await Promise.race([
      loadPublicRelease(pin, () => bytes.subarray(0, received)),
      deadline,
    ]);
  } catch (error) {
    controller.abort();
    // Do not let a stalled cancellation extend the overall deadline.
    if (reader) void reader.cancel().catch(() => {});
    throw error;
  } finally {
    clearTimeout(timer!);
    reader?.releaseLock();
  }
}
