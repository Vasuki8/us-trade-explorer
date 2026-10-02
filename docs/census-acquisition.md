# Census acquisition development — 2 October 2026

## Evidence and scope

The first main-branch acquisition, [run 36957552437](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36957552437), failed after three bounded attempts. Its generic error did not retain the transport stage or HTTP status. It uploaded no candidate and changed no public data. We cannot establish its exact cause or whether Census accepted the key from that log.

The public metadata endpoint was reachable without a key during this investigation: HTTP 200, 13,710 bytes, about 0.6 seconds from the local machine. This demonstrates metadata connectivity from this machine, not authenticated data access from GitHub's runner.

The current [Census trade API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf) identifies broad-query timeouts, recommends smaller requests and YEAR/MONTH predicates, and documents `-` as a total marker. These support the connector changes; they do not retrospectively prove the first failure's cause. Import and export field names were checked against their official [import](https://api.census.gov/data/timeseries/intltrade/imports/hs/variables.html) and [export](https://api.census.gov/data/timeseries/intltrade/exports/hs/variables.html) metadata.

## Implemented behavior

- A fixed set of safe error categories and optional numeric HTTP status survives retries. Logs omit URLs, headers, bodies, credentials and raw exception messages.
- The default is a single-month HS2 09 / Canada 1220 probe. Inputs are validated before networking. Broader wildcards are explicit choices and remain subject to the original size/time/retry limits.
- YEAR/MONTH predicates replace `time` in requests. Returned YEAR/MONTH and legacy `time` representations are validated; contradictory representations fail.
- Requested aggregate dimensions are mandatory and must equal `-`. The previous guessed `0`/`00` expectations are removed. Out-of-scope observations and duplicate keys fail validation.
- Private candidate schema v2 records the sanitized query and unverified requested scope. Query-aware identity preserves repeatability without confusing a narrow probe with a broader request that returned the same rows.
- HTTP 204 is reported as no records, without generating a zero observation or an empty candidate.

## Recovery and next live verification

Local verification: all 21 Python tests passed, including the existing source limits, credential reflection, atomic activation and rollback tests. New diagnostics and request-contract tests failed against the previous implementation before being corrected. CLI tests verify that repeated candidates create one file, different request scopes remain distinct and a failed request preserves existing evidence. Authenticated source queries have not been rerun with this branch's code; mock responses in tests are fabricated, not official figures.

Independent review found no actionable defects and also exercised a fabricated HTTP success through transport and candidate creation. GitHub Checks run 36965085903 passed for implementation commit `bb4e92d1e199cd67e43eef310ca485423c9d0196`, including pipeline, frontend and browser checks. Live source verification remains a required next step.

Timeout limitation retained from the previous connector: the socket connection timeout does not impose a hard deadline on operating-system DNS resolution. The socket watchdog protects response headers/body after connection; the 20-minute Actions job cap is the outer bound for a stalled lookup. Resolver/process isolation is a future reliability improvement. These tests do not establish a 30-second wall-clock cap across DNS.

Review and merge the acquisition change before dispatch; the secret-bearing workflow remains restricted to trusted `main` and the `census-ingestion` environment. Start with imports, July 2026, HS2 09, partner 1220. Inspect safe diagnostics or the private artifact, then test the corresponding exports partition. A successful response still needs source semantics, official dates, classification/partner inventory, reconciliation and release assembly before replacing the synthetic website.

Candidate schema v1 files, if any exist locally, are historical development evidence and must not be promoted or silently relabelled as v2. New candidate filenames use a full digest of the contract version, flow, period, sanitized query and raw source hash. Repeating identical source content for the same query preserves the first evidence file and ingestion timestamp.

Website hosting, subscriptions and AWS provisioning are outside this increment. PR #7 holds the separate GitHub development-preview work; this branch is based on `main` and changes ingestion only.
