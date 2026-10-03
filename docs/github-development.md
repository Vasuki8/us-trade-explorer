# GitHub development first

**Actual-state update, 2 October local / 3 October UTC:** GitHub independently confirms a public repository; the agent did not change visibility. [Private-evidence safeguards](private-evidence-visibility.md) now require manual private-main context for all five Census workflows. Existing artifacts cannot be promised private in a public repository. Pages API currently reports HTTP 200, legacy/errored configuration, and the configured site returns HTTP 404; the Astro deployment-enable variable is absent. The old private-plan HTTP 422 result below is historical, not the current hosting limitation. No host setting changed. Current owner visibility intent/private evidence path remains unresolved.

Current owner direction, **2 October 2026**: keep development in private GitHub, prioritize validated official data and prefer future Cloudflare Workers + Static Assets/R2, with optional D1 only for smaller metadata. This supersedes the **1 October AWS-after-development preference**. The existing UI remains approved; no provider/account, spending or commercial deployment is activated. See [permanent instructions](../AGENTS.md) and the [operating-model decision](decisions/2026-10-02-operating-model.md).

GitHub remains the source of truth for code, CI, reviewed changes, source contracts and small manifests. Actions handles testing, sample builds and private Census candidate artifacts. Large historical data and credentials stay out of Git history.

## Development preview

The `GitHub development preview` workflow builds from `main`, checks the public contract and generated pages, and retains a downloadable build for 14 days. It does not read the Census secret. GitHub Pages deployment runs only when the repository variable `ENABLE_GITHUB_PAGES_PREVIEW` is explicitly `true`, Pages is configured for Actions and the `github-pages` environment permits `main`.

Current provider result: the Pages setup API returned HTTP 422, “Your current plan does not support GitHub Pages for this repository.” No Pages site was created and no plan or repository visibility was changed. Development continues with local previews and private Actions artifacts. The Pages deployment variable remains unset.

The intended project URL is `https://vasuki8.github.io/us-trade-explorer/`; it is not a confirmed live URL until deployment and HTTP checks succeed. The origin and `/us-trade-explorer/` path use the portable build; a future approved host must verify the same URL/HTTP contract. A downloadable artifact uses this same path: serve its extracted files under `/us-trade-explorer/` when viewing locally.

The preview stays clearly labelled, synthetic and noindex. It has no advertising, sign-up, checkout, payment collection, analytics scripts or paid features. GitHub's terms prohibit using Pages as free hosting to run an online business or commercial SaaS. This is a development demonstration of the project; migrate hosting before operating the commercial service. Reassess terms if the preview's purpose changes. [Pages limits and terms](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

Pages for a private repository requires an eligible paid GitHub plan. Keep the repository private. Do not buy a plan or publish source code to work around an eligibility limitation without the user's choice. Private Actions artifacts are the fallback. A private source repository does not necessarily make its Pages website private. [Pages availability](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

## Hosting limitations and privacy

The previously researched GitHub Pages candidate lacks the configurable response-header and log-export controls required by the production design. The build uses a meta CSP as a browser safeguard; meta CSP cannot enforce `frame-ancestors`, HSTS or Permissions-Policy. Verify those controls against actual responses/configuration on the eventual approved host, including Workers/static/error/download behavior if Cloudflare is selected. Generated static 404 behavior and project-path links need live deployment checks. Provider capability/legal research is dated and must be refreshed before changed use.

GitHub says Pages logs visitors' IP addresses for security, including signed-out visitors. Hosting therefore still processes personal/network information; no promise of zero data collection is made. Do not invent retention periods, India log residency or deletion control over GitHub's provider logs. The preview privacy page identifies this provider behavior. [GitHub Pages data collection](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection)

## Official data work

The existing `CENSUS_API_KEY` repository secret is used only by isolated ingestion. Configure the `census-ingestion` environment for the trusted `main` branch before the first dispatch. Fetch and inspect one monthly candidate first; validate source dimensions, suppression markers, publication dates and reconciliation before introducing live figures into the site. Nothing in the Pages workflow can promote a Census candidate or turn the sample into an official release.

The environment was created and the API confirmed its only selected deployment branch is `main`. Required human environment reviewers and main-branch protection have not been verified. Limit repository write access to trusted administrators; workflow code reviews remain necessary while the key is a repository secret. The initial imports candidate was dispatched from the reviewed, merged PR #1 commit for July 2026; its result must be inspected separately from website validation.

Initial acquisition result: [run 36957552437](https://github.com/Vasuki8/us-trade-explorer/actions/runs/36957552437) failed after three bounded source attempts and skipped artifact upload. The sanitized error did not distinguish transport failure, timeout or a retryable HTTP response, so the precise cause and API-key acceptance remain unverified. No candidate or official public data was produced. Do not weaken validation or substitute invented official figures; next ingestion work should add safe error categories and test a smaller documented source partition if needed.

## Verification of this increment

The new browser regression failed before the CSP was added, then passed with the meta policy. Nine contract tests, thirteen ingestion/store tests, the Astro type check and all sixteen desktop/mobile browser journeys passed locally. All sixteen browser journeys also passed under `/us-trade-explorer/`, including search, filtering, safe CSV download and a real local HTTP 404. Both builds verified 30 HTML pages and their internal links. This proves local behavior, not enforcement on a deployed GitHub Pages site.

## Future authorized hosting transition

After official-data prerequisites and business launch gates pass, evaluate the same static output on Workers + Static Assets and larger objects on R2; optional D1 is for smaller metadata, not the complete analytical fact table. Recheck actual plans/terms, source reuse, credentials, processing locations, logs/retention, headers, route/404 behavior, cost and independent backup/rollback. Provision only after required authorization; no migration code is implemented here. Replace temporary notices with verified practices and enable indexing only for substantive official pages after acceptance. Basic local saved research does not require accounts. Later cloud/paid workspaces require the server-side authorization and subscription boundary before launch; AWS remains a historical alternative.
