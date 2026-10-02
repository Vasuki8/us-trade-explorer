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

Verified runtime baseline: [PR #15](https://github.com/Vasuki8/us-trade-explorer/pull/15), main merge **`ae769e9e530703c5aaf9bddc7783ea53908c8783`**. Its final head was `cd7b6ad27e32d41301d16719c1fc3ab1341e9112`; final-head and merged-main Checks passed. Authenticated import/export discovery and recovery were independently verified below. Subsequent documentation-only changes record receipts without changing that runtime. Check the [repository history](https://github.com/Vasuki8/us-trade-explorer/commits/main/) for the current main commit.

The owner explicitly granted **standing authorization to merge tested, reviewed PRs**: “from now onward you dont have to ask me for merge permission.” This instruction supersedes the earlier automatic review restriction to individually named PRs; **do not re-ask for merge permission**. Complete implementation, relevant tests, independent review and final-head CI before merging, and record the merge and subsequent checks here. This authority does not change the private-repository, spending, provider, AWS-deferral or public-launch boundaries above.

## Current public application

Astro 7.3.5, TypeScript 6.0.3, Node 24 and a standard-library Python pipeline. The single Astro application lives at root `src/`; shared TypeScript contracts are in `packages/contracts/`, ingestion in `pipeline/`. No database service or subscription backend runs yet.

Thirty prerendered HTML pages cover overview, search, product and country profiles, exploration, comparisons, changes, methodology, sources, release/status/privacy and a real 404. Root and `/us-trade-explorer/` paths are tested. Origin and path are configurable through `SITE_URL` and `BASE_PATH`.

The website uses **synthetic data only**: four HS2 chapters, five countries plus illustrative world totals, and 25 months. Pages are labelled sample and noindex; the sample sitemap is empty. `PUBLICATION_MODE=production` deliberately fails. `src/lib/data.ts` selects the fixed sample through its committed manifest and bounded public-only loader; real private candidates/reports do not feed HTML or downloads. JSON, CSV and the [sample metadata sidecar](public-release-boundary.md) share the validated release. Do not remove the production guard or label sample values official because acquisition passes.

GitHub's Pages setup returned HTTP 422 because the current plan does not support Pages for this private repository. No Pages website was created; `ENABLE_GITHUB_PAGES_PREVIEW` is unset. Latest runtime [private preview build 37043548932](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043548932) succeeded on PR #15's main merge and skipped deployment. Local preview and private 14-day build artifacts are available; the intended `vasuki8.github.io/us-trade-explorer/` URL is **not a verified hosted site**. GitHub Pages also lacks the planned production header/log controls and has commercial-use restrictions. See [GitHub development](github-development.md); AWS remains deferred.

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

Verified private development copies are under the worktree's ignored `.local/batch-evidence/`, `.local/control-evidence/`, `.local/archive-evidence/` and `.local/partner-evidence/`. Their `verification.json` files record checks without source amounts or credentials. The control copy preserves both normalized snapshots, the announcement proof/PDF and the report. The archive and partner copies each contain four verified run directories, described below. `.local/inspect-live-batches.py`, `.local/inspect-control-evidence.py`, `.local/inspect-archive-evidence.py` and `.local/inspect-partner-evidence.py` are ignored, machine-specific helpers, not portable interfaces. Preserve needed evidence in controlled private storage before expiry; local copies are not independent durable backups.

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

CI repeats the build and 18 desktop/mobile browser tests with `BASE_PATH=/us-trade-explorer/` and `SITE_URL=https://vasuki8.github.io`, then checks that `PUBLICATION_MODE=production` fails with the expected message. Set the same values for a local subpath check, then restore prior environment settings before another root check. `npm run dev` serves a local sample preview. No preview URL is confirmed live merely because a process was started.

Sandboxed Windows temporary-directory access and subprocess spawning have previously produced false `WinError 5`/permission failures. If that exact limitation recurs, rerun the necessary tests/build with the ordinary execution escalation and a specific justification. Do not weaken tests or broaden permissions on evidence directories. Network pushes/API requests also need execution escalation. A failed command is not a passing receipt.

## Next publication and launch gates

1. Preserve the verified archived market/world and partner-discovery snapshots before their 9 October artifact expiry. Exact source capture, trusted-main acquisition/recovery and independent byte verification are complete for the ten singleton observations and reviewed partner queries; controlled local copies still need a durable private backup strategy.
2. Review the verified DET discovery observations and approve per-flow/per-period partner and commodity inventories, including special statistical buckets, US territories and non-overlapping aggregate rules. The bounded July chapter 09 discovery is complete; observed codes and current reporting lists still do not establish a complete additive leaf inventory. Generalize periods/products only after those rules are evidenced.
3. Establish compatible dimensions and revision vintage, exact full-world reconciliation with documented rules and classification comparability. A `LAST_UPDATE` label, matched month or unchanged code alone is insufficient evidence.
4. Extend the implemented sample-only public boundary through a separately reviewed official producer/versioned contract that binds approved inventory, classification, provenance and validation receipts. Keep private evidence out of public output, preserve the last valid release on failed updates, and add meaningful production activation/rollback tests before changing sample/noindex/canonical/sitemap behavior. The checksum-pinned sample loader alone does not complete official publication.
5. After development is complete, resolve the domain/provider/company facts and scoped legal/tax questions, provision the approved host, verify real security/log/backup/rollback behavior and notices, then launch the public commercial site. Authentication, private workspaces, recurring billing and alerts remain later server-backed work.

The owner requires **a handoff update after every completed task**, including implementation subtasks, verification/review, merges and live checks. Record what changed, exact verification, current branch/integration state, remaining gates and recovery instructions before moving to the next task. Commit the relevant handoff change with that task. Leave uncertain facts explicitly unresolved; repository/PR history records documentation-only integration receipts without requiring recursive receipt PRs.

## Partner discovery implementation and live verification

Implementation branch `feat/census-partner-discovery` started from main `dbdbf03606e9355783b201499d1386d16d9d2759` (merged documentation PR #14; main Checks 37038097016 passed). The [plan](superpowers/plans/2026-10-02-census-partner-discovery.md) is implemented, reviewed, merged and live-verified within July 2026 / HS2 09, preserving exact raw bytes, independently verified observations, bounded cache/restore and attempt state. Maximum 500 rows, 512 KiB per object, 2 MiB snapshots, 20 files/24 ZIP entries. Numeric codes remain unreviewed detail; world `-` is a separate control. The task receipts below distinguish each intermediate state from the final live verification. Existing public/sample and publication gates remain.

Completed task 1: added explicit DET, smaller transport/normalization limits and strict bounded JSON decoding while preserving default singleton queries and identities. Eight new source tests were first observed failing for the absent interfaces, then passed with implementation. The focused command `py -3.14 -m unittest pipeline.tests.test_partner_source pipeline.tests.test_census_acquisition pipeline.tests.test_world_controls pipeline.tests.test_raw -q` passed **30 tests**.

Completed task 3: added a separately trusted main discovery artifact downloader with 512 KiB members, 20 files/24 entries and 2 MiB total bounds. Existing normalized and singleton-archive modes retain their 64 KiB limits, paths and provenance. Twenty-six new transport tests first failed for the missing entry point; the focused command `py -3.14 -m unittest pipeline.tests.test_partner_restore pipeline.tests.test_restore pipeline.tests.test_archive_restore -q` then passed **57 tests**, independently rerun by the primary implementer. This covers API-only authorization, path/type/size/digest checks, rejected protocol confusion and complete ZIP-index validation before decompression.

Completed task 2: implemented the separate discovery plan, strict scan/receipt contracts, immutable raw/scan/receipt store, generation journal, safe CLI and trusted restore integration. The 35 focused tests cover raw/candidate binding, unreviewed roles, missing-versus-zero behavior, secret reflection (including quoted/backslash credentials), failed refresh, cache corruption before networking, bounded restore and interruptions after each atomic write. The primary implementer independently ran `py -3.14 -m unittest pipeline.tests.test_partners -q`: **35 tests, one Windows symlink privilege skip**. The completed full pipeline suite ran **200 tests, two Windows symlink privilege skips**, with no failures; Linux CI must exercise both skipped paths before merge.

Completed workflow/documentation integration: added main-only manual **Discover private Census partners**, using the fixed reviewed plan, one flow per store, validated input environment variables, the shared acquisition concurrency group, pinned Actions, read-only permissions, the existing `census-ingestion` environment and repository secret. A twenty-minute job bound and seven-day partial artifacts exclude locks/atomic temporaries. The [operator guide](census-partners.md) records reviewed source definitions, observed roles, safe acquisition/restore and failure recovery; README and implementation status link it.

Integrated local verification: `py -3.14 -m unittest discover -s pipeline/tests -q` passed **200 tests, two Windows symlink privilege skips**. `ASTRO_TELEMETRY_DISABLED=1 npm run verify` passed **9 Node tests**, Astro check with zero errors/warnings/hints, and the 30-page sample build with internal-link, noindex, secret-pattern and asset checks (4,441 bytes gzipped JavaScript). The website was not modified by this increment. Independent whole-branch review, final-head Linux CI, merge and authenticated discovery remain outstanding. No raw discovery amounts or runtime evidence have entered Git or the public sample build.

[Draft PR #15](https://github.com/Vasuki8/us-trade-explorer/pull/15) contains implementation head `fe0d0724047fef2c41e8fbd250bb639e078c2409`. Its [Checks 37042004930](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37042004930), job `110954134557`, passed all **200 Python tests on Linux without skips**, 9 Node tests, Astro/build checks, 16 browser journeys at each base path and production-publication rejection.

Completed independent whole-branch review: base `dbdbf03606e9355783b201499d1386d16d9d2759` to immutable head `fe0d0724047fef2c41e8fbd250bb639e078c2409`; reviewer independently ran 34 source/restore tests. No critical/minor findings; one important finding reproduced a near-capacity failed-journal transition exceeding the 2 MiB snapshot bound. It must be fixed/tested and receive a scoped fix review before merge. Statistical approval, authentic results/vintage, provider enforcement/backups, controlled-writer limits, DNS deadlines and unchanged public launch behavior were explicitly set aside for their documented evidence/feature boundaries; these remain gates, not verified capabilities. No merge or authenticated discovery is claimed.

Completed review-fix task: five new regression tests first reproduced the oversized failed state and unchecked failure write. Acquisition now preflights the largest allowlisted failure journal before writes/networking; failure handling revalidates actual retained evidence, including partial atomic writes, before saving failed state. Insufficient capacity preserves prior journal, pointer and immutable bytes. The implementer ran **40 focused tests, one Windows symlink skip**; the primary implementer independently ran the full suite: **205 tests, two Windows symlink skips**, no failures. The guide documents the capacity rule. Scoped fix review and new final-head Linux CI remain required before merge.

Completed scoped fix review: immutable fix head `049f06172deaf21a442a5f12677c74aeabbc19ef`, against the prior review-receipt commit, was approved. The reviewer independently passed all five new regressions, confirmed the failure-capacity finding addressed and found no new issues in the fix wave. Final-head Linux CI must pass before the standing-authorized merge. Authenticated discovery and merged-main checks remain outstanding.

Completed final-head verification and merge: [Checks 37043267776](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043267776), job `110958328367`, passed **all 205 Python tests on Linux without skips**, 9 Node tests, Astro/build checks, 16 browser journeys at each base path and production-publication rejection on final head `cd7b6ad27e32d41301d16719c1fc3ab1341e9112`. PR #15 merged under standing owner authorization at `ae769e9e530703c5aaf9bddc7783ea53908c8783`. The clean primary checkout fast-forwarded to it. Receipt branch `docs/census-partner-live` starts from that runtime; main Checks `37043549038` and private preview `37043548932` are still running. The ingestion environment's sole custom deployment branch was independently reconfirmed as main. Authenticated scans/recoveries are next, not yet claimed.

Completed merged-main verification: [Checks 37043549038](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043549038), job `110959266353`, passed the full **205 Python tests on Linux without skips**, 9 Node tests, Astro/build checks, both 16-journey browser suites and production rejection on merged runtime `ae769e9e530703c5aaf9bddc7783ea53908c8783`. [Private preview 37043548932](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043548932) passed its build; deployment was skipped. Pages remains unavailable, and no live hosted website is claimed.

Completed authenticated fresh discovery workflows on that runtime: imports [37043703299](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043703299), job `110959788040`, passed with **138 observed rows/partners**; exports [37043711698](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37043711698), job `110959891483`, passed with **122 observed rows/partners**. Logs confirmed each requested flow and private publication-blocked state; no source amounts or credentials were printed locally. Artifact recovery and independent raw/scan/receipt/generation verification remain next. These counts alone do not establish approved geographic leaves or world reconciliation.

Completed Actions recovery and independent evidence verification on 2 October 2026: import recovery [37044026813](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37044026813), job `110960870538`, and export recovery [37044035338](https://github.com/Vasuki8/us-trade-explorer/actions/runs/37044035338), job `110961031523`, passed. All four executions are completed successful manual main runs of `.github/workflows/census-partners.yml` on runtime `ae769e9e530703c5aaf9bddc7783ea53908c8783`. An independent inspector checked that provenance, exact artifact names, run/repository bindings, ZIP digest/size/path limits and API-only authorization; independently reparsed every raw row and regenerated candidate/scan/receipt identities, query/scope/date/dimension relationships and the successful journal/pointer; then staged and reverified each preserved snapshot offline before atomic promotion. **Every member and byte matched its flow's fresh/recovery pair.** ZIP container hashes differ; member bytes do not.

| Flow | Observed rows/partners | World controls | Unreviewed detail | Explicit reported zeros | Files / unpacked bytes |
|---|---|---|---|---|---|
| Imports | 138 | 1 | 137 | 25 | 5 / 49,949 |
| Exports | 122 | 1 | 121 | 31 | 5 / 43,974 |

Each snapshot contains one raw response, one scan, one immutable receipt, a successful generation-1 journal and its pointer. Absent rows remain unobserved. No four-digit code is automatically approved as a country or additive leaf. Shared reviewed plan ID: `5ffb6842559df8b89c6149ab54bc7cfc0d14b4e59a93acb3f2bbcf9dffd1e305`.

```text
imports source    2919f984337dd3eb32d73fdea98795b1f40b82545094d206355a764897f364a8
imports scan      fe01fea0fbafb02770d00e62bc69e67bad177f2a607330ba3b16a57743847f2a
imports receipt   4f7d8bce7e0f1a8553bf3527835365a713de0631753ff3ea054d3013ea10808f
imports inventory 0409c8c596e5cc68a0c7721ff0c290fd926e0426eb1c351b81cef436a8f2fa9c
exports source    65f44acedfc7191ade9b0dd4769afb01f1b0714b2c089d1b2ef33813424d2417
exports scan      2e0dcca537fd99a82198e911fa46adf5cc3b1a14e202008f8fbab5c912046c31
exports receipt   fcbf818cd63f4fe6063a94c15a414156217bf5a6e9d252d972f0f75ece672f0f
exports inventory e6bd356d24f4bb42706249187c97f0e57196d454a202fe78babdb9f89926924e
```

| Role | Artifact ID | ZIP bytes | Expires (UTC) |
|---|---|---|---|
| Imports fresh | `11244250426` | 8,432 | 2026-10-09 17:53:07 |
| Imports recovery | `11243342495` | 8,432 | 2026-10-09 17:56:04 |
| Exports fresh | `11243691737` | 7,679 | 2026-10-09 17:53:30 |
| Exports recovery | `11242947918` | 7,679 | 2026-10-09 17:56:31 |

Verified archive SHA-256 values:

```text
imports fresh    e87c634e4fa44867cf73656409b2138e52f056a86cb7ab9e0cb7f8b08a925828
imports recovery 81f70cced8e036571d0d4d2ae7ce0a6e18597a1283ec3033bfc21b4edc74d385
exports fresh    359c593e6737b17038ced33cc1d40cc07946f441408a9a07b7dd0667a5ebe4f5
exports recovery 30dc9cd9f45382add049b3ce4440e846779f27f9dc28022b11800ef24792e622
```

Private copies are `.local/partner-evidence/{runId}/`, with sanitized `.local/partner-evidence/verification.json`. The inspector did **not read or possess the Census key**; its reflection checks ran in protected workflows. The local inspector checked its in-memory GitHub credential against raw and decoded evidence. Seven-day artifacts and these local copies are not independent durable backups. Live induced failures/refreshes were not exercised; regression tests cover their storage/recovery boundaries. API revision vintage, official revision date, period-effective additive inventory, full-world reconciliation, classification comparability and validated public projection remain unverified. The website remains synthetic/noindex, production-blocked and unhosted; AWS and commercial integrations stay deferred.

Completed documentation review: [receipt PR #16](https://github.com/Vasuki8/us-trade-explorer/pull/16), reviewed immutable head `efe5ad162e7549284ee5b63d70c9fc794a7c2a6d` against runtime `ae769e9e530703c5aaf9bddc7783ea53908c8783`, received no critical, important or minor findings. The reviewer independently matched every copied run/artifact/source/scan/receipt/inventory identity, count, role, generation, size, digest and expiry to the sanitized private verification record; unchanged runtime scope and historical task states were explicitly preserved. All 49 relative documentation links and whitespace checks passed.

The receipt branch `docs/census-partner-live` records these completed tasks from runtime baseline PR #15. Require final-head CI before its standing-authorized integration. Repository/PR history records its documentation-only final head, checks and merge without changing or recursively replacing that runtime evidence.

## Active increment — explicit public release boundary

Branch `feat/public-release-boundary` starts from clean main `88ef717f1a72298d2e93139d453583e0b5fede34` (merged receipt PR #16; main Checks `37045425661` passed). The existing isolated linked worktree is reused. The [plan](superpowers/plans/2026-10-02-public-release-boundary.md) implements the approved public-projection gate with a sample-only allowlist DTO, independent frozen copies, deterministic UTF-8 bytes, a pinned public manifest, bounded checksum/schema loader and metadata download. It does not add an ingestion protocol or official selection switch; the website remains pinned to synthetic data. Future official approval/coverage/classification contracts, hosting and AWS stay gated.

Completed coverage/evidence review on 2 October 2026: two independent read-only analyses and primary offline revalidation of fresh imports `37043703299` and exports `37043711698` confirmed exact observed numeric-row sums equal each returned world control. The primary command blocked socket creation; no Census key or local GCM credential was read, and no source amounts were printed. Numeric inventories overlap at **95**, union **163**, with **42 imports-only** and **26 exports-only**; both explicit zeros and positive observations occur in the one-flow-only sets. Missing rows remain unobserved. This exploratory arithmetic does not establish period-effective additive coverage, API vintage or full-world reconciliation; every approval flag remains false. Current Schedule C and catalog modification dates do not supply the missing historical inventory/vintage evidence. The dated coverage guide will retain official references and approval requirements. Public boundary implementation/tests are in progress; no new completion/merge/production claim is made.

Completed download-test setup: the added browser journey failed against the unchanged sample build because the metadata download link did not exist, after sample disclosures passed. It will independently hash the actual HTTP JSON response and compare its count, scope, coverage and sample provenance with the sidecar. Integration and GREEN verification remain next; the RED test does not claim the endpoint is implemented.

Completed Task 1: `packages/contracts/public-release.ts` constructs explicit public fields, freezes independent DTO/manifest copies and accepts sample/synthetic only. The loader validates metadata before requesting bounded bytes, snapshots callback buffers, checks SHA-256/count, rejects malformed UTF-8/noncanonical JSON and binds coverage/provenance to the body. Twenty-two focused tests were observed failing before implementation, then passed after implementation; primary re-execution passed **22/22** and strict targeted TypeScript. Primary integration verification passed all **31 Node tests**, Astro with zero errors/warnings/hints and the root sample build. The committed producer-generated manifest pins **136,422 bytes** and SHA-256 `9758d0cc72f3d2523bf3704e548ee2adaf66e78407213dc8d9272ed8179a750f`. No private schema or approval boolean selects official data. Task 2 integration is under verification; review/CI/merge remain pending.

Completed Task 2: Astro loads only the fixed sample through its pinned manifest. The existing JSON endpoint serves immutable canonical text and CSV uses the same frozen release; `/data/sample-2026-07-v1.manifest.json` and its release-page download link expose public sample metadata. Build verification binds actual generated JSON to that sidecar and the reviewed pin. Primary checks passed **31 Node tests**, clean Astro diagnostics, both root/project-path builds and **18 desktop/mobile tests at each path**. The new actual-HTTP checksum journey is GREEN at both paths after its observed RED. Four temporary output-tampering checks rejected body corruption, a private DTO field, official metadata and scope drift; exact original bytes were restored and output verification passed. Production was deliberately rejected with `Production publication is disabled`. Thirty HTML pages/noindex/empty sitemap/internal links and the 4,441-byte compressed JS budget are preserved. No ingestion credentials, official selector, provider or backend was added. Documentation validation and immutable review/CI/integration remain next.

Completed Task 3 documentation: the [coverage review](census-coverage-review.md) records dated official references and explicit unresolved additive-inventory/vintage/classification decisions without private amounts. The [public boundary guide](public-release-boundary.md) documents exact APIs/limits, download metadata, safe failure and separately gated official production. Its Node producer/regeneration command was run; adding the repository formatter removed formatting-only drift and reproduced the committed manifest with no Git diff. All **60 relative documentation links** and whitespace checks passed. README/status/current application/next gates now distinguish the implemented sample boundary from future official publication. Immutable whole-branch review and final-head CI/merge/main verification are still pending.
