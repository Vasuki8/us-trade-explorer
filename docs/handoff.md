# Development handoff

Updated **2 October 2026**. This is a working handoff for a maintainer without the conversation history. Exact receipts below record merged implementation, verified private acquisition/recovery and the remaining public-release gates.

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

Verified runtime baseline: [PR #13](https://github.com/Vasuki8/us-trade-explorer/pull/13), main merge **`b7e470ba749679f93c026afedf916dad531e05f8`**. Its final head was `a1cb7effcd7e70af329f1bcfac76b78ff25f3901`; final-head and main Checks passed. Subsequent documentation-only changes record receipts without changing that runtime. Check the [repository history](https://github.com/Vasuki8/us-trade-explorer/commits/main/) for the current main commit.

The owner explicitly granted **standing authorization to merge tested, reviewed PRs**: “from now onward you dont have to ask me for merge permission.” This instruction supersedes the earlier automatic review restriction to individually named PRs; **do not re-ask for merge permission**. Complete implementation, relevant tests, independent review and final-head CI before merging, and record the merge and subsequent checks here. This authority does not change the private-repository, spending, provider, AWS-deferral or public-launch boundaries above.

## Current public application

Astro 7.3.5, TypeScript 6.0.3, Node 24 and a standard-library Python pipeline. The single Astro application lives at root `src/`; shared TypeScript contracts are in `packages/contracts/`, ingestion in `pipeline/`. No database service or subscription backend runs yet.

Thirty prerendered HTML pages cover overview, search, product and country profiles, exploration, comparisons, changes, methodology, sources, release/status/privacy and a real 404. Root and `/us-trade-explorer/` paths are tested. Origin and path are configurable through `SITE_URL` and `BASE_PATH`.

The website uses **synthetic data only**: four HS2 chapters, five countries plus illustrative world totals, and 25 months. Pages are labelled sample and noindex; the sample sitemap is empty. `PUBLICATION_MODE=production` deliberately fails. `src/lib/data.ts` still selects the sample fixture; real private candidates/reports do not feed HTML or downloads. Do not remove the production guard or label sample values official because acquisition passes.

GitHub's Pages setup returned HTTP 422 because the current plan does not support Pages for this private repository. No Pages website was created; `ENABLE_GITHUB_PAGES_PREVIEW` is unset. Latest [private preview build 37035527239](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035527239) succeeded on PR #13's main merge and skipped deployment. Local preview and private 14-day build artifacts are available; the intended `vasuki8.github.io/us-trade-explorer/` URL is **not a verified hosted site**. GitHub Pages also lacks the planned production header/log controls and has commercial-use restrictions. See [GitHub development](github-development.md); AWS remains deferred.

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
| PR #13 final-head Checks [37034560955](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37034560955) | All 131 Python tests passed on Linux without skips, plus 9 Node tests, Astro/build checks, 16 browser journeys at each tested base path and production rejection |
| PR #13 main Checks [37035527230](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035527230) | Same complete checks passed on merged `b7e470ba749679f93c026afedf916dad531e05f8` |

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

See [acquisition](census-acquisition.md), [batch/recovery contracts](census-batches.md), [private control evidence](census-controls.md), [exact-response archive](census-archive.md) and [operations](operations.md) for boundaries and procedures. PR #12's candidates/report retain source hashes and normalized evidence, **not raw statistical payloads**. PR #13 adds exact-response archiving on main; its live verification is recorded separately below. The pinned announcement PDF is a different kind of evidence and does not replace raw statistical bytes.

## Evidence retention and recovery

Actions ingestion/report artifacts expire after **seven days** and are not backups. Existing market artifacts expire on 9 October 2026; the report artifact expires **2026-10-09T15:23:56Z**. Its ID is `11236035043`, compressed size 1,656,621 bytes, archive SHA-256 `5e0c511bab31e6c9a5335d4073a0d1fb9b4ff6493d02a982f747eafc289f66c0`.

Verified private development copies are under the worktree's ignored `.local/batch-evidence/`, `.local/control-evidence/` and `.local/archive-evidence/`. Their `verification.json` files record checks without source amounts or credentials. The control copy preserves both normalized snapshots, the announcement proof/PDF and the report. The archive copy contains four verified run directories, described below. `.local/inspect-live-batches.py`, `.local/inspect-control-evidence.py` and `.local/inspect-archive-evidence.py` are ignored, machine-specific helpers, not a portable interface. Preserve needed evidence in controlled private storage before expiry; local copies are not independent durable backups.

To recover while an artifact is unexpired, use trusted main workflows and the same reviewed plan. **Acquire Census batch** and **Acquire archived Census batch** accept `markets` or `world-controls`, `resume_run` and `refresh`; market and world snapshots must use separate destinations. Select the archived workflow to retain actual source bytes; its restore entry point accepts only archived workflow artifacts. **Verify private Census controls** accepts completed successful normalized market/world run IDs; it does not consume new archived snapshots. Restore verifies repository/workflow/main origin, digest, sizes, paths, JSON and object relationships before writing. A failed refresh may preserve an earlier batch pointer, but the report/archive verifier refuses to silently use that earlier generation. Recover the batch first or deliberately select its earlier successful run.

If artifacts expire, preserve and verify any existing local copy offline. Otherwise acquire new trusted main batches and rerun the control workflow. A new fetch can change source bytes and identities; it does not recreate the old vintage or establish an official revision date. Never repair a corrupt immutable file in place or replace missing data with zero. A normalized historical artifact cannot become a raw archive without refetching exact source bytes.

## Security and operating boundaries

- `CENSUS_API_KEY` exists as a **repository secret**. Trusted main ingestion uses the `census-ingestion` environment. Read-only configuration checks on 2 October 2026 confirmed its sole custom deployment branch is main; no required-reviewer protection rule was reported. Main branch protection remains unverified. Do not read, request, paste or write the key locally; never expose it to untrusted PR code.
- Acquisition uses fixed approved sources, schema/scope/size checks, bounded retries, timeouts and redacted allowlisted diagnostics. Known secrets are checked in raw and decoded evidence before persistence. Never enable verbose HTTP logs, print signed download URLs or store token-bearing URLs.
- Source calls use five-second connect timeouts and thirty-second response watchdogs, with a twenty-minute Actions cap. OS DNS resolution is not independently hard-bounded by those socket deadlines. Existing batch snapshots are limited to eight explicit slots, 2 MiB, 48 files and 64 KiB per JSON member.
- In Actions, private artifact retrieval uses a token with read-only repository/Actions permissions. The local verifier uses Git Credential Manager's available credential in memory; its account scopes were not verified. Authorization is sent only to the GitHub API and never to signed storage destinations. The Census key was unavailable locally; its reflection checks ran inside protected workflows.
- Public builds do not include `.local/`, pipeline outputs, reports or private snapshots. Secrets, raw/history data and runtime evidence must stay out of Git and public artifacts. CI has read-only permissions, pinned Actions, locked packages and no PR secrets.
- No server-side authorization/session/entitlement/payment system exists yet. Build that boundary before accounts or paid workspaces. Future checkout must be hosted by a reputable processor with signature-verified, idempotent webhooks; never hide private data merely with UI controls or noindex.
- Before commercial hosting, verify actual HTTPS/headers, logs/IP processing, provider locations/retention, privacy contacts and incident recovery. Launch ads, analytics, email, B2C renewals or international sales only after their actual providers/data flows and feature-specific legal/accounting gates are resolved. Census attribution/non-endorsement is required; no government logo or unrestricted third-party-licence assumption is authorized.

## Raw archive implementation and live verification

The [implementation plan](superpowers/plans/2026-10-02-census-raw-archive.md) is implemented and merged in [PR #13](https://github.com/Vasuki8/us-trade-explorer/pull/13). It adds a separately named archived-batch protocol around the established normalized contract: exact content-addressed response bytes, independently reparsed candidate scope/hash/rows, a verified archive receipt and bounded trusted-main artifact restore. Legacy normalized batches and control reports stay compatible. The [archive guide](census-archive.md) describes commands, bounds, migration and interruption recovery.

Implementation/review head **`6775535c66144e435b008bafbe8949cda5263e19`** was reviewed against main `3b0f42d8704f4424c15aa2351cbb2a2593b48281`. One fresh independent whole-branch review found **no critical, important or minor findings** and independently reran the complete Python suite. Final PR head `a1cb7effcd7e70af329f1bcfac76b78ff25f3901` added documentation receipts; [final-head Checks 37034560955](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37034560955) passed before the authorized merge at `b7e470ba749679f93c026afedf916dad531e05f8`.

The local Python suite on 2 October 2026 reported **131 tests**, with one directory-symlink test skipped because this Windows machine lacks the privilege. **9 Node tests**, Astro check with zero errors/warnings, and a 30-page build with internal-link, sample/noindex, secret-pattern and asset checks passed. Final-head and merged-main CI passed **all 131 Python tests on Linux without skips**, including that directory-symlink regression, plus 9 Node tests, Astro checks, both configured builds, **16 browser journeys at each base path**, and production-publication rejection.

Recovery regressions reproduced and fixed two interruption cases: a valid orphan appearing after an earlier complete receipt, and a leftover regular `.pending-*` write. The former is independently checked and can be incorporated offline; strict verification still requires exact retained inventory. Temporaries remain locally and never count as evidence. Missing/corrupt raw evidence for a normalized candidate still fails before networking.

Review scope decisions: full inventory, vintage, classification and public projection remain publication gates; controlled local evidence and seven-day private artifacts are development storage rather than independent durable backups. Refresh history must stay within fixed bounds, and stale locks require an operator to confirm the process stopped. Hostile concurrent filesystem replacement and independently hard DNS deadlines are not new guarantees. These limits are accepted for this private increment; removing them requires explicit engineering and operational verification, and an incorrect assumption could lose recovery evidence or misstate completeness.

Four authenticated archived workflow jobs succeeded on trusted main `b7e470ba749679f93c026afedf916dad531e05f8`:

| Plan | Fresh acquisition | Actions recovery without refresh |
|---|---|---|
| Markets | [37035812076](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035812076), job `110933624956` | [37035964431](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035964431), job `110934132670` |
| World controls | [37035816019](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035816019), job `110933800315` | [37035998991](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37035998991), job `110934248940` |

The independent verifier confirmed each run's exact repository, manual main workflow, merge commit, artifact name/digest/size and bounded inventory. It reparsed every retained raw response against its candidate and approved slot, verified hashes and matching successful journal/bundle/receipt generations, then ran offline archive verification before promoting the staged local copies. Each market snapshot has **21 files, 8 raw responses and 8 candidates**; each world snapshot has **9 files, 2 raw responses and 2 candidates**. Neither contains raw orphans. Each fresh/recovery pair preserves **every file and byte**, including immutable receipt/bundle identities. The 30 files across the two fresh snapshots are retained in 60 copied files across four run directories, containing 10 distinct raw responses. ZIP-container hashes differ between runs; the member evidence is identical within each pair.

| Plan | Archived normalized bundle | Exact-response receipt |
|---|---|---|
| Markets | `788088255fea656383565046e4ae06af4c6459407befc072680bab745ac398d3` | `546d4edef8b01061b2ea0ada205c7d5bff6e6497fa642d673eef0f9369521ddf` |
| World controls | `d1ef650ad03b65aa1780cd5f92232b198545a287bcec80cbf4372ce2343c392b` | `f36936f3d83f9b835e62408aefee1fcab4c0f684e3285016e70691be0b376375` |

Plan IDs remain the reviewed market/world identities above. The archived bundles have new normalized object hashes/ingestion times; they are distinct from PR #12's historical inputs and do not silently upgrade its report.

| Run role | Artifact ID | ZIP bytes | Expires (UTC) |
|---|---|---|---|
| Markets fresh | `11240190607` | 14,336 | 2026-10-09 16:43:30 |
| Markets recovery | `11239027554` | 14,336 | 2026-10-09 16:44:35 |
| World fresh | `11240470541` | 5,549 | 2026-10-09 16:43:56 |
| World recovery | `11239771391` | 5,549 | 2026-10-09 16:44:55 |

Verified ZIP SHA-256 values:

```text
markets fresh    98f47f7321e66bee668d51d666e6d37d403c5cb6f0983db5bb0b3ea16c3da226
markets recovery c52e4de8e3c3a113ff2b22bd1e580e80b09f494068d907113fb0c98b8c157a96
world fresh      137b52fd3d1f698b86b5acea17904b831eae6fabc5819410f5121be82fff1dea
world recovery   7b6b29b97fc784e1c7918b8d65a0861ffd60134e1548defc0fa46263ad24d4c7
```

Private copies are `.local/archive-evidence/{runId}/` with redacted receipt `.local/archive-evidence/verification.json`. Census-key reflection was checked by the protected acquisition/recovery workflows; the local verifier **did not read or possess the Census key**. It checked its in-memory GitHub credential in raw and decoded evidence. Live induced failure/refresh and independent durable-backup restoration were not exercised; regression tests cover interruption/corruption paths. These verified captures establish the requested partitions' raw/normalized relationship, not full inventory, API revision vintage, classification comparability or world reconciliation. Publication remains blocked.

This receipt refresh was prepared on **`docs/census-archive-live`**, based on runtime main `b7e470ba749679f93c026afedf916dad531e05f8`. It records standing merge authorization and live receipts without changing runtime code. Repository/PR history records the documentation refresh's own commit, checks and integration state; a later documentation merge does not replace the runtime evidence above.

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

1. Preserve the verified archived market/world snapshots before their 9 October artifact expiry. Exact source capture, trusted-main acquisition/recovery and independent byte verification are complete for these ten singleton observations; controlled local copies still need a durable private backup strategy.
2. Design a bounded full-leaf scan and approve per-flow/per-period partner and commodity inventories, including special statistical buckets, US territories and non-overlapping aggregate rules. Reporting-code lists or selected markets are not a complete inventory.
3. Establish compatible dimensions and revision vintage, exact full-world reconciliation with documented rules and classification comparability. A `LAST_UPDATE` label, matched month or unchanged code alone is insufficient evidence.
4. Build an explicit public DTO/release projection and loader with provenance, validation receipts and missing states. Keep private evidence out of public output, preserve the last valid release on failed updates, and add meaningful production-boundary tests before changing sample/noindex/canonical/sitemap behavior.
5. After development is complete, resolve the domain/provider/company facts and scoped legal/tax questions, provision the approved host, verify real security/log/backup/rollback behavior and notices, then launch the public commercial site. Authentication, private workspaces, recurring billing and alerts remain later server-backed work.

The owner requires **a handoff update after every completed task**, including implementation subtasks, verification/review, merges and live checks. Record what changed, exact verification, current branch/integration state, remaining gates and recovery instructions before moving to the next task. Commit the relevant handoff change with that task. Leave uncertain facts explicitly unresolved; repository/PR history records documentation-only integration receipts without requiring recursive receipt PRs.

## Active increment — partner discovery

Branch `feat/census-partner-discovery` starts from main `dbdbf03606e9355783b201499d1386d16d9d2759` (merged documentation PR #14; main Checks 37038097016 passed). The [plan](superpowers/plans/2026-10-02-census-partner-discovery.md) captures all observed DET partners for July 2026 / HS2 09, preserving exact raw bytes, independently verified observations, bounded cache/restore and attempt state. Maximum 500 rows, 512 KiB per object, 2 MiB snapshots, 20 files/24 ZIP entries. It labels numeric codes unreviewed detail rather than approving geographic leaves; world `-` remains a separate control. No authenticated discovery run is claimed yet. Existing public/sample and publication gates remain.

Completed task 1: added explicit DET, smaller transport/normalization limits and strict bounded JSON decoding while preserving default singleton queries and identities. Eight new source tests were first observed failing for the absent interfaces, then passed with implementation. The focused command `py -3.14 -m unittest pipeline.tests.test_partner_source pipeline.tests.test_census_acquisition pipeline.tests.test_world_controls pipeline.tests.test_raw -q` passed **30 tests**. Task 2 (private discovery/store) and task 3 (separate trusted artifact restore) remain in progress; final whole-branch review and CI have not yet run for this increment.
