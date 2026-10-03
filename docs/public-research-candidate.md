# Unpublished public research candidate

The [Python producer](../pipeline/public_candidate.py) prepares a small, public-field-only bundle for July 2026 / HS2 chapter 09. It revalidates complete retained import and export archives, the selected-country reports and their classification references before projecting either flow. The [TypeScript contract](../packages/contracts/research-candidate.ts) independently validates the resulting structure and arithmetic. Neither is connected to the website's [sample-only loader](public-release-boundary.md).

This is a review artifact, **not an approved official release**. Actual candidates stay in ignored `.local` storage. The checked-in [shared test fixture](../tests/fixtures/research-candidate.example.json) is conspicuously labelled fabricated; its tiny values and mock source-document pins are only for tests. It is not a Census capture and is not included in website output.

## Contract and supported interpretation

One envelope contains `manifest` and `data`. Both declare schema version 2 and `publicationState: unpublished-review`. The manifest names the exact period, chapter, two ordered flows and four Schedule C countries, and binds the canonical data's byte count and SHA-256 hash. The two flows are published into this local envelope together, never independently advanced.

The data retains:

- Reporting period, chapter label and separate import/export definitions: monthly nominal USD, not seasonally adjusted; general imports/customs value versus total exports including re-exports/FAS value.
- World control and Canada, Mexico, India and China values, with reviewed display names and geographic qualifications. Raw external descriptions are omitted.
- Reported zero versus unobserved states, exact integer dollars, world shares rounded half-up to two decimal places, observed selected sum and complete selected subtotal only when all four are observed. A missing or zero world denominator cannot produce a share. The selected sum cannot exceed an observed world control.
- Census dataset endpoints, separate classification reference URLs, Schedule C designation reference URLs, and first retained retrieval time. These reference editions do not certify the API's classification vintage or every provision's effective interval.
- Explicitly unknown official release/revision dates, revision-detection time and publication time. This producer does not consume the separate initial-announcement evidence, so it cannot infer these fields from it or from collection time.
- Restrictions against historical growth, fine-code joins, quantities, global rankings and country-level concentration. Four selected countries do not establish worldwide coverage. No causal explanation is generated.

Raw queries, unselected codes, private archive paths/identities, scan/receipt/journal IDs, operational attempts, raw source text/bytes and approval flags are excluded. Both validators use exact field sets. The TypeScript reader also checks statistical definitions, source URLs, calendar-valid retrieval timestamps, statuses, coverage and BigInt arithmetic independently; it returns detached, deeply frozen objects.

## Encoding, validation and trust

Data is canonical sorted-key, compact JSON with ASCII escaping, matching Python's existing `canonical()` function. USD values are decimal strings, so JavaScript never rounds them through floating point. The shared fabricated fixture checks encoding parity, including the accented chapter label.

The reader accepts at most 64 KiB of data and an 8 KiB manifest. It validates and snapshots the manifest before calling its byte loader, copies returned bytes before asynchronous hashing, verifies count/checksum and strict UTF-8/JSON, then compares canonical bytes. This rejects duplicate keys, BOMs, alternate encodings and unknown fields even if someone recalculates the checksum. It contains no network transport; a future adapter must separately bound redirects, response bytes and timeouts.

**Checksums establish consistency, not source authenticity.** Plausible invented values with internally correct arithmetic can satisfy a standalone format validator. `validate_bundle` rebuilds from the exact source archives and reviewed documents to catch that substitution. Future production acceptance must bind a reviewed candidate to trusted acquisition/evidence and an approved release pin. No `publicationReady` toggle can convert this candidate into an accepted website release.

The producer's CLI performs no network or credential lookup and writes atomically only below the repository's ignored `.local` directory, outside both input archives and all reference files. Validation or write failures retain prior output and emit fixed messages without source values or exception details.

```sh
python -m pipeline.public_candidate \
  --plan sources/scans/coffee-partners-2026-07.json \
  --imports .local/partner-evidence/37043703299 \
  --exports .local/partner-evidence/37043711698 \
  --annex-dir .local/chapter-scope/annexes \
  --classification-dir .local/chapter-scope \
  --output .local/public-candidate/fresh.json
```

These paths refer to retained local evidence, not files in Git. A clean clone can run fabricated tests but cannot reproduce an actual candidate without the approved evidence. Do not copy actual candidates or evidence into Git, `public`, build artifacts or logs.

## Verification and next step

On 3 October 2026, ten focused Python tests and thirteen Node tests pass. The producer tests first failed because the implementation was missing; the TypeScript test likewise failed on the missing module. Source replay catches rehashed invented values. Tests cover both input archives, missing/zero semantics, incompatible definitions, unsafe output locations, write/input failure preservation, secret reflection, unknown fields, oversize/cyclic inputs, malformed/noncanonical bytes and asynchronous mutation isolation. Existing sample-loader tests explicitly reject the new artifacts before any byte fetch.

Offline replay of the four retained actual snapshots produces matching fresh/recovery bundles: each data body is 5,124 bytes. Builder and CLI output match, TypeScript confirms canonical checksum and content, the site loader rejects the manifest, and all input bytes remain unchanged. Network, credential access and subprocesses were prohibited during Python replay. Actual statistics remain local.

Full local validation: 305 Python tests (four existing Windows capability skips), 118 Node tests, zero Astro errors/warnings/hints, unchanged 30-page sample build and 8,254-byte gzipped JavaScript. Independent review of `218b96fefc330d10cbcca8364874eab80abcc37f` found no actionable issues and separately passed all focused tests, actual replay with writes intercepted, website rejection and 64 fabricated cross-language cases covering missing countries/world controls, zero and large integers. No finding was deferred. Exact-head GitHub Checks passed the same Python/Node checks on Linux, plus 62 browser checks per base path and production rejection. Post-merge receipts belong in the [handoff](handoff.md) and PR history.

Next: build a separate **local-only review view** that exercises this contract with direct profile entry, explicit basis/coverage/source context and missing-data states. Keep official publication disabled until source-use, hosting/notice acceptance, repository visibility intent and an approved private execution/storage path are resolved. Production release pinning/rollback belongs to that later acceptance step. No new acquisition, host, account, advertising or payment integration is introduced here.
