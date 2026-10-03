# Repository visibility and private evidence

Verified **2 October 2026 local / 3 October UTC** through the GitHub connector and a separate unauthenticated GitHub REST request: `Vasuki8/us-trade-explorer` is **public** (`private=false`). This supersedes the handoff's old private-repository assumption. The agent did not change visibility. Owner intent is unresolved; an asynchronous question is pending. No visibility change, historical artifact deletion or new storage service is authorized by the engineering safeguard.

## Enforced workflow boundary

The five Census acquisition/discovery/control workflows now require all three conditions at job dispatch:

1. `github.ref` is `refs/heads/main`.
2. `github.event_name` is `workflow_dispatch`.
3. `toJSON(github.event.repository.private)` is the string `true`, which requires a boolean true in trusted event metadata.

GitHub evaluates [job conditions before sending the job to a runner](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts). Public/unknown visibility skips the entire job, including checkout, protected-environment credentials, requests, restoration and artifact upload. A skipped job is **blocked acquisition**, not evidence of successful ingestion. Existing protected environment, read permissions, timeouts and full-SHA Action pins remain. The tests parse real YAML and cover every private job's visibility, branches/events and secret/output boundary; they evaluate a deliberately limited reviewed expression subset, not a general GitHub runner emulator.

This is an initial dispatch boundary. It cannot undo previously uploaded artifacts, prove who accessed them or protect a private run if an administrator makes the repository public while it executes or while its artifact is retained. Before any future visibility change, stop private jobs and settle the evidence/storage/access plan. A public source repository requires separate access-controlled storage/execution for private evidence; no such service is configured here.

## Existing evidence and visibility limits

[GitHub artifact downloads](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts) require a signed-in account with repository read access. A public repository therefore cannot promise that its artifact is private merely because its filename or workflow says private. The previously recorded Census artifacts remain unexpired; for example, discovery artifact `11244250426` from run `37043703299` expires **9 October 2026 at 17:53:07 UTC**, as freshly confirmed by artifact metadata. No private artifact was downloaded or newly produced in this increment. Previously verified local copies/recovery records remain ignored and preserved; they are not an independent durable backup. This is not an exposure/access audit or a claim that a key was leaked; existing outputs were already checked for secrets.

Public `Checks` and development preview contain the pinned synthetic data only and remain credential-free. The preview artifact label now accurately says sample-only rather than private. Repository visibility, artifact access, indexing and website production acceptance are distinct: noindex does not restrict artifact access.

Current Pages metadata returns HTTP 200 with `build_type=legacy`, `status=errored` and HTTPS enforced. The configured [site URL](https://vasuki8.github.io/us-trade-explorer/) returns HTTP 404. `ENABLE_GITHUB_PAGES_PREVIEW` is absent (HTTP 404), so the reviewed Astro workflow does not deploy. The old private-plan HTTP 422 limitation is historical; current evidence is the public repository's incompatible legacy Jekyll configuration. No Pages setting, preview variable or host was changed by this task.

## Follow-up before ingestion or hosting

Resolve the owner's visibility intent. If private development is restored with authorization, verify actual visibility/protected-environment access before acquisition. If source remains public, design an approved private evidence store/runner and revisit backup, retention and access before acquiring new private candidates. Preserve local evidence; do not delete remote history reflexively.

The source-research advance remains in the [July coverage review](census-coverage-review.md): equal July annex text does not resolve its territory note, and documented API annual revisions do not certify the generation of archived response bytes. All classification, partner inventory, vintage and publication gates remain unchanged. The [Census clarification draft](census-clarification-draft.md) is unsent; contacting Census needs owner authorization.

Dependency audit during the test-parser pin reported the already locked `http-cache-semantics` issue [GHSA-ch52-4w7c-c8xp](https://github.com/advisories/GHSA-ch52-4w7c-c8xp), plus the same advisory propagated to Astro (two high package entries, one underlying advisory). The advisory currently lists no patched version. No forced Astro downgrade was attempted. Local code inspection finds that dependency in Astro's remote-image build cache; this site uses static output and no `astro:assets` remote images or user sessions. No reachable cross-user shared-response cache was demonstrated; this is a bounded applicability observation, not a vulnerability dismissal or full scan. Reassess before remote-image/SSR/authenticated-cache features or hosting activation.

Actual tests, immutable review, final-head/main CI and live skipped-job evidence belong in the [handoff](handoff.md) and PR history. This document does not itself certify those outcomes.
