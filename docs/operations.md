# Running and operating the public preview

This increment is a working sample website and tested acquisition/release foundations. It is not a deployed official-data service. Production builds deliberately fail until live coverage, reconciliation, hosting controls and operating notices are verified.

## Local development

For the current GitHub-first development phase, see [GitHub development](github-development.md), [permanent instructions](../AGENTS.md) and the [operating-model decision](decisions/2026-10-02-operating-model.md). The agent performs routine setup/tests/recovery; these commands are maintainer instructions, not work to hand back to the product owner. No cloud account is needed to build/test the preview.

Requirements: Node 24 LTS and Python 3.12 or newer (tested on Python 3.14). Python pipeline code uses only the standard library.

```sh
npm ci --ignore-scripts
npm run dev
```

Astro listens on loopback only. Set `ASTRO_TELEMETRY_DISABLED=1` in the shell to disable framework development telemetry. The browser application has no telemetry or third-party dependencies. On Windows PowerShell use `$env:ASTRO_TELEMETRY_DISABLED='1'`.

```sh
npm test
python -m unittest discover -s pipeline/tests -v
npm run check
npm run build
npx playwright install chromium
npx playwright test
```

On Windows, `py -3.14` can replace `python`. For an installed Chrome, set `PLAYWRIGHT_CHANNEL=chrome` and omit the browser download. Tests launch an isolated profile and do not use saved browser sessions. Node tests run in one process so restricted environments need fewer subprocess permissions. Some Windows sandboxes prevent reopening Python's private temporary directories or starting the Astro compiler; those checks need a normal local shell.

Build output is `dist/`. `SITE_URL` accepts a clean HTTPS origin and `BASE_PATH` accepts `/` or `/trade/`-style paths. Example shell settings: `SITE_URL=https://example.com BASE_PATH=/trade/ npm run build`. Public links, datasets, styles and canonical paths use that base. Domain remains a placeholder until chosen. No sample URL is added to the sitemap, and all HTML is noindex. This is an indexing instruction, not access control.

## Connect the Census key safely

See the [acquisition development record](census-acquisition.md) for the failed first request, source evidence and recovery scope.

1. In the repository's **Settings → Environments**, create `census-ingestion`. Restrict deployment branches to `main`, enable required reviewer approval where supported by the repository's plan, and disable administrator bypass where available. If these protections are unavailable, keep acquisition disabled until an equivalent trusted execution boundary is configured.
2. The user has already saved a **repository secret** named `CENSUS_API_KEY`; the workflow can resolve it without seeing its value here. Prefer migrating it to an environment secret of the same name when environment protections are configured. Never put its value in source files, issues, PR descriptions or chat. GitHub masking supplements the connector's own redaction; it is not the only protection.
3. Review and merge this branch before running the acquisition workflow. It refuses to use a non-main ref. Protect changes to `.github/workflows/`, `pipeline/`, source contracts and release validation through branch reviews. Untrusted PR checks have read-only permissions and no secrets.
4. Run **Acquire Census candidate** manually for one flow and one month, initially with product `09` and partner `1220` (Canada). The workflow and CLI now default to this small probe. Use an explicit `*` only after the probe succeeds and its dimensions are inspected. Each job has a 20-minute cap. The connector allows three attempts, a 5-second connection timeout, a 30-second response deadline, 10 MiB responses and 100,000 rows per partition. Redirects and unapproved hosts are rejected.
5. Inspect the private candidate artifact within seven days. Schema version 2 stores normalized fields, the source hash, requested scope and a query map built only from validated codes and fixed parameters. It never stores the key or credential-bearing request URL. Candidate identity includes the query and source hash so different scopes cannot collide when responses happen to match. Source rejection is reported without echoing source text, transport exception text or URLs.

The request uses `YEAR`/`MONTH` and explicitly filters district and import provision/subcode or export domestic/foreign dimensions to `-`. All requested aggregate dimensions must appear in the response and match. The parser checks each returned period representation, rejects conflicting dates, and rejects rows outside the requested product/partner. The Census guide recommends smaller requests, describes `YEAR`/`MONTH` as less prone to timeouts than `time`, and defines `-` as the total marker for string parameters. [International Trade API guide, pp. 7, 10–11](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf)

Wildcard results preserve Census partner codes, including the `-` aggregate. Four-digit codes are not yet classified into countries versus special areas/groups. Do not add every returned row together: validate the official partner inventory and separate overlapping aggregates before reconciliation. `coverage: unverified` applies even to a successful small probe. A no-results HTTP 204 stops acquisition with `no_results`; it produces neither an invented zero nor a candidate.

Each failed attempt emits only a fixed event name, attempt number, allowlisted category and optional HTTP status. `connect_timeout`, `headers_timeout`, `body_timeout`, `dns_error`, `tls_error`, `connection_error` and `protocol_error` distinguish transport stages. `rate_limited` and `upstream_unavailable` keep the bounded retry policy. `http_rejected` needs credential/parameter/source review and does not by itself prove that the key is invalid. `validation_failed` stops without retry. The final CLI message retains the last safe category. Never enable verbose HTTP traces to recover the missing detail.

This first connector is **candidate-only**. Its handling of default Census dimensions and zero markers must be confirmed against a real response. Unknown layouts fail closed. Official publication/revision dates remain unknown until their supporting official evidence is attached. A successful request is not evidence of coverage or official reconciliation.

## Release promotion remains a separate gate

Private [market/world control reports](census-controls.md) now attach verified initial-announcement evidence and exact selected-market checks. They retain the full-coverage, revision-vintage, raw-archive and classification blockers and cannot activate public data. The [batch record](census-batches.md) contains the successful live market acquisition/recovery receipts.

The public fixture cannot be switched to official mode with an environment variable. Before introducing an official release loader:

- Establish the complete HS2 chapter and partner inventories for each period, including aggregate/special codes. Preserve classification vintages; do not infer missing observations as zero.
- Verify import/export source dimensions and connect a comparable official control. `pipeline/reconcile.py` proves exact integer reconciliation only for a caller-approved complete group; it does not establish comparability for arbitrary source rows.
- Archive bounded raw payloads in private storage, with response hashes and secret scanning. Current candidate artifacts contain normalized evidence, not a full historical raw archive.
- Assemble release partitions with explicit missing states, dates, transformation commit, input hashes and a validation receipt. Run failed-update and secret-canary tests before activation.
- Generate substantive official profiles, choose indexable base routes, update canonical/sitemap rules, verify source notices and remove the production gate only through reviewed code.

`pipeline/store.py` is a local model of immutable content plus atomic activation. The caller must pass a trusted validator. Tests prove identical payloads are deduplicated, validation failures preserve the active pointer, interrupted writes do not partially activate, and rollback verifies checksums. It is not an S3/CDN transaction implementation. An interrupted process can leave `activation.lock`; confirm no writer is running and inspect the active object before manually removing that lock. Never automatically steal a lock from a possibly live writer.

## Preferred future hosting and previous AWS contract

The owner now prefers Workers + Static Assets/R2, optional D1 for smaller metadata and analytical objects/Parquet where appropriate. No Cloudflare account/service, runtime adapter or migration is implemented. Provider-supported identity, actual HTTP/security headers, logs/retention/locations, source terms, cost, backup/rollback and notices need fresh verification before authorized provisioning. Preserve the existing static URL and internally consistent release contract. Do not promise India residency or apply historical Pages limits to Workers.

The AWS instructions below are retained as the **superseded 1 October candidate**, not the current deployment mandate. Existing CloudFront configuration/test fixtures remain unchanged. Recheck this alternative only if justified and authorized; neither these commands nor this instruction update provision resources.

Use private S3 REST origins with Block Public Access, bucket versioning, encryption and CloudFront Origin Access Control. Do not expose the bucket website endpoint. A short-lived GitHub OIDC role should write only candidate release prefixes; production activation should be a separate trusted step. Public and private future storage use separate permissions and origins.

Upload a complete immutable release directory, verify object hashes and HTML/data smoke tests, then activate the matching CloudFront origin path. Cache propagation is not globally atomic; every page pins its data release so a visitor gets an internally consistent view. Rollback selects a known earlier directory. Retain prior releases and independently restore a backup before declaring launch readiness.

CloudFront needs directory-index rewrites, slash normalization, query-preserving redirects, explicit JSON/CSV types and a real error page. Map missing-origin 403/404 responses to the 404 document **with HTTP 404**, not a homepage 200. Immutable assets use long cache lifetimes; HTML and activation state use short, deliberate cache settings. Keep old release-pinned URLs available.

`infra/cloudfront/response-headers.json` contains the proposed response policy. Local browser tests inject its CSP to verify compatibility; this does not prove cloud enforcement. Apply HTTPS redirect, the reviewed header policy and authenticated preview access on the actual distribution. Confirm each header with real HTTP requests. A noindex preview is still public if hosted without access controls.

Before selecting a paid AWS plan, recheck its commercial terms and custom policy support. Configure budget alerts (alerts do not cap spending), selected security logging and the reviewed India log archive/retention settings from the design. Validate actual data locations and deletion behavior. No AWS resources or ongoing charges are created by this branch.

## Freshness, recovery and incidents

Production freshness must compare the active data period with the official publication calendar and release status. Revisions have a separate check. A failed scheduled ingestion or expired expected release should notify an administrator independently of the deployment job and show a clear stale-data notice without replacing the last good data. This scheduler and notification destination are not enabled yet.

Administrators should use MFA, branch reviews and separate ingestion/deployment roles. If a key is exposed, stop acquisition, revoke/rotate the key at Census, inspect repository history/artifacts/logs, remove affected evidence according to the incident procedure, and verify a fresh candidate before resuming. Do not rely on merely deleting a visible line. Infrastructure recovery must rehearse restore and rollback on the chosen provider before launch.

## Privacy and commercial features

There are no accounts, subscriptions, email, ad tags or analytics in this preview. Search/filter state lives in URLs and may be visible to the eventual host. Hosting still processes IP addresses and request metadata. Complete notices from actual providers, retention and company contact details before public operation. Keep direct sponsor creatives local and labelled when introduced; obtain usage rights first. No sponsor relationship is implied by the current UI.

The future authentication/workspace/payment design remains in `docs/design/`. No private content or paid entitlement is protected by this static application. Implement server-side authorization and private storage before adding those features.
