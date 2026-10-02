# Private Census batches

This increment extends the verified singleton imports/exports connector to bounded plans and recoverable private evidence. It assembles **candidate bundles**, with completeness limited to the requested partitions. Official-data publication still requires a statistical inventory, source dates, reconciliation and classification review.

## Initial reviewed plan

`sources/batches/coffee-markets-2026-07.json` requests July 2026, HS2 chapter 09 (coffee, tea, maté and spices), imports and exports for Canada 1220, Mexico 2010, India 5330 and China 5700. These codes were checked against [Census Schedule C](https://www.census.gov/foreign-trade/schedules/c/countrycodes.html). The selected code list is not a complete partner inventory. The plan is reviewed configuration; data, credentials and runtime evidence stay outside Git.

The batch validates 1–8 explicit `{flow, period, product, partner}` slots. Wildcards, duplicates, unexpected fields and malformed codes fail before networking. Sorting makes plan identity independent of input order. Each slot must return exactly one valid, in-scope observation on the existing value/aggregation contract. A four-digit partner syntax does not classify it as a country: approved partner kinds remain a later statistical gate.

The separate `sources/batches/coffee-world-2026-07.json` plan contains two world-control slots, one per flow, for the same month and chapter. World uses `CTY_CODE=-` and explicit `SUMMARY_LVL=DET`, which the guide documents for the world row. Missing or non-DET response dimensions fail closed. This extends the existing candidate contract only to a previously unsupported explicit world scope; established market queries, plan identity and stored evidence remain unchanged. See [private control reports](census-controls.md).

The [Census API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf) documents world `-`, group codes, explicit monthly zeros and HTTP 204 outcomes. `no_results` is retained as a failed slot with HTTP 204; the batch cannot satisfy that slot by inventing zero. A reported numeric `0` remains `reported_zero`. Broader wildcard results must not be presumed to contain every possible product/country pair.

## Run, resume and refresh

The manual **Acquire Census batch** workflow runs only on trusted `main` in `census-ingestion`, using repository secret `CENSUS_API_KEY`. Choose `markets` (eight slots, default) or `world-controls` (two slots). A fixed shell mapping permits only those reviewed paths. It acquires slots sequentially, shares the single-probe concurrency group, has a 20-minute cap and read-only repository/Actions permissions. Inputs enter environment variables and a quoted argument array. No secrets are available to pull-request checks.

- Fresh run: leave `resume_run` empty and `refresh` false.
- Recover a failed or interrupted run: enter its completed run ID, keep `refresh` false. Existing successful evidence is revalidated and only unfinished slots are acquired.
- Detect revisions: enter the previous run ID and set `refresh` true. Every slot is re-fetched; unchanged evidence keeps its original object and ingestion time. Changed source bytes create a new candidate identity and bundle, retaining previous evidence.

Select the same plan as the prior run when restoring. Market and world snapshots have distinct plan identities and must use separate destinations; a cross-plan restore is rejected before writes. A refresh detects changed bytes; it cannot establish an official revision date.

The preceding run must be in this repository, be a completed manual `main` execution of `.github/workflows/census-batch.yml`, and contain exactly the expected, unexpired `census-batch-{run_id}` artifact. Restore verifies metadata, the archive SHA-256 digest, paths, sizes and all JSON contracts/references before persisting files. The token is sent only to `api.github.com`; the signed artifact-storage redirect receives no authorization header. Both Census and GitHub credential reflections are rejected after JSON decoding.

The read-only Actions token is sufficient for the same private repository. Cross-repository restoration, PR artifacts and artifacts from the single-probe workflow are rejected. Snapshot limits are 2 MiB compressed/unpacked, 48 archive entries and 64 KiB per JSON member. This deliberately small singleton protocol is not a bulk historical archive.

Local equivalent, after setting credentials securely in the process environment:

```powershell
py -3.14 -m pipeline.batch --plan sources/batches/coffee-markets-2026-07.json --output .local/census-batch
```

Repeat with the same output to resume. Add `--refresh` to re-fetch every slot. To restore from Actions into an empty destination, set `GH_TOKEN` using a credential manager, then add `--resume-run RUN_ID --repository Vasuki8/us-trade-explorer`. Never put keys or tokens in command arguments, URLs, checked-in environment files or chat.

Offline verification requires no credentials:

```powershell
py -3.14 -c "import json; from pipeline.batch import verify_bundle; b=verify_bundle(json.load(open('sources/batches/coffee-markets-2026-07.json')), '.local/census-batch'); print(b['bundleId'],len(b['partitions']))"
```

## Evidence and failure semantics

```text
objects/{candidate-id}.json            immutable normalized candidate
batches/{plan-id}/progress.json        atomic slot states and safe failure categories
bundles/{bundle-id}.json               immutable complete candidate references
batches/{plan-id}/complete.json        last fully validated candidate-bundle pointer
```

Each success references a candidate ID and a hash of the stored object bytes. Reuse validates both, the fixed source/query, period, row/status and publication blockers. Existing candidate identity excludes ingestion time; identical re-fetches preserve the first file. Query-aware source identities prevent a narrow request from being confused with a broader one. This normalized-only protocol retains the raw-source hash but does not archive raw Census payloads or independently verify that hash against archived source bytes. The separate [exact-response archive protocol](census-archive.md), added in PR #13, provides that boundary without silently upgrading legacy artifacts.

Objects are durably written before recording success. Unique temporary files, atomic replacement and a local writer lock protect state. If a process stops after object persistence but before journal success, a repeat fetch reuses matching immutable content. A network/schema/no-results failure records only a safe category/status and leaves earlier successes available. No new bundle is assembled until every expected slot succeeds. A failed refresh preserves the old complete pointer and bundle; resuming uses the new partial journal without splicing old successful slots into the new generation.

Partial evidence is uploaded even when acquisition fails. The artifact upload excludes locks and temporary files. A download/validation failure before restore writes produces no new artifact. Restoring requires an empty destination and rejects different plans and unexpected files. Corrupted local evidence fails closed; recover from a verified prior artifact into a fresh directory or preserve the corrupt directory for diagnosis and acquire a fresh batch. Do not overwrite or repair a candidate in place. A stale local lock should be removed only after verifying its process is no longer running.

Actions artifacts expire after **seven days** and are not backups. Preserve needed private evidence before expiry in a controlled private archive; the ignored local output is one development copy. Repeated refreshes accumulate immutable history and can eventually exceed snapshot limits; archive older generations separately rather than raising bounds casually. Long-lived raw/history storage and independent backup restore remain the AWS phase; bounded archived Actions recovery is documented separately. A socket timeout cannot hard-bound OS DNS resolution; the job cap remains the outer recovery bound.

## Gates before official publication

Bundles carry explicit blockers and null official release/revision dates. They never call `ReleaseStore.publish`, mutate `active.json`, feed `src/lib/data.ts`, build public CSVs or enter the preview artifact. The public schema remains strict and the production build remains disabled.

Required follow-up: approved per-flow commodity/partner inventory including special statistical codes, same-period/basis/vintage world controls, documented residual rules, official publication/revision evidence and comparable classification vintages. Low-value estimates and US territory rules need review before summing leaves; [Census program definitions](https://www.census.gov/foreign-trade/guide/sec2.html) explain why reporting-code lists alone are insufficient. Selected market totals are not world totals. There is no arbitrary residual tolerance or claim of successful reconciliation here.

## Verification receipt

The PR #10 imports/exports probes succeeded for July 2026, chapter 09 and Canada. After PR #11 merged at `286c8ec333afaad3a962555790d4b5705930fced`, authenticated eight-slot acquisition [run 36973640536](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36973640536) and Actions-to-Actions recovery [run 36973761962](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36973761962) both succeeded. All eight observations passed the scope, schema and numeric/status contracts; both runs produced bundle `2e8ca3d5fb34b378ead182c2826950f6f977fb98f0fde70e9c558cf3077b5830`. The eleven restored files were byte-identical to the fresh artifact. The recovery run reused successful slots without new source requests.

These runs verify authenticated market acquisition and real private artifact recovery, not complete coverage, raw-source archival or reconciliation. Induced live network failure and refresh were not exercised; their behavior is covered by regression tests. After PR #12 merged, world acquisition run 37026467626 and combined report run 37026664906 passed on trusted main; the [control record](census-controls.md) preserves their exact inputs and verification receipts. PR #13's separate raw-response archive acquisition/recovery results are in the [handoff](handoff.md). CI and independent review receipts belong to the relevant pull request.
