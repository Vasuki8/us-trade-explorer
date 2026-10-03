# Single-period chapter research

`pipeline.research` assembles a private July 2026 / HS2 chapter **09 — Coffee, tea, maté and spices** research slice. It combines the existing [selected-country report](selected-partners.md) with exact, reviewed import or export classification references and explicit limits on supported analysis. It does not publish data, change previous report formats, fetch statistics, or enable the public sample to accept official/private artifacts.

## Reviewed scope and source decision

The [document registry](../sources/chapter09-evidence-2026-07.json) records six exact source identities, their URLs, retrieval times, byte sizes, hashes and roles. Source files remain ignored under `.local/chapter-scope/` and `.local/official-evidence/`; only metadata is committed. Five documents were captured over HTTPS on **3 October 2026**, with a fixed allowlist, no redirects, a 25-second timeout and bounded response sizes. The earlier Revision 11 chapter PDF is retained with its original receipt. No API key or private ingestion workflow was used. These local files are not an independent durable backup.

For imports, the reviewed references are [2026 HTS Revision 11](https://hts.usitc.gov/reststop/file?release=2026HTSRev11&filename=Chapter%209) and corresponding Revisions 12–14. They explicitly identify chapter 09 and its notes. Revisions 11–12 have eight PDF pages; Revisions 13–14 have seven. Extracted first-page chapter/statistical-note text agrees across all four after replacing only the edition number and normalizing whitespace. This does **not** mean the complete documents are equal: the earlier [JSON comparison](classification-evidence.md) found 57 detailed-row footnote differences. Revision 14's first page was also visually inspected, including its footnote identifying an expired legal provision. Source legal notes are not converted into current customs/legal advice.

For exports, the captured [2026 Schedule B index](https://www.census.gov/foreign-trade/schedules/b/2026/index.html) labels use after **1 July 2026** and links the captured [chapter 09 PDF](https://www.census.gov/foreign-trade/schedules/b/2026/c09.pdf). The PDF has four pages: chapter/statistical notes on pages 1–2 and the table on pages 3–4. The notes and first table page were visually inspected. The table contains 43 ten-digit export rows, whereas the earlier import JSON inspection found 91 import detail rows. For example, export unroasted non-decaffeinated coffee has one `0901.11.0000` row; imports subdivide that group. Shared chapter labels cannot justify joining the two ten-digit dictionaries. Capture of the exact export bytes resolves the previously recorded download limitation.

**Narrow decision:** use these references to identify chapter 09 in the already captured monthly observations, while preserving each flow's existing Census statistical basis. This permits selected-country values and same-response world shares for that one month. The Census response supplies the chapter total directly; this implementation does not sum overlapping subheadings or reinterpret individual commodity classifications. The reference documents do not identify the exact classification revision applied within the retained API response. An index's use-after label is recorded as such, not invented as a provision-effective interval, observation revision date, or certification that the API normalized historical values to that edition.

Import general/customs values and total-export/FAS values remain separate in the nested provenance record. Reporting month, first retrieval, current archive attempt, unknown API release/revision/generation and null publication time retain their existing meanings. No shared fine-code dictionary, historical concordance, certified organic assessment, tariff calculation or chapter-wide quantity aggregation is introduced.

## Implemented contract

- `build_slice(plan, flow, files, annexes, documents)` validates the complete active source archive, rebuilds the selected-country report and checks every required chapter reference against its reviewed size/hash. It accepts only the existing July 2026 / chapter 09 / DET scope, with exact per-flow document membership.
- The slice retains the original selected report unchanged under `selectedTrade`. Missing, reported zero, incomplete selected subtotals, absent/zero world controls, exact integer USD and rounded world shares keep their tested behavior. Other partners remain unassessed.
- `classification` provides the reviewed chapter name, separate HTSUS/Schedule B identity, reference documents and date-role limits. `historicalComparability=not-established`, `apiClassificationVintage=not-identified` and `provisionEffectiveFromVerified=null` prevent unsupported certainty.
- `analysisPolicy` limits country values to the selected countries in the same flow and period, and world shares require an observed positive world control. Historical growth, fine-code joins, quantity metrics and global rankings/concentration remain unsupported. This is a consumer contract; future consumers must enforce it when offering calculations. No such unsupported calculation is implemented here.
- `validate_slice(...)` rebuilds the entire slice from its source inputs and compares canonical bytes. Rehashing altered classifications, values, capabilities, flags or boolean/numeric substitutions cannot make them valid. A checksum is not sufficient on its own.
- Publication remains false. The public loader rejects this private state, including a forged approval flag, before loading payload data. Source documents/raw observations/private slices remain outside Git and website artifacts. The sample pin, noindex and production rejection stay unchanged.

The pipeline uses the Python standard library. Bundled PDF tools were used for source review only; no new runtime dependency, paid service, account, provider or workflow was added.

## Local use and recovery

Supply the four pinned Schedule C annexes as `2026HTSRev11.pdf` through `2026HTSRev14.pdf`, as required by the selected-country report. The classification directory contains the filenames in the registry: four `hts-2026-revNN-chapter09.pdf` files for imports, or `schedule-b-2026-index.html` and `schedule-b-2026-chapter09.pdf` for exports.

```powershell
python -m pipeline.research --plan sources/scans/coffee-partners-2026-07.json --flow imports --snapshot .local/partner-evidence/IMPORT_RUN --annex-dir .local/chapter-scope/annexes --classification-dir .local/chapter-scope --output .local/chapter-scope/research/imports.json
```

Exports use their own archive and `--flow exports`. The CLI never retrieves credentials or accesses the network. Reads are bounded, paths reject symlinks/junctions, and output must be a JSON file under this repository's `.local`, outside the archive and distinct from every input. Output is atomic; failed validation or retries leave the previous result intact. Console errors are fixed messages without source values, payloads or request URLs.

Thirteen focused tests were observed failing before implementation and passing afterward. They cover scope and flow separation, source bindings, null date semantics, inherited missing/coverage behavior, altered/rehashed claims, offline execution and safe CLI recovery. Production pins are checked against the registry. The public-loader regression covers this new private state.

Actual offline replay passed for both retained flow snapshots and their recovery copies. Both the pure builder and CLI produced identical results, recovery pairs matched, and all source files remained unchanged. Sockets, credential access and subprocesses were prohibited. Four-country slices are 8,360 bytes for imports and 7,820 bytes for exports; trade values stay local.

## Next step and remaining boundaries

Implement a separate **public-only projection and official-release validation** for these bounded slices, retaining their coverage labels, basis, provenance and analysis restrictions. That work should prepare reviewable public artifacts without switching the sample pin or pretending a complete global/historical dataset exists. New private ingestion still requires the unresolved access-controlled execution/storage decision. Public activation requires the actual source-use, hosting and notice acceptance checks in the [handoff](handoff.md). Full-world concentration and historical/quantity analytics need their own evidence and coverage work; they are not prerequisites for every correctly labelled single-period selected-country fact.
