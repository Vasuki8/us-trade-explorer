# Private partner coverage diagnostics

Updated **2 October 2026**. This guide specifies the bounded offline review increment for the existing July 2026 / HS2 chapter 09 discovery evidence. Actual runtime, test, independent-review, CI and integration results belong in the dated [handoff receipts](handoff.md) and [implementation status](implementation-status.md); this guide is not a passing receipt.

The [dated coverage review](census-coverage-review.md) identifies the unresolved period-effective inventory, territory/special-bucket, classification and revision-vintage evidence. This increment helps an operator examine inclusion/exclusion scenarios without approving those gates. The [discovery guide](census-partners.md) retains acquisition, storage and recovery instructions; diagnostics add no acquisition, journal, restore or transport protocol.

## Verified inputs and APIs

The fixed plan is `sources/scans/coffee-partners-2026-07.json`: US reporter, `2026-07`, HS2 `09`, DET, monthly nominal USD, not seasonally adjusted. Imports retain general-import customs value `GEN_VAL_MO`; exports retain total domestic-plus-foreign FAS value `ALL_VAL_MO` and their reviewed aggregate dimensions.

| API | Purpose |
|---|---|
| `partners.read_partner_snapshot(plan, flow, root, secrets=())` | Load bounded safe files once, revalidate all raw/scan/receipt relationships and require the active receipt to match the current successful generation; return validated state |
| `partners.verify_partner_scan(plan, flow, root, secrets=())` | Preserve the existing receipt-only verification interface through the same reader |
| `partner_review.make_review(plan, flow, files, secrets=())` | Validate a complete in-memory snapshot and generate an all-unresolved worksheet |
| `partner_review.build_diagnostics(plan, flow, files, review=None, secrets=())` | Validate the snapshot and optional worksheet, then recompute a deterministic private report |

The CLI uses one validated snapshot read. It does not verify a receipt and later reread unchecked observations. Failed or pending refresh state cannot silently select an earlier complete pointer. Hashes bind preserved bytes and relationships; they do not prove Census authenticity or official revision vintage.

## Worksheet and scenario decisions

The report's `review` field is the editable worksheet. Extract that field into its own private JSON file, retain its `scope` and `inputs`, edit its decisions, and pass the file with `--review`. A copied report is not a worksheet.

The worksheet has exactly `schemaVersion=1`, `state=draft-partner-review`, `decisionAuthority=operator-scenario-only`, `scope`, `inputs` and `decisions`. Scope binds `planId`, `basis`, `flow`, `period`, `product` and `summaryLevel`. Inputs bind `scanId`, `receiptId`, `sourceHash` and `objectHash` to the active verified evidence. A worksheet from another flow or changed source/receipt fails validation.

Every observed numeric detail code needs exactly one decision with `code`, `disposition`, `rationale` and `references`. Decisions are sorted in validated output. Missing, duplicate, extra and unobserved codes fail; world `-` is excluded from decisions. Worksheet names, amounts, approval flags and extra fields are rejected. Default decisions are `unresolved`, with `rationale=null` and `references=[]`.

An `include` or `exclude` scenario requires nonblank rationale of at most **250 characters**, without C0 or DEL controls, and **1–10 unique reference IDs**. IDs match `[a-z0-9][a-z0-9._-]{0,79}`. They are operator source labels, not URLs, paths, retrieved documents or historical approval. An unresolved decision may retain the null/empty defaults or use the same bounded rationale/reference pair. No disposition approves a geographic leaf.

The worksheet has no self-hash to update manually. The report computes `reviewId` from its validated canonical worksheet and `reportId` from the other report fields. Editing bound identities to match new evidence does not supply the missing inventory/vintage/classification review.

## Exact diagnostics and missing observations

The report retains observed numeric code/name/status/value and the scenario disposition, with world reported separately as `{status,value}`. `totals` contains exact decimal strings for `observedUSD`, `includedUSD`, `excludedUSD` and `unresolvedUSD`; corresponding counts describe observed rows in each category. World is excluded from these sums.

`residuals.observedMinusWorldUSD` is **observed numeric-detail total minus world**. `residuals.includedMinusWorldUSD` is **scenario-included total minus world**. Both are signed decimal strings calculated with Python integers, including values above JavaScript's exact-integer range. Positive, negative and zero residuals are diagnostics, not reconciliation approval.

An absent world is `status=unobserved`, `value=null`; both residuals are null and an explicit missing-world blocker is retained. A returned zero remains `reported_zero` with value `"0"`. An empty category has mathematical total `"0"` and count zero; it is not a source zero observation. No absent partner is invented or converted to zero, including a code seen only in the other flow.

Every report keeps `coverage=observed-partners-only`, `leafInventoryApproved=false`, `apiVintageVerified=false`, `fullWorldReconciliation=not-verified` and `publicationReady=false`. These remain unchanged when residuals are zero or all decisions are classified. Official release/revision dates and revision-detection time remain null; ingestion time remains the verified scan timestamp. Inventory, vintage, classification and reconciliation blockers persist.

## Windows offline commands

Run from the repository root with Python 3.14. These commands use the preserved fresh imports/export snapshots documented in the handoff and print counts plus the publication-blocked state, without amounts, names, rationale or source payloads:

```powershell
py -3.14 -m pipeline.partner_review --plan sources/scans/coffee-partners-2026-07.json --flow imports --snapshot .local/partner-evidence/37043703299 --output .local/partner-review/imports.json
py -3.14 -m pipeline.partner_review --plan sources/scans/coffee-partners-2026-07.json --flow exports --snapshot .local/partner-evidence/37043711698 --output .local/partner-review/exports.json
```

Extract the generated all-unresolved worksheets without printing their contents:

```powershell
@'
from pathlib import Path
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, decode

root = Path(".local/partner-review")
for flow in ("imports", "exports"):
    report = decode((root / (flow + ".json")).read_bytes(), maximum=512 * 1024)
    atomic_write(root / (flow + "-worksheet.json"), canonical(report["review"]))
print("2 private worksheets extracted.")
'@ | py -3.14 -
```

Edit only each worksheet's decision dispositions/rationale/reference labels in a local editor. Recompute an import scenario into a separate private report:

```powershell
py -3.14 -m pipeline.partner_review --plan sources/scans/coffee-partners-2026-07.json --flow imports --snapshot .local/partner-evidence/37043703299 --review .local/partner-review/imports-worksheet.json --output .local/partner-review/imports-scenario.json
```

For exports, use `--flow exports`, snapshot `37043711698` and the export worksheet/output paths. The CLI reads no credential environment variable, requires no key or token, and performs no network request. It accepts the fixed plan and local files only. Known-secret checks remain available to API callers that explicitly supply `secrets`.

## Private output, failure and recovery

Output must be a `.json` file beneath this repository's ignored `.local/`, resolved from the module location independently of the caller's working directory. Output inside the input snapshot or equal to the plan/worksheet input is rejected. Symlink/junction files and ancestors are rejected for plan, worksheet, snapshot and output paths. Raw responses, scans, receipts and acquisition state are never output targets.

Inputs retain existing **500-row / 2 MiB snapshot** bounds. Worksheet JSON is capped at **256 KiB** and report JSON at **512 KiB**. Strict decoding rejects duplicate keys, nonfinite numbers and unexpected fields; limits reject rather than truncate. Output parents are created only after evidence/worksheet validation, and the bounded result uses atomic replacement. Validation or write failure preserves an existing report; no cleanup, public pointer or new journal follows.

Failures expose fixed diagnostics without echoing bad arguments, paths, URLs, notes, amounts or upstream payloads. Preserve the worksheet and snapshot for diagnosis. For stale/corrupt discovery evidence, follow the existing discovery recovery guide and deliberately select a verified successful snapshot. Never repair immutable evidence or adjust identities to hide a mismatch.

Keep report amounts, codes, names, worksheets, notes and source payloads out of Git and public artifacts. The [public release boundary](public-release-boundary.md) continues to select only its pinned synthetic sample; a diagnostic report, residual or approval field cannot activate official data. AWS, hosting, providers, spending, durable backups and commercial launch retain their existing gates.

Use the handoff for exact verification commands/results, immutable review, final-head CI, merge and merged-main receipts. A generated report proves only the validations and scenario arithmetic described here; neither this guide nor a CLI success closes the dated publication gates.
