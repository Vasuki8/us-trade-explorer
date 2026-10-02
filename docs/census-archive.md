# Private exact-response archive

This increment retains the exact Census JSON response bytes for the existing eight-slot market and two-slot world plans. It independently checks that those bytes reproduce the normalized singleton observations before completing an archive receipt. It does not expand coverage or switch the website to official data.

## What the archive proves

The source capture adapter runs only after the established request/response validation and Census-key reflection checks. It receives bytes, never a credential-bearing URL. The archival adapter then applies the additional 64 KiB singleton bound, strict JSON/decoded known-secret checks, the candidate source hash, and an independent parse of flow, month, product, partner, aggregate dimensions, value and status. The parsed observation must exactly match the normalized candidate. World responses must explicitly contain `SUMMARY_LVL=DET`.

Whitespace and field ordering are retained exactly; the archive is not a reconstructed or reformatted substitute for the original response. Altered raw bytes, a normalized value inconsistent with those bytes, an unexpected dimension, or a known credential hidden by JSON escaping fails before persistence. Integer dollars and reported zero retain their existing meaning. Missing/HTTP 204 data is not converted into a zero observation.

These checks bind raw and normalized evidence from a trusted ingestion run. They do not constitute a digital signature by Census, independently prove the current API revision vintage, approve an additive leaf inventory or establish classification comparability. Full reconciliation and public release assembly remain separate gates.

The current [Census API terms](https://www.census.gov/data/developers/about/terms-of-service.html), rechecked 2 October 2026, permit retrieval/analysis subject to their use, attribution and confidentiality conditions. This archive contains aggregate API tables; it does not reconstruct suppressed values or identify respondents. Public presentation retains the required non-endorsement notice and distinguishes our calculations. No government logos, third-party supplements or new datasets are introduced. This bounded workflow does not circumvent access limits or promise continuous source availability.

## Storage and bounds

```text
raw/{sourceHash}.json               exact immutable source bytes
objects/{candidateId}.json          established normalized candidate
batches/{planId}/progress.json      existing atomic partition states
bundles/{bundleId}.json             existing complete normalized references
batches/{planId}/complete.json      last valid normalized-bundle pointer
archive/{receiptId}.json            immutable independently verified raw references
archive/complete.json               last complete private archive receipt
```

Raw objects are persisted before their normalized slot is recorded successful. Content-addressed reuse checks the stored bytes instead of overwriting a corrupt object. Repeated acquisition preserves immutable history; identical responses make no duplicate source object. Archive verification binds the current successful journal, pointed bundle and receipt, rather than accepting a prior complete pointer after a failed refresh.

Limits remain eight explicit slots, 64 KiB per JSON/raw object, 2 MiB compressed/unpacked snapshot and 48 ZIP entries. The source transport itself has a larger response bound, but the archival singleton protocol rejects anything above its smaller cap. No payload is truncated to fit. This is a development protocol for small approved partitions, not the complete 60-month historical warehouse. Repeated refresh history can reach the limits; preserve older evidence separately and start a reviewed fresh generation rather than casually raising the caps.

Every normalized candidate in a snapshot, including unused historical candidates, requires its matching verified raw object. A narrowly recoverable raw orphan can result from interruption after raw persistence but before the normalized object write. Its content hash, strict JSON, known-secret checks, exact singleton scope and aggregate dimensions must match an authorized plan slot. It is retained and recorded without candidate references; it cannot satisfy a normalized slot or count toward coverage, and resumption must obtain a normalized observation. Unexpected or unclassifiable raw objects are rejected.

## Migration and operation

Established candidate/bundle identities and normalized-only batch workflows remain unchanged. Their source hash alone cannot recover absent bytes. Do not reconstruct raw responses from a normalized candidate or silently upgrade a legacy artifact. Start a fresh **Acquire archived Census batch** run to obtain actual bytes. Select `markets` or `world-controls`; the workflow maps these choices to fixed reviewed plan paths.

The new manual workflow runs only on trusted `main` in `census-ingestion`, with `CENSUS_API_KEY` and the read-only GitHub Actions token in its process environment. It shares acquisition concurrency, uses pinned Actions, read-only repository/Actions permissions and a twenty-minute job cap. Inputs are validated environment values in quoted argument arrays; they are not interpolated into executable source. PR checks receive no credentials. No raw data enters the static build, sitemap, CSV downloads or preview artifact.

Local equivalent, after securely setting the process key:

```powershell
py -3.14 -m pipeline.archive --plan sources/batches/coffee-markets-2026-07.json --output .local/census-archive
```

Repeat with the same output to resume; use `--refresh` to re-fetch all slots. For private Actions restoration into a new empty destination, configure `GH_TOKEN` securely and add `--resume-run RUN_ID --repository Vasuki8/us-trade-explorer`. Never pass secrets in command arguments or paste them into chat.

Only completed manual main executions of `.github/workflows/census-archive.yml` and exact unexpired `census-archive-{runId}` artifacts are accepted by the new downloader. Legacy normalized-only restoration remains a separate entry point and still rejects raw/archive paths. Archive SHA-256, bounded HTTPS/ZIP handling, safe paths/types and all semantic relationships are checked before destination writes. The signed storage request receives no authorization header. Restore rejects wrong plans, missing objects, extra paths, reflected credentials and inconsistent receipts.

## Failure and recovery

Acquisition preserves safe partial evidence when a source request fails; successful slots are checked before any later network call. A corrupt or missing raw file associated with a cached candidate fails before networking, including a requested refresh. Preserve the damaged directory for diagnosis; restore a verified prior archived artifact into a fresh empty directory or perform fresh acquisition. Do not overwrite a corrupt content-addressed object.

A failed refresh retains previous complete objects and pointers for recovery. Current archive verification refuses the incomplete generation until it is resumed. An interrupted receipt/pointer write can be retried against the completed normalized generation. Old successful workflow runs remain explicitly selectable for intentionally using earlier verified evidence; selecting a failed refresh must not disguise its prior generation as the current one.

Local writer locks prevent competing archival writers. Remove a stale lock only after confirming its process has stopped; do not automatically steal it. Regular `.pending-*` atomic-write temporaries are retained locally but excluded from evidence inventory and artifacts; symlinks and unknown actual evidence paths still fail validation. Valid later raw evidence can be incorporated by regenerating a receipt offline, but strict verification refuses a receipt that omits retained responses. Temporary files and locks are excluded from artifacts. Bounded socket reads and watchdogs protect headers/body; OS DNS resolution still relies on the outer job cap for recovery.

Private Actions artifacts expire after seven days and are not durable backups. Preserve verified evidence before expiry in controlled private storage. Runtime raw files stay under ignored `pipeline/output/` or `.local/`, outside Git history. Long-lived historical storage, independent backup restoration and AWS provisioning remain deferred. Secrets, key-bearing request URLs and upstream error text must never be retained as evidence.

## Verification state

Local tests exercise fabricated raw responses, malformed/hash/row mismatches, zero values, secret reflection, immutable reuse, interrupted generations and artifact restoration. [PR #13](https://github.com/Vasuki8/us-trade-explorer/pull/13) merged at `b7e470ba749679f93c026afedf916dad531e05f8` under the owner's standing authorization to merge tested, reviewed PRs. A fresh independent review found no findings. Final PR [Checks 37034560955](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37034560955) and [main Checks 37035527230](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035527230) passed 131 Python tests on Linux without skips, 9 Node tests, Astro/build checks, 16 browser journeys at each configured path and production rejection.

Authenticated trusted-main [market acquisition 37035812076](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035812076) and [world acquisition 37035816019](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035816019), plus real Actions-to-Actions recoveries [37035964431](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035964431) and [37035998991](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035998991), passed on that merge commit. Independent verification checked exact workflow/main provenance, artifact hashes/sizes, complete retained inventory and successful journal/bundle/receipt generations; every raw response was independently reparsed against its candidate. Offline archive verification passed before local staged copies were promoted. Each market snapshot contains 21 files/8 raw responses/8 candidates; each world snapshot contains 9 files/2 raw responses/2 candidates, with no raw orphans. Both recovery pairs retained every file and byte. ZIP-container digests differ between runs while the member evidence remains identical.

| Plan | Verified private receipt |
|---|---|
| Markets | `546d4edef8b01061b2ea0ada205c7d5bff6e6497fa642d673eef0f9369521ddf` |
| World controls | `f36936f3d83f9b835e62408aefee1fcab4c0f684e3285016e70691be0b376375` |

Verified development copies are under ignored `.local/archive-evidence/{runId}/`, with a redacted `verification.json` receipt. The four private artifacts expire on **9 October 2026**, between 16:43:30 and 16:44:55 UTC. They remain temporary evidence; the local copies are not independent durable backups. The [handoff](handoff.md) records exact plan/bundle/receipt/artifact identities, expiries and operating limits.

The local verifier held its GitHub credential in memory and checked it against raw/decoded evidence. It did not read or possess the Census key; Census-key reflection remains the protected workflow's check. No source amounts or raw payloads enter tracked documentation. Live induced failure/refresh was not exercised; regression tests verify those failure paths. PR #12's historical normalized market/world report remains separate and is not relabelled as an archived-input report.

Next work joins archived inputs with full partner scan/inventory and revision evidence, then assembles a validated public release through an explicit projection. The existing selected-market report continues to carry its raw-statistical-archive blocker because its historical inputs contain normalized evidence only. No public release is activated by this module.
