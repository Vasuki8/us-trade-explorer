# Public release boundary

Updated **2 October 2026**. This guide describes the implemented [boundary plan](superpowers/plans/2026-10-02-public-release-boundary.md). Verification, review and integration have separate dated [handoff receipts](handoff.md); this guide is not a passing receipt. The website remains a synthetic sample, noindex and blocked from production publication.

## Fixed sample and public downloads

The integration pins `tests/fixtures/sample-release.json` to `releases/sample-2026-07-v1.manifest.json`. The selector accepts the committed sample hash only; there is no official-data configuration or CLI switch. Private Census candidates, scans, reports, raw responses and credentials cannot select the website's data.

The release ID is `sample-2026-07-v1`. Public paths below acquire the configured base path, including `/us-trade-explorer/` when selected:

| Path | Content |
|---|---|
| `/releases/sample-2026-07-v1/` | Release explanation and download links |
| `/data/sample-2026-07-v1.json` | Canonical public release bytes |
| `/downloads/sample-2026-07-v1.csv` | CSV from the same validated release |
| `/data/sample-2026-07-v1.manifest.json` | Public metadata sidecar |

The sample covers four selected HS2 chapters, five countries plus an illustrative world partner, and 25 periods. Its world control covers the included synthetic chapters; it is not all US merchandise trade. `HS2022` is a synthetic label, not evidence of current Census classification. Sample official release/revision dates and revision-detection time are null.

## Boundary contract

`packages/contracts/public-release.ts` is a portable, browser-safe module. It has no filesystem, network or secret access:

| API | Purpose |
|---|---|
| `projectPublicRelease(input)` | Reconstruct explicit version-1 public fields, validate relationships/statuses and freeze independent nested copies |
| `encodePublicRelease(input)` | Encode the projected DTO as ordered `JSON.stringify` UTF-8 bytes without trailing whitespace |
| `validatePublicManifest(input)` | Validate the exact sample-only manifest contract |
| `createSampleManifest(input)` | Produce metadata and SHA-256 from the canonical sample encoding |
| `loadPublicRelease(manifest, loadBytes)` | Validate metadata before calling `loadBytes(contentHash)`, then bind and validate a snapshot of its returned bytes |

Projection explicitly copies allowed top-level, product, partner and observation fields. Extra assembly fields are omitted; serialized public DTOs and manifests reject unknown fields. Neither copied approval flags nor plausible Census labels authorize official publication. Deep freezing and independent copies protect the verified release from later input/output mutation.

Limits reject oversized input before expensive copying/parsing: **99 products, 300 partners, 72 periods, 5,000 observations, 512 KiB public JSON and 64 KiB manifest**. Exact dollar strings are preserved. Reported zero remains distinct from missing statuses with null values; every declared product/partner/period/flow combination needs an explicit status.

The manifest has exactly `schemaVersion`, `artifact`, `mode`, `source`, `releaseId`, `releaseSchemaVersion`, `contentHash`, `contentBytes`, `basis`, `scope`, `coverage`, `classification` and `provenance`. Its artifact is `public-trade-release`, mode/source are `sample`/`synthetic`, and both schema versions are 1.

Coverage contains ordered `productCodes`, `partnerIds`, `periods`, flows `['imports','exports']`, kind `selected-synthetic-fixture` and world scope `included-synthetic-chapters`. Classification is HS/HS2022/HS2 with claim `synthetic-label-only`. Provenance is `synthetic-illustration-only`, with null official dates/revision-detection time and an ingestion timestamp matching the DTO. Metadata, array order, identity and scope must match the body exactly.

The loader snapshots callback buffers before asynchronous hashing. It rejects checksum/count mismatches, oversized/truncated bytes, malformed UTF-8, a BOM, duplicate JSON keys, unknown nested fields and any encoding that differs from canonical bytes, even when a supplied digest matches those invalid bytes. Invalid input produces no loaded release or automatic fallback to private evidence.

Build verification also compares the bounded sidecar's raw bytes with the canonical encoding of the reviewed pin. It does not accept parsed equality alone: duplicate keys could otherwise hide a discarded private payload in the downloadable file.

## Regenerate the sample manifest

Run this from the repository root with **Node 24** in PowerShell after installing the locked development dependencies. It uses the same encoder/producer as the website and verifies their agreement before writing and formatting the manifest for review:

```powershell
@'
import { readFile, writeFile } from 'node:fs/promises';
import { createSampleManifest, encodePublicRelease, loadPublicRelease } from './packages/contracts/public-release.ts';
const sample = JSON.parse(await readFile('tests/fixtures/sample-release.json', 'utf8'));
const bytes = encodePublicRelease(sample);
const manifest = await createSampleManifest(sample);
await loadPublicRelease(manifest, () => bytes);
await writeFile('releases/sample-2026-07-v1.manifest.json', JSON.stringify(manifest, null, 2) + '\n');
'@ | node --input-type=module
node node_modules/prettier/bin/prettier.cjs --write releases/sample-2026-07-v1.manifest.json
```

Review the fixture and manifest diff together and run the plan's relevant checks. Do not hash a pretty-printed fixture or hand-edit the digest to bypass a failure. The sidecar's checksum establishes download consistency, not a Census signature, statistical approval or an official revision vintage. Runtime/build verification must bind the actual JSON endpoint bytes to that checksum/count and inspect DTO/sidecar field boundaries.

## Future official release gate

An official producer and a separately reviewed versioned contract remain required. Version 1 cannot express the unresolved period-effective territory/special-area and classification decisions safely. The [Census coverage review](census-coverage-review.md) identifies the evidence needed before such a producer may assemble approved data and public metadata.

Future official assembly must preserve missing states, scope selected chapters honestly, bind approval and reconciliation evidence to exact private inputs, and produce an explicit public projection without private payloads. Current hashes and boolean flags cannot replace that review. Public activation/rollback and host enforcement need their own implemented checks and receipts. See [data-model design](design/03-data-model.md), [implementation status](implementation-status.md) and [handoff](handoff.md). AWS, providers and commercial integrations remain deferred.
