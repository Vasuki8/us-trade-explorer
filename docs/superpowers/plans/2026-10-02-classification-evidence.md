# Official classification evidence implementation plan

> **For agentic workers:** Use superpowers:executing-plans for this bounded increment, followed by independent whole-branch review. Standing merge authorization is recorded in the handoff.

**Goal:** Make archived import-classification inspection repeatable without losing unnamed hierarchy or confusing textual agreement with historical comparability.

**Architecture:** Add a pure offline HTS JSON reader and comparison helper to the existing Python pipeline. Bind each input to its reviewed SHA-256; retain hierarchy, descriptions, reported units and footnotes. Neither function retrieves data, writes files, approves comparability or publishes observations.

**Tech stack:** Standard-library Python 3.14, existing unittest/CI; no dependency, host, credential or workflow changes.

**Spec:** [Permanent instructions](../../../AGENTS.md), especially sections 7–10, 13–17 and 31; [coverage prerequisites](../../census-coverage-review.md).

## Global constraints

- Existing sample/public contract and production guard remain unchanged.
- Raw editions and private source evidence stay ignored; commit only source identities and research conclusions.
- Imported labels are untrusted text. Retain exact text, bounded types and safe diagnostics; do not render it as HTML or provide customs advice.
- Distinguish publication/archive labels, effective dates, retrieval time and observation vintage. A date conflict remains explicit.
- No inventory, classification, quantity or API-vintage approval follows from matching text, units or arithmetic.

## Review focus

- A blank-code ancestor changes a leaf's meaning despite an unchanged leaf label.
- Rows with the same code but changed units/footnotes need visible differences.
- Duplicate codes/JSON keys, nonfinite numbers, oversized inputs and malformed indentation fail safely.
- Adjacent chapters and noncontiguous chapter fragments must not enter the inspected slice.
- Source-row movements elsewhere in the document must not become false semantic changes; changed order inside the selected chapter remains observable.

## One coherent task: offline extraction, comparison and dated receipts

**Files:** Create `pipeline/classification.py`, `pipeline/tests/test_classification.py`, `sources/hts-evidence-2026-07.json` and `docs/classification-evidence.md`; update coverage review, handoff and implementation status.

**Interfaces:** `extract_hts_chapter(raw: bytes, expected_sha256: str, chapter: str = '09') -> dict`; `compare_hts_chapters(before: bytes, after: bytes, before_sha256: str, after_sha256: str, chapter: str = '09') -> dict`. Both revalidate raw source identities. Results are review-only with comparability/publication false, explicitly import HTS metadata rather than export Schedule B or observations.

- [x] Write meaningful tests for hierarchy/context changes, additions/removals, units, footnotes, ordering and fail-closed inputs; run and observe missing-module RED.
- [x] Implement the reader/comparison. Preserve each scoped row and coded-row ancestry; compare semantic fields, excluding absolute positions in other chapters.
- [x] Run focused tests, then full pipeline suite. Replay on five locally captured official editions without sockets or credential access.
- [x] Record exact artifact identities, July edition/date discrepancies, verified metadata differences and unresolved statistical comparability/partner/vintage gates. Update durable handoff and next task.
- [ ] Review diff, run relevant documentation/build checks, commit and request independent immutable branch review. Fix evidenced findings and pass final-head CI.
- [ ] Merge under standing authorization; inspect merged-main checks/private preview and safely synchronize the primary while retaining the owner's edit. Record final integration receipts in PR history without a recursive documentation PR.
