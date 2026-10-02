# Development handoff

Updated **2 October 2026**. This is a working handoff for a maintainer without the conversation history. Exact receipts below describe completed work; the separate development section describes work that is still in progress.

## Purpose and confirmed decisions

Build a light, searchable US import/export analytics reference. Public profiles explain products and countries, trade flow, period, measured changes, comparisons, statistical basis and sources, with shareable links and safe downloads. Initial revenue is intended to come from advertising, starting with direct sponsorship; future subscriptions add saved workspaces, watchlists, alerts, advanced comparisons and reports. Useful public profiles remain free.

- The operator is in **Gujarat, India**. Target markets are the US, Canada, Mexico, China, India and Europe **including the UK**. Future subscriptions serve businesses and consumers. These facts came from the owner; device location is irrelevant. Exact European countries, company identity/address, registrations and contact details remain unresolved.
- The owner approved the current light interface and chose **private GitHub development now; AWS after development is complete**. There is no authorization to change repository visibility, buy a plan, incur cloud spending or introduce commercial integrations.
- The provisional US$25–50 monthly infrastructure estimate is a planning assumption. Domain and hosting, ad, analytics, email and payment providers are unselected. No AWS resources, accounts, subscriptions, ads, trackers or payment flows have been deployed.
- “Legal assessment” means practical safeguards while building, plus feature-specific launch reviews. Use verified operating facts and the dated matrix; do not claim universal legal compliance or copy notices for providers that are not operating.

The approved design is in [architecture](design/01-architecture.md), [public and subscriber flows/SEO](design/02-experience-and-seo.md), [data model](design/03-data-model.md), [threat model](design/04-security.md), [jurisdiction/licence/privacy matrix](design/05-legal-and-privacy.md) and [phased delivery](design/06-delivery-plan.md). Mermaid diagrams remain reviewable source. Their intended controls are not automatically implemented controls. Legal research in the matrix is dated 1 October 2026; recheck the affected official sources before launching a gated feature.

## Repository, checkouts and authorization

Repository: [Vasuki8/us-trade-explorer](https://github.com/Vasuki8/us-trade-explorer), **private**.

| Checkout | Local path | Purpose |
|---|---|---|
| Primary | `D:\Projects\ChatGPT\New folder\us-trade-explorer` | Clean main checkout |
| Development worktree | `D:\Projects\ChatGPT\New folder\us-trade-explorer-mvp` | Current feature work and ignored private evidence |

The sibling worktree is a manually linked Git worktree, not a managed Codex attachment. Retain it, especially ignored `.local/` evidence, unless recovery copies have been preserved. Verify `git status`, branch and current main before making changes; do not reset or clean another worker's modifications.

Latest verified main merge: [PR #12](https://github.com/Vasuki8/us-trade-explorer/pull/12), commit **`3b0f42d8704f4424c15aa2351cbb2a2593b48281`**, explicitly approved by the owner. Earlier named PR approvals have been consumed by their corresponding merges. The owner has authorized continued development and updating this handoff; **a new PR is not yet authorized for merge**. An earlier automatic approval review limited merge authorization to named PRs. Complete implementation, tests, independent review and CI first, then request the new PR's specific merge permission. Do not work around that restriction with a different merge tool.

## Current public application

Astro 7.3.5, TypeScript 6.0.3, Node 24 and a standard-library Python pipeline. The single Astro application lives at root `src/`; shared TypeScript contracts are in `packages/contracts/`, ingestion in `pipeline/`. No database service or subscription backend runs yet.

Thirty prerendered HTML pages cover overview, search, product and country profiles, exploration, comparisons, changes, methodology, sources, release/status/privacy and a real 404. Root and `/us-trade-explorer/` paths are tested. Origin and path are configurable through `SITE_URL` and `BASE_PATH`.

The website uses **synthetic data only**: four HS2 chapters, five countries plus illustrative world totals, and 25 months. Pages are labelled sample and noindex; the sample sitemap is empty. `PUBLICATION_MODE=production` deliberately fails. `src/lib/data.ts` still selects the sample fixture; real private candidates/reports do not feed HTML or downloads. Do not remove the production guard or label sample values official because acquisition passes.

GitHub's Pages setup returned HTTP 422 because the current plan does not support Pages for this private repository. No Pages website was created; `ENABLE_GITHUB_PAGES_PREVIEW` is unset. [Private preview build 37026368465](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026368465) succeeded and skipped deployment. Local preview and private 14-day build artifacts are available; the intended `vasuki8.github.io/us-trade-explorer/` URL is **not a verified hosted site**. GitHub Pages also lacks the planned production header/log controls and has commercial-use restrictions. See [GitHub development](github-development.md); AWS remains deferred.

## Verified private data baseline

Statistical scope is US reporter, July 2026, HS2 chapter 09, monthly nominal USD, not seasonally adjusted. Imports are general-import customs value `GEN_VAL_MO`; exports are total domestic-plus-foreign FAS value `ALL_VAL_MO`. Approved selected countries are Canada 1220, Mexico 2010, India 5330 and China 5700. Two separate world controls use `CTY_CODE=-`, `SUMMARY_LVL=DET` and explicit aggregate dimensions. A four-digit code alone does not establish a valid leaf country.

| Receipt | Result |
|---|---|
| PR #10 imports [36967466271](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36967466271), exports [36967536133](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36967536133) | Authenticated singleton Canada observations passed |
| PR #11 market acquisition [36973640536](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36973640536) | Eight selected-market slots passed |
| PR #11 Actions recovery [36973761962](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36973761962) | Revalidated and reused all successful slots; 11 files identical to fresh evidence |
| PR #12 main Checks [37026368794](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026368794) | 96 Python tests, 9 Node tests, Astro check/build and 16 browser journeys at each tested base path passed; production rejection passed |
| PR #12 world acquisition [37026467626](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026467626) | Both authenticated world-control slots passed |
| PR #12 private report [37026664906](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37026664906) | Restored fresh market run 36973640536 plus world evidence and verified pinned announcement; 20 files independently verified, report recomputed |

Immutable identities:

```text
market plan   d65b6555a0cea3229c1cf21d52557ae177a9512d94d3857d3cc0fcdd407faaaf
market bundle 2e8ca3d5fb34b378ead182c2826950f6f977fb98f0fde70e9c558cf3077b5830
world plan    48480a611fb59eeb35dae977b5300b06b663d66a67eebd5cf65f4393df6c829e
world bundle  f624a46363ebfd9821021c1941d20398a8d6ec7715220b024a32506d5fde87d1
report        fe6327d05521da9b928977aab8bf3b2672f4c0e920f35e7d8a4071ba6fff1cb1
```

Both exact checks `selectedTotalUSD <= worldControlUSD` passed with a positive amount outside the selection. This is **subset consistency**, not complete reconciliation. The report retains `coverage=selected-markets-only`, `publicationReady=false`, `fullWorldReconciliation=not-verified` and `apiVintageVerified=false`. The official revision date is null. Private amounts are intentionally omitted here.

The [July 2026 FT900 announcement](https://www.census.gov/foreign-trade/Press-Release/ft900/ft900_2607.pdf), page 1, supports initial monthly announcement date **2026-09-03** (CB26-142/BEA26-40). Its pinned PDF is 1,826,911 bytes, SHA-256 `c122b8ccee947c58859597a7549bb5dcb6691add3e405180ab915d43f6c43aa0`. The reviewed statement is `sources/publications/ft900-2026-07.json`. This initial-announcement proof does not establish the current detailed API's revision vintage. The PDF's headline seasonally adjusted goods/services totals are not detailed-HS reconciliation controls.

See [acquisition](census-acquisition.md), [batch/recovery contracts](census-batches.md), [private control evidence](census-controls.md), and [operations](operations.md) for boundaries and procedures. Existing candidates retain raw-source hashes but **main has no archived raw statistical payloads**. The pinned announcement PDF is retained privately; these are different kinds of evidence.

## Evidence retention and recovery

Actions ingestion/report artifacts expire after **seven days** and are not backups. Existing market artifacts expire on 9 October 2026; the report artifact expires **2026-10-09T15:23:56Z**. Its ID is `11236035043`, compressed size 1,656,621 bytes, archive SHA-256 `5e0c511bab31e6c9a5335d4073a0d1fb9b4ff6493d02a982f747eafc289f66c0`.

Verified private development copies are under the worktree's ignored `.local/batch-evidence/` and `.local/control-evidence/`. Their `verification.json` files record checks without source amounts or credentials. The control copy preserves both normalized snapshots, the announcement proof/PDF and the report. `.local/inspect-live-batches.py` and `.local/inspect-control-evidence.py` are ignored, machine-specific helpers, not a portable interface. Preserve needed evidence in controlled private storage before expiry; local copies are not independent durable backups.

To recover while an artifact is unexpired, use trusted main workflows and the same reviewed plan. **Acquire Census batch** accepts `markets` or `world-controls`, `resume_run` and `refresh`; market and world snapshots must use separate destinations. **Verify private Census controls** accepts completed successful market/world run IDs. Restore verifies repository/workflow/main origin, digest, sizes, paths, JSON and object relationships before writing. A failed refresh may preserve an earlier batch pointer, but the report refuses to silently use that earlier generation. Recover the batch first or deliberately select its earlier successful run.

If artifacts expire, preserve and verify any existing local copy offline. Otherwise acquire new trusted main batches and rerun the control workflow. A new fetch can change source bytes and identities; it does not recreate the old vintage or establish an official revision date. Never repair a corrupt immutable file in place or replace missing data with zero. A normalized historical artifact cannot become a raw archive without refetching exact source bytes.

## Security and operating boundaries

- `CENSUS_API_KEY` exists as a **repository secret**. Trusted main ingestion uses the `census-ingestion` environment. Read-only configuration checks on 2 October 2026 confirmed its sole custom deployment branch is main; no required-reviewer protection rule was reported. Main branch protection remains unverified. Do not read, request, paste or write the key locally; never expose it to untrusted PR code.
- Acquisition uses fixed approved sources, schema/scope/size checks, bounded retries, timeouts and redacted allowlisted diagnostics. Known secrets are checked in raw and decoded evidence before persistence. Never enable verbose HTTP logs, print signed download URLs or store token-bearing URLs.
- Source calls use five-second connect timeouts and thirty-second response watchdogs, with a twenty-minute Actions cap. OS DNS resolution is not independently hard-bounded by those socket deadlines. Existing batch snapshots are limited to eight explicit slots, 2 MiB, 48 files and 64 KiB per JSON member.
- Private artifact retrieval uses a read-only GitHub token; authorization is sent only to the GitHub API and never to signed storage destinations. The local verifier obtains a token through Git Credential Manager and retains it only in memory. The Census key was unavailable locally; its reflection checks ran inside protected workflows.
- Public builds do not include `.local/`, pipeline outputs, reports or private snapshots. Secrets, raw/history data and runtime evidence must stay out of Git and public artifacts. CI has read-only permissions, pinned Actions, locked packages and no PR secrets.
- No server-side authorization/session/entitlement/payment system exists yet. Build that boundary before accounts or paid workspaces. Future checkout must be hosted by a reputable processor with signature-verified, idempotent webhooks; never hide private data merely with UI controls or noindex.
- Before commercial hosting, verify actual HTTPS/headers, logs/IP processing, provider locations/retention, privacy contacts and incident recovery. Launch ads, analytics, email, B2C renewals or international sales only after their actual providers/data flows and feature-specific legal/accounting gates are resolved. Census attribution/non-endorsement is required; no government logo or unrestricted third-party-licence assumption is authorized.

## Current development — not merged or live-tested

Branch **`feat/census-raw-archive`** starts at main `3b0f42d8704f4424c15aa2351cbb2a2593b48281`. The [implementation plan](superpowers/plans/2026-10-02-census-raw-archive.md) adds a separately named archived-batch protocol around the existing normalized contract. Implemented evidence is exact content-addressed raw response bytes, independently reparsed against candidate scope/hash/rows, a verified archive receipt, and bounded trusted-main artifact restore. Legacy normalized batches and control reports stay compatible. The [archive guide](census-archive.md) describes commands, bounds, migration and interruption recovery.

Local verification on 2 October 2026 passed: **131 Python tests** (one directory-symlink test skipped because this Windows machine lacks the privilege), **9 Node tests**, Astro check with zero errors/warnings, and a 30-page build with internal-link, sample/noindex, secret-pattern and asset checks. The Linux CI run must exercise the skipped symlink test and repeat both browser base paths. Independent whole-branch review, PR creation and CI are pending at this recorded stage.

Recovery regressions reproduced and fixed two interruption cases: a valid orphan appearing after an earlier complete receipt, and a leftover regular `.pending-*` write. The former is independently checked and can be incorporated offline; strict verification still requires exact retained inventory. Temporaries remain locally and never count as evidence. Missing/corrupt raw evidence for a normalized candidate still fails before networking.

Authenticated archived acquisition and recovery can be exercised only after the new code is reviewed and approved for main. Do not imply that the PR #12 live evidence already includes raw statistical bytes. There is no new live archival receipt or approved merge yet.

## Reliable local commands

Run from the development worktree. Known runtimes are Node 24.20.0/npm 11.19.0 and Python 3.14 (`py -3.14` on this Windows machine).

```powershell
$env:ASTRO_TELEMETRY_DISABLED = '1'
npm ci --ignore-scripts
py -3.14 -m unittest discover -s pipeline/tests -q
npm run verify
$env:PLAYWRIGHT_CHANNEL = 'chrome'
npx playwright test
```

The browser suite previews the built output at loopback port 4321. Stop any stale preview that uses different build settings before switching paths. Local Chrome is used because the in-app browser/CDP connection previously timed out; this verifies isolated headless behavior, not the app browser connection. Screenshots and test output stay ignored.

CI repeats the build and 16 browser journeys with `BASE_PATH=/us-trade-explorer/` and `SITE_URL=https://vasuki8.github.io`, then checks that `PUBLICATION_MODE=production` fails with the expected message. Set the same values for a local subpath check, then restore prior environment settings before another root check. `npm run dev` serves a local sample preview. No preview URL is confirmed live merely because a process was started.

Sandboxed Windows temporary-directory access and subprocess spawning have previously produced false `WinError 5`/permission failures. If that exact limitation recurs, rerun the necessary tests/build with the ordinary execution escalation and a specific justification. Do not weaken tests or broaden permissions on evidence directories. Network pushes/API requests also need execution escalation. A failed command is not a passing receipt.

## Next publication and launch gates

1. Finish exact raw statistical capture, safe reuse/restore and failure tests; verify, independently review, push and create the new PR. Update this handoff with its actual state, obtain specific merge permission, then run authenticated archived acquisition and recovery on trusted main.
2. Design a bounded full-leaf scan and approve per-flow/per-period partner and commodity inventories, including special statistical buckets, US territories and non-overlapping aggregate rules. Reporting-code lists or selected markets are not a complete inventory.
3. Establish compatible dimensions and revision vintage, exact full-world reconciliation with documented rules and classification comparability. A `LAST_UPDATE` label, matched month or unchanged code alone is insufficient evidence.
4. Build an explicit public DTO/release projection and loader with provenance, validation receipts and missing states. Keep private evidence out of public output, preserve the last valid release on failed updates, and add meaningful production-boundary tests before changing sample/noindex/canonical/sitemap behavior.
5. After development is complete, resolve the domain/provider/company facts and scoped legal/tax questions, provision the approved host, verify real security/log/backup/rollback behavior and notices, then launch the public commercial site. Authentication, private workspaces, recurring billing and alerts remain later server-backed work.

The handoff is part of the repository's source of truth. Update it when a tested branch, approved merge, live receipt or operating fact changes; leave uncertain facts explicitly unresolved.
