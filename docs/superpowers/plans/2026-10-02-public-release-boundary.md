# Public release boundary implementation plan

> **For agentic workers:** Use test-driven development and independent final review. Update `docs/handoff.md` after every completed task and commit its receipt with that task. Existing owner authorization permits tested, reviewed merges; do not ask again.

**Goal:** Exercise an explicit public-only projection and checksum-pinned sample loader through the current website/downloads while official approval remains unsupported.

**Architecture:** A portable TypeScript boundary constructs an independent, deeply frozen version-1 public DTO from a narrow statistical assembly, encodes deterministic JSON, and validates a separate pinned manifest before loading bounded bytes. The existing Astro sample source uses this boundary; JSON, CSV and a new public metadata sidecar share the same validated release. No private pipeline record or approval flag selects official data.

**Tech stack:** Existing Astro/TypeScript/Node 24 toolchain and Web Crypto; no new packages, network transport, ingestion protocol or cloud service.

**Spec:** Approved `docs/design/03-data-model.md`, `04-security.md`, `06-delivery-plan.md`; `docs/handoff.md` public-projection gate. The owner requests continued reversible MVP work. This implements the existing approved projection/download flow, retaining its sample/production boundaries. Classification-v2 migration and official activation are deferred rather than guessed from July observations.

## Global constraints

- Base main `88ef717f1a72298d2e93139d453583e0b5fede34`; reuse clean linked development worktree, branch `feat/public-release-boundary`.
- The actual website stays pinned to `tests/fixtures/sample-release.json`. Stable pages, JSON/CSV URLs, sample disclosures, noindex, empty sitemap, both base paths and production rejection remain.
- Version-1 Release fields remain compatible. HS2022/HS2 in the new manifest is explicitly a synthetic label, not verification of current Census classification. Future official classification/territory/coverage needs a separately reviewed versioned contract.
- Support **sample/synthetic only** in projection, manifest and loader. Official/Census labels, private candidate/scan/report schemas, boolean approval flags and announcement evidence do not authorize publication. No official configuration/CLI switch exists.
- Construct every top-level/product/partner/observation field explicitly; never spread/serialize pipeline/private records. Extra assembly fields are omitted. Validate projected relationships/statuses before returning; freeze independent nested copies so later input/output mutation cannot change loaded bytes or CSV.
- Bounds before expensive copying/parsing: 99 products, 300 partners, 72 periods, 5,000 observations, 512 KiB public JSON, 64 KiB manifest. Limits reject; never truncate. Dollar strings remain exact. Missing statuses/null and explicit zero remain distinct.
- Deterministic JSON is `JSON.stringify` of the explicitly ordered DTO, UTF-8, no trailing whitespace. Loader requires exact canonical bytes, so duplicate keys, BOM, noncanonical encoding/whitespace, nested unknown fields and malformed UTF-8 fail even when an attacker supplies a matching digest.
- A manifest pins SHA-256 and byte count, release ID/schema/basis/scope, sample coverage, classification label and separate provenance dates. Hashes establish consistency, not source signatures/statistical approval.
- Manifest exact fields: `schemaVersion:1`, `artifact:'public-trade-release'`, `mode:'sample'`, `source:'synthetic'`, `releaseId`, `releaseSchemaVersion:1`, `contentHash`, `contentBytes`, `basis`, `scope`, `coverage`, `classification`, `provenance`.
- Coverage exact fields: `kind:'selected-synthetic-fixture'`, `productCodes`, `partnerIds` (including illustrative world), `periods`, `flows:['imports','exports']`, `worldControlScope:'included-synthetic-chapters'`. Arrays preserve DTO order and match it exactly.
- Classification exact fields: `system:'HS'`, `edition:'HS2022'`, `level:'HS2'`, `claim:'synthetic-label-only'`. Provenance exact fields: `claim:'synthetic-illustration-only'`, `officialReleaseDate:null`, `officialRevisionDate:null`, `ingestedAt` matching DTO, `revisionDetectedAt:null`. All sample official dates are null.
- Private evidence/credentials stay ignored and outside browser/public artifacts. AWS, providers, spending, ads, accounts and billing remain deferred.

## Review focus

- A valid JSON hash or plausible official labels must never open an official-publication path; reject unsupported manifests before invoking the byte callback.
- Private fields nested inside assembly records must not leak to DTO, JSON, CSV or sidecar; downstream mutation must not invalidate a verified manifest.
- Manifest/data mismatches in scope, coverage order, dates, identity, byte count and classification must fail even when each object independently validates.
- Loader must snapshot callback buffers before asynchronous hashing and retain strict UTF-8/canonical-byte verification; never allow mutable buffers or duplicate-key JSON to bypass the contract.
- Root/subpath endpoints and links must deliver the exact bytes whose digest is in the sidecar. Downloadable metadata must explain checksum versus statistical approval, without adding implementation clutter to ordinary analytics flows.

## Task 1 — Public DTO, manifest and bounded loader

Files: create `packages/contracts/public-release.ts`, `tests/public-release.test.ts`, `releases/sample-2026-07-v1.manifest.json`.

Interfaces: `projectPublicRelease(input: unknown): Release`; `encodePublicRelease(input: unknown): Uint8Array`; `validatePublicManifest(input: unknown): PublicReleaseManifest`; `createSampleManifest(input: unknown): Promise<PublicReleaseManifest>`; `loadPublicRelease(manifest: unknown, loadBytes: (contentHash: string) => Uint8Array | Promise<Uint8Array>): Promise<Release>`. Export the two byte-limit constants. Import the existing Release validator/types; browser-safe module with no Node filesystem/secret/network dependencies.

- [x] Add meaningful failing tests for absent interfaces, allowlist reconstruction/nested canaries, independent deep freeze, exact integers/statuses/missing coverage, bounded input, official/private rejection, manifest schema/fields/date/basis/classification rules.
- [x] Implement the explicit sample-only projection and deterministic encoding. Validate array bounds before copying, then use the established statistical Release validator and require sample official dates null.
- [x] Implement independent strict manifest validation, sample manifest derivation with Web Crypto SHA-256, and bounded loader with pre-callback manifest checks, byte-copy snapshot, checksum/count verification, fatal UTF-8 decode, schema/projection validation and byte-for-byte canonical equality.
- [x] Test manifest/body scope/identity/order/date mismatches, tampered/truncated/oversized buffers, duplicate fields/noncanonical JSON/invalid UTF-8, mutable returned buffers and false approval flags. Generate and pin the sample manifest through the implemented encoder/producer; confirm cross-platform deterministic bytes.
- [x] Run focused Node tests, primary integration verification, update handoff and commit.

## Task 2 — Exercise boundary in Astro and downloads

Files: modify `src/lib/data.ts`, `src/pages/data/[id].json.ts`, `src/pages/downloads/[id].csv.ts` if needed, `src/pages/releases/[id].astro`, `scripts/verify-build.mjs`, `tests/browser/journeys.spec.ts`; create `src/pages/data/[id].manifest.json.ts`.

- [ ] Add a failing browser download journey for the metadata link/endpoint, actual JSON response digest/byte count, public-only metadata and unchanged sample disclosure. Run it against the pre-integration sample build to observe the missing sidecar.
- [ ] Encode the fixed sample fixture, load through its committed pinned manifest and export one validated frozen release plus its exact public bytes and validated public manifest. Callback maps only the pinned hash to sample bytes; no arbitrary paths/URLs/environment input or official switch.
- [ ] Existing JSON endpoint serves the pinned canonical bytes; CSV consumes the same frozen release. Add sidecar `/data/{releaseId}.manifest.json` and a clear metadata download link on the release page. Explain that its checksum verifies download integrity; figures remain synthetic.
- [ ] Extend build verification to bind the actual generated JSON to the sidecar digest/count and inspect public DTO/manifest allowlists, so accidental private-field leakage or endpoint drift fails the build. Keep existing internal-link/asset/sample/production checks.
- [ ] Verify full Node/Astro/build suite, root and configured project-path browser journeys and production rejection. Update handoff and commit.

## Task 3 — Coverage review, guide, independent review and integration

Files: create `docs/public-release-boundary.md`, `docs/census-coverage-review.md`; update README/status/handoff and this plan.

- [ ] Record the completed offline July chapter09 review: observed numeric sums equal each returned world, common95/union163/import-only42/export-only26; retain all false approval flags and unobserved-versus-zero distinction. Explain unresolved period-effective territory/special-area inventory and revision evidence with dated official sources. Never publish private amounts or claim full-world reconciliation.
- [ ] Document boundary APIs, sample manifest regeneration, safe failures, sidecar semantics and the future separate official approval producer/contract-v2 requirements. Link current guides/status/handoff.
- [ ] Check documentation links/whitespace/public artifact boundaries. Run one fresh immutable whole-branch review; fix material findings with regressions and scoped fix review.
- [ ] Create/attach PR, require exact final-head CI and reviewed standing-authorized merge, sync clean primary checkout and verify main checks/private preview limitations. Handoff records each completed task; own documentation integration receipts can be recorded in PR/repository history without recursive receipt PRs.
