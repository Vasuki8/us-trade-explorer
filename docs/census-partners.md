# Private Census partner discovery

This bounded scan captures every observed detail partner returned for the reviewed July 2026 / HS2 chapter 09 query, together with exact response bytes and independently revalidated observations. It prepares private evidence for later inventory review. A completed discovery receipt does not approve an additive partner inventory or activate a public release.

## Scope and source meaning

The reviewed plan is `sources/scans/coffee-partners-2026-07.json`, schema version 1, basis `census-monthly-goods-nsa-usd-v1`. Imports and exports run separately against this fixed period and product; the manual workflow does not accept arbitrary dates, commodities or URLs.

| Dimension | Fixed contract |
|---|---|
| Reporter, period and commodity | US reporter, `2026-07`, HS2 `09` |
| Partner selection | `CTY_CODE=*`, with explicit `SUMMARY_LVL=DET` required in every returned row |
| Imports | Monthly general-import customs value, `GEN_VAL_MO`; `DISTRICT=-`, `CTY_SUBCODE=-`, `RP=-` |
| Exports | Monthly total domestic-plus-foreign FAS value, `ALL_VAL_MO`; `DISTRICT=-`, `DF=-` |
| Amount and adjustment | Exact nominal US dollars, monthly, not seasonally adjusted |
| Date predicates | `YEAR=2026`, `MONTH=07`; returned date representations must agree |

The request's `get` fields and predicate fields are disjoint. Aggregate dimensions must be present and equal their reviewed `-` markers. Conflicting dates, dimensions, duplicated rows or non-DET summaries fail validation; neither a wildcard nor a plausible four-digit code relaxes these checks.

Official source references were rechecked **2 October 2026**:

| Reference | What it supports |
|---|---|
| [Census international trade API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf), pages 7, 11–12, 15 and 27 | Total `-` markers, wildcard queries, YEAR/MONTH predicates, detail versus country-group summaries, and world `-` in DET. Numeric `0001`/`0003` country groups show why four digits alone cannot establish a leaf. |
| [Import variable metadata](https://api.census.gov/data/timeseries/intltrade/imports/hs/variables.html) and [export variable metadata](https://api.census.gov/data/timeseries/intltrade/exports/hs/variables.html) | The flow-specific value fields and aggregate dimensions above. |
| [Schedule C reporting codes](https://www.census.gov/foreign-trade/schedules/c/countrycodes.html) | A current reporting aid, including US `1000` and territory codes `9030`, `9110`, `9350`, `9510`, `9610` and `9800`. Current names and membership do not establish period-effective, non-overlapping additive coverage. |
| [Census trade definitions](https://www.census.gov/foreign-trade/guide/sec2.html), sections 1 and 16 | Foreign-trade statistical coverage and separate statistics for trade with US possessions. These require reviewed coverage rules before classifying returned areas or summing them. |

Discovery preserves source code and name as observed. World `-` has role `world-control`; every numeric DET code has role `unreviewed-detail`. That role deliberately leaves country, territory, special-area and additive-leaf decisions unresolved. Do not approve or discard a code solely from its syntax, a current reporting list or its name.

Rows absent from this query remain **unobserved**. They are never added as zero observations. An explicit source zero retains `reported_zero`; an unknown or suppressed value marker fails the established value contract. A no-records response is not a completed zero-valued scan. A missing world row does not invent a control or prove complete world coverage.

## Evidence and bounds

```text
raw/{sourceHash}.json       exact immutable source response bytes
scans/{scanId}.json         independently normalized, sorted observations
receipts/{receiptId}.json   immutable plan/scan/raw/object hashes and counts
progress.json              atomic current-attempt journal
complete.json              last successful receipt pointer
```

The scan records the sanitized query, source identity, sorted observed `(code, name, role)` entries and publication blockers. Source and scan identities exclude ingestion time; identical refreshes reuse the first immutable evidence instead of replacing its timestamp. Changed responses create distinct immutable history. A content-addressed object is checked before reuse, never repaired in place.

Every scan, including retained historical scans, requires its matching raw response. Independent reparsing checks that those bytes reproduce its scope, rows, values and statuses. Receipt validation binds the reviewed plan, scan, raw/object hashes and counts. Hashes bind retained bytes and relationships; they are not Census signatures or proof of an official API revision vintage.

| Limit | Maximum |
|---|---|
| Source rows per flow | 500 |
| Source response or JSON object | 512 KiB |
| Compressed artifact and total unpacked snapshot | 2 MiB each |
| Evidence files | 20 |
| ZIP entries, including directory entries | 24 |

Limits reject oversized evidence without truncation. Strict JSON rejects duplicate fields and nonfinite numbers. Scope, hashes, dates, dimensions, status, source text and known-secret checks apply before persistence. Known credentials are checked in raw and decoded evidence, including JSON escapes. Diagnostics expose fixed categories, safe status and counts without source amounts, response bodies, upstream exception text or credential-bearing URLs.

Valid raw orphans from an interrupted write are independently checked for hash, scope and known secrets, then retained for recovery. They do not become completed observations. Regular `.pending-*` atomic-write temporaries remain local and do not count as evidence; symlinks and unknown evidence paths fail validation. Artifact packaging excludes locks and temporaries. Historical objects and orphans still count against the applicable bounds, so repeated refreshes can exhaust this small development protocol.

The discovery state remains `private-partner-discovery`, with `coverage=observed-partners-only`, `leafInventoryApproved=false`, `apiVintageVerified=false` and `publicationReady=false`. Official release and revision dates remain null in this evidence. The separately reviewed monthly announcement does not establish the detailed API's current revision vintage.

## Manual acquisition and restore

Run `.github/workflows/census-partners.yml` on trusted **main**, choosing `imports` or `exports`. Start each flow in its own output. Leave `refresh` false for a fresh acquisition or recovery; select true only when deliberately acquiring another source generation. To restore a prior private artifact, provide its completed `resume_run` ID. The fixed plan remains the same on acquisition and recovery.

The workflow uses the `census-ingestion` environment and repository `CENSUS_API_KEY`, read-only repository/Actions permissions, pinned Actions, shared acquisition concurrency and a twenty-minute job cap. The key belongs only in trusted main ingestion; do not read or retrieve it locally or expose it to PR code. Inputs are validated environment values passed as quoted arguments. A private `census-partners-{runId}` artifact retains safe completed or partial evidence for seven days.

CLI reference used by the trusted runner:

```powershell
python -m pipeline.partners --plan sources/scans/coffee-partners-2026-07.json --flow imports --output .local/partner-discovery
```

Use the same root to resume a checked local acquisition; `--refresh` requests a new generation. For trusted Actions recovery into a new empty destination, append `--resume-run RUN_ID --repository Vasuki8/us-trade-explorer`. The restore CLI uses the process `GH_TOKEN`; never put a token or Census key in command arguments, tracked files or chat. Prefer the main workflow for authenticated acquisition and recovery. `verify_partner_scan(plan, flow, root, secrets=())` provides offline validation of preserved evidence without fetching Census data.

The separately named downloader accepts only completed manual main executions of `.github/workflows/census-partners.yml` in the requested repository, and their exact unexpired `census-partners-{runId}` artifacts. A completed failed run may carry recoverable partial evidence; accepted transport provenance does not make its generation complete. Existing normalized-batch and archived-singleton protocols keep their original paths, limits and trust rules and do not accept discovery evidence.

Restore checks repository/workflow/main provenance, artifact digest, redirects, compressed/unpacked bounds, safe paths/types and the entire snapshot contract before destination writes. Only `raw/`, `scans/` and `receipts/` hash-named JSON objects, `progress.json` and `complete.json` are permitted evidence paths. Authorization is sent only to the GitHub API and is never forwarded to signed storage destinations. Wrong flow or plan, unexpected entries, missing history, corrupt bytes, reflected credentials or inconsistent receipts fail restoration.

## Failure and recovery

The journal distinguishes `pending`, `successful` and `failed` acquisition attempts. Only a successful attempt records its scan/receipt references. Strict current verification requires that successful journal generation to match the pointed receipt. A prior complete pointer retained after a failed refresh remains recovery evidence; it cannot masquerade as a successful current acquisition.

- **Source or refresh failure:** preserve the directory and safe partial artifact. Resume the current attempt through the main workflow. To deliberately use older successful evidence, select that earlier run explicitly.
- **Missing or corrupt cached evidence:** validation fails before any API call, even with `--refresh`. Preserve the damaged root for diagnosis; restore a verified artifact into a fresh empty destination or begin fresh acquisition in another root. Do not overwrite immutable objects.
- **Interrupted journal, object or pointer write:** revalidate retained complete objects and retry the current attempt. A receipt without matching journal success does not satisfy strict verification. Valid orphans and regular pending temporaries stay available without counting as completed observations.
- **Writer lock:** confirm that its process has stopped before removing a stale lock. Do not steal an active lock or run competing writers against the same root.
- **Expired artifact or exhausted history limits:** preserve and verify existing private evidence first. A new trusted acquisition may return changed bytes; it cannot recreate the old vintage. Do not casually raise caps to accommodate history.

Source connections use bounded retries, five-second connect timeouts and thirty-second response watchdogs. OS DNS resolution is not independently hard-bounded by those socket deadlines; the outer Actions cap remains the recovery boundary. Seven-day artifacts and ignored `.local/` development copies are not independent durable backups. Preserve needed evidence in controlled private storage before expiry.

## Verification and publication gates

The [implementation plan](superpowers/plans/2026-10-02-census-partner-discovery.md) defines source, scan/store, restore, workflow, review and live-verification work. The [handoff](handoff.md) and linked implementation PR record actual test counts, final-head/main checks, independent review and authenticated import/export recovery receipts. This operator guide alone is not a receipt for a passing test, successful live run or merged implementation.

Publication still requires reviewed per-flow/per-period inventories covering special statistical buckets and territories, non-overlapping aggregate rules, compatible source dimensions and revision vintage, exact full-world reconciliation with documented rules, classification comparability and an explicit validated public projection/loader. Observed-partner counts or a successful receipt cannot satisfy those gates.

The website remains synthetic, labelled sample and noindex, with production publication blocked. Private raw responses, scan history and credentials stay outside Git and public artifacts. AWS provisioning, spending, advertising and commercial integrations remain deferred. Existing [Census API terms and attribution safeguards](census-archive.md) and the [dated legal/privacy matrix](design/05-legal-and-privacy.md) continue to apply; discovery adds no broader reuse or compliance claim.

See the [exact-response archive guide](census-archive.md), [selected-market control guide](census-controls.md) and [operations guide](operations.md) for their distinct evidence protocols and recovery procedures.
