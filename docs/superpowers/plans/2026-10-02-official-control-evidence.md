# Official control and publication evidence

Implement the next private-data foundation from the approved public MVP design. The website remains synthetic and noindex; AWS and subscriptions remain deferred.

## Scope and decisions

- Preserve the successful eight-partition market plan and its immutable evidence. Add a separate two-partition HS2 09, July 2026 world plan, using Census `CTY_CODE=-` and explicit `SUMMARY_LVL=DET`. The existing eight-request cap remains.
- Pin the reviewed July FT900 announcement PDF and its SHA-256 in Git. Fetch a bounded private copy and verify that copy before attaching its announcement date. The PDF establishes the initial announcement date, not the vintage of current API observations or a revision date. Candidate dates remain null.
- Independently verify both bundles and all referenced objects before calculating exact selected-market amounts and the amount outside that subset. Require the reviewed four-country inventory and matching flow, period, chapter and statistical basis. Never describe a selected-country check as full world reconciliation, even when amounts happen to match.
- Add main-only manual acquisition choices and a separate private report workflow. No ingestion secrets enter PR checks or public builds. Preserve existing recovery behavior and private artifact boundaries.
- Keep raw API archival, complete leaf inventory, classification comparability and exact full reconciliation as explicit publication blockers. These need a later acquisition contract rather than a silent change to the existing immutable artifacts.

## Tasks

1. Add failing world-query and offline-contract tests; implement explicit world support and the separate plan.
2. Add a strict publication statement, bounded fixed-source PDF reader, private archive and tests for dates, checksums, unsafe URLs, limits and reflected secrets. Archive no binary source in Git.
3. Add failing subset-report tests; implement independently verified joins, exact arithmetic, scoped checks, honest blockers and atomic private output. Include recovery/download failure behavior.
4. Update manual workflows and operator documentation; record the already successful market acquisition/recovery receipts.
5. Run Python and web verification, review the entire branch independently, create a PR, check CI, and request specific merge approval only once the result is reviewable.

Implementation uses the existing isolated worktree. Independent publication code may be delegated under the active multi-agent instruction; shared batch/control files stay with the primary implementer. Tests use fabricated values and local HTTP doubles. Live world acquisition is deferred until the main-only workflow has been merged with approval.

## Local implementation receipt

The three world-control tests initially failed because explicit world scope was unsupported. The private-control tests initially failed on the absent report module; the publication implementer likewise recorded absent-module failures. Initial verification passed 94 Python tests and 9 Node tests. Astro checked 33 files with zero errors, warnings or hints, and its verified build produced 30 sample/noindex HTML pages with 4,441 bytes of compressed JavaScript. The official PDF was fetched by the bounded reader, verified against its pinned digest, privately archived and reused without a second fetch.

Independent review found one material recovery issue: the report could select a preserved older bundle after a failed refresh or interrupted pointer write. Two added tests reproduced three failures before correction. The report now requires wholly successful journals whose references match the selected bundles, and records journal identities; batch recovery semantics are unchanged. Final test/CI evidence is recorded in the pull request. Live world and report execution remain a post-merge check.
