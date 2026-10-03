# Private world controls and announcement evidence

This increment prepares official data without changing the sample website. It adds an independently verified private report for July 2026, HS2 chapter 09, comparing Canada, Mexico, India and China with a world control for each trade flow. A successful report cannot activate a public release.

## Statistical scope

Imports use monthly general-import customs value, `GEN_VAL_MO`, across all districts, country subcodes and rate provisions. Exports use monthly total domestic-plus-foreign FAS value, `ALL_VAL_MO`, across all districts. Amounts are exact nominal US dollars, not seasonally adjusted. Imports and exports have different valuation definitions; neither is a country-wide balance-of-payments measure.

The separate two-slot world plan requests `CTY_CODE=-`, `COMM_LVL=HS2` and `SUMMARY_LVL=DET`, preserving the existing aggregate dimensions. The [Census API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf) places world in DET; country groups use CGP. World rows never enter a selected-country sum. A missing/non-DET summary, malformed amount, unexpected dimension or HTTP 204 fails acquisition. Missing records remain missing; they are never invented as zero.

`sources/control-checks/coffee-2026-07.json` pins the four selected [Schedule C](https://www.census.gov/foreign-trade/schedules/c/countrycodes.html) countries. The report requires both plans to match that exact reviewed scope, revalidates bundle references and each stored object checksum, checks code/name mappings, and independently verifies the announcement document. A numeric country-code pattern alone does not approve any additional leaf.

For each flow:

```text
selectedTotalUSD    = Canada + Mexico + India + China
outsideSelectionUSD = worldControlUSD - selectedTotalUSD
```

The report requires the selected amount to be no greater than the world amount. This is a limited subset consistency check. The difference describes the amount outside the selection; it is not an unexplained statistical residual, a fabricated observation or proof of an additive full inventory. Even a difference of zero leaves `fullWorldReconciliation=not-verified` and `publicationReady=false`. No tolerance or rounding is used.

The source captures may have different revision vintages. Passing this inequality does not establish matched vintage, full world reconciliation or statistical comparability. `LAST_UPDATE` is not yet captured; Census's label “Date of Last Update” alone would not establish an official revision date. Complete source scans and approved inventories remain later work.

## Reviewed announcement evidence

`sources/publications/ft900-2026-07.json` contains a reviewed statement tied to the exact PDF SHA-256. Page 1 of the official [July 2026 FT900 announcement](https://www.census.gov/foreign-trade/Press-Release/ft900/ft900_2607.pdf) gives initial release date **2026-09-03**, Census release **CB26-142** and BEA release **BEA26-40**. The reviewed download is 1,826,911 bytes, SHA-256 `c122b8ccee947c58859597a7549bb5dcb6691add3e405180ab915d43f6c43aa0`.

The statement's date is a human-reviewed assertion from those pinned bytes, not an automatic extraction from arbitrary PDFs. The reader permits only the period-matched HTTPS `www.census.gov` FT900 path, with no redirects, credentials, query or fragment. It checks identity encoding, declared/actual size, a 4 MiB maximum, PDF signature, checksum and known credential reflection. Requests use a five-second connect timeout and thirty-second response watchdog; OS DNS resolution remains bounded by the outer job cap rather than a hard resolver deadline.

The proof's `claim=initial-monthly-announcement-only`, `apiVintageVerified=false` and null revision date prevent an announcement from being presented as proof of current detailed API vintage. Existing candidate/bundle dates remain null; the separate report attaches this narrower announcement evidence. PDF headline seasonally adjusted goods/services figures are not used to reconcile the detailed HS values.

The private archive retains verified `documents/{sha256}.pdf` and `proof.json` with actual `retrievedAt`. Pure offline verification preserves the original statement/document identity without inventing a retrieval time. No PDF, raw source payload, key or runtime report is stored in Git. If Census replaces the PDF at the same URL, its changed hash fails closed; review the new document and statement in Git before retrying.

## Manual workflow

1. Run **Acquire Census batch** on `main`, selecting `markets`; use an existing successful unexpired market run if appropriate.
2. Run it again selecting `world-controls`. Keep its distinct artifact separate from the market plan.
3. Run **Verify private Census controls** on `main` with the two completed run IDs.

The report workflow restores only trusted completed manual main batch runs from this private repository. Existing path, size, digest, strict JSON and secret-reflection checks run before each snapshot is persisted. It fetches no new Census statistical rows; the Census secret is used to validate known-credential reflection in restored evidence. The read-only GitHub token retrieves private artifacts and is never forwarded to signed storage URLs. Only the pinned official announcement is fetched separately.

The workflow uses the `census-ingestion` environment, read-only repository/Actions permissions, pinned Actions and a twenty-minute cap. Only a completed successful report is uploaded as private `census-controls-{run_id}` evidence. PR checks receive no keys. The public build includes none of these directories. Logs contain fixed diagnostics and counts, without upstream text, signed URLs or secrets.

Local equivalent, with securely configured process credentials:

```powershell
py -3.14 -m pipeline.controls --market-run MARKET_RUN_ID --world-run WORLD_RUN_ID --output .local/census-controls
```

Use a new empty destination. Operator-supplied run IDs are validated and passed as quoted arguments. Failed or partial input bundles, wrong plans, expired downloads, missing documents, changed hashes or a selected sum above world produce no completed report. The UI and last public release remain untouched.

Each input's current progress journal must be wholly successful and reference exactly the candidate IDs/object hashes in its complete bundle. A failed refresh can retain the old complete pointer for batch recovery, but the report refuses to substitute that older generation. An all-successful journal with an interrupted bundle/pointer write must first be recovered by resuming the batch. To deliberately reuse earlier valid evidence, select its successful prior run. Verified journal identities are recorded alongside bundle identities in the report.

`build_report(...)` also supports offline verification from two preserved batch roots, the reviewed check/statement and archived PDF bytes, without network access or credentials. Known secret canaries can be supplied explicitly for verification. Input hashes, candidate IDs and ingestion times are recorded in the report; a second identical verification yields the same report identity.

## Recovery and publication boundaries

Completed reports are immutable `reports/{reportId}.json`; the private `reports/complete.json` pointer is replaced only after successful calculation and object persistence. An interrupted pointer write preserves the preceding completed report and can be retried. This private pointer is unrelated to the public release store's `active.json`.

Preserve needed evidence before its seven-day Actions expiry. Artifacts are temporary development evidence, not durable backups. The private report includes both normalized input snapshots and the verified announcement document. The original batch restore protocol remains 2 MiB/48 files/64 KiB per JSON; it does not accept the larger report artifact. Long-lived raw history, backups and independent restore drills require the future authorized private-storage phase; see the [current direction](decisions/2026-10-02-operating-model.md).

Full publication still requires an approved per-flow leaf inventory including special statistical buckets, archived and independently revalidated raw statistical responses, matched API revision vintage, complete exact reconciliation, classification comparability and an explicit public data projection/loader. Reporting-code lists and a four-country subset cannot satisfy these gates. No public loader, indexing, deployment, ads or subscription behavior is changed here.

## Verification receipt — 2 October 2026

[PR #12](https://github.com/Vasuki8/us-trade-explorer/pull/12) merged with explicit owner approval at `3b0f42d8704f4424c15aa2351cbb2a2593b48281`. Main [Checks run 37026368794](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026368794) passed: 96 Python tests, 9 Node tests, Astro checks/build verification and 16 browser journeys under each configured path. The [private preview run 37026368465](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026368465) built successfully and skipped Pages deployment.

Authenticated [world acquisition run 37026467626](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026467626) and [combined report run 37026664906](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026664906) both passed on that trusted main commit. The report restored market evidence from successful [fresh run 36973640536](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36973640536). Its 20 preserved files were independently verified and the report recomputed from the normalized inputs and pinned PDF. Separate recovery run 36973761962 had previously reproduced the same normalized files; it was not the selected report input.

| Evidence | Immutable identity |
|---|---|
| Market bundle | `2e8ca3d5fb34b378ead182c2826950f6f977fb98f0fde70e9c558cf3077b5830` |
| World bundle | `f624a46363ebfd9821021c1941d20398a8d6ec7715220b024a32506d5fde87d1` |
| Private report | `fe6327d05521da9b928977aab8bf3b2672f4c0e920f35e7d8a4071ba6fff1cb1` |
| Report artifact SHA-256 | `5e0c511bab31e6c9a5335d4073a0d1fb9b4ff6493d02a982f747eafc289f66c0` |

Both exact subset checks passed, with a positive amount outside the selected countries. The report retains `publicationReady=false`, `coverage=selected-markets-only`, `apiVintageVerified=false`, `fullWorldReconciliation=not-verified` and a null official revision date. The PDF supports initial announcement date 2026-09-03 only. No full world reconciliation or official public release is claimed.

The report artifact expires **2026-10-09 at 15:23:56 UTC**. Verified private copies and a redacted receipt are preserved under ignored `.local/control-evidence/`; these remain development copies, not durable backups. The Census key was available only to the protected workflows, where reflection checks ran. The local verifier used a GitHub credential held in memory and did not have the Census key. See the [handoff](handoff.md) for recovery and the current raw-archive development boundary.
