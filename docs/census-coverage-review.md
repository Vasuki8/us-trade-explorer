# July 2026 Census coverage review

Research and offline review dated **2 October 2026**. This records the bounded July 2026 / HS2 chapter 09 discovery evidence and unresolved publication gates. It approves no additive partner inventory and does not feed the public sample. Exact source/scan/receipt identities and acquisition/recovery receipts are in the [handoff](handoff.md) and [discovery guide](census-partners.md).

## Completed offline observations

The read-only audit used the independently verified fresh import/export snapshots. It retained the reviewed US reporter, month/chapter, DET summary and aggregate dimensions: general-import customs value `GEN_VAL_MO`; total domestic-plus-foreign export FAS value `ALL_VAL_MO`; monthly nominal USD, not seasonally adjusted.

| Observation | Imports | Exports |
|---|---|---|
| Returned rows | 138 | 122 |
| World controls (`-`) | 1 | 1 |
| Unreviewed numeric detail rows | 137 | 121 |
| Explicit reported-zero rows | 25 | 31 |
| Numeric codes observed only in this flow | 42 | 26 |
| Of those flow-only codes: positive / zero | 27 / 15 | 18 / 8 |

There are **95 common numeric codes and 163 in the union**. A code absent from the other flow remains unobserved there; this review creates no zero row. Independently summing all observed numeric values as exact integers equals the world value within each response. No private amounts or code payloads are published here.

That arithmetic equality does not establish mutually exclusive geographic leaves, all possible July members, matched official revision vintage or approved full-world reconciliation. World remains a separate control and numeric rows remain `unreviewed-detail`. Coverage remains `observed-partners-only`; `leafInventoryApproved`, `apiVintageVerified` and `publicationReady` remain false. Discovery official release/revision dates remain null. The separate [FT900 announcement proof](census-controls.md) supports its initial announcement date only.

## Official sources and supported rules

The following current Census resources were checked on **2 October 2026**. Undated resources are labelled as such; a retrieval date does not establish July-effective membership.

| Source | Supported rule and limit |
|---|---|
| [Statistical-program guide](https://www.census.gov/foreign-trade/guide/sec2.html), §§3 and 16; undated current page | Foreign-country trade covers the US customs territory, foreign-trade zones and US Virgin Islands. US/possessions shipments are separately published. PR/USVI foreign-country trade is included in US totals. Review territory transaction meaning before deciding additive inclusion. |
| Same guide, §10 | `UNIDENT` and commodity-dependent `OTH CTY` illustrate special statistical designations and aggregates. A familiar name or numeric code cannot prove non-overlap. |
| Same guide, §14 | Export low-value estimates use `9880.00.4000`; import estimates use `9999.95.0000`. Eligible imports can roll into detailed commodities. Chapter 09 excludes those separate special chapters, but cannot be described as excluding all low-value trade. |
| [International Trade API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf), pp.10, 15, 17 and 27; undated current PDF | Valid requests may return no data/HTTP 204. DET identifies individual partners but includes world `-`; CGP groups include numeric `0001`/`0003`. Explicit zero and absent rows are different observations. Code syntax is not inventory approval. |
| [2026 Schedule B index](https://www.census.gov/foreign-trade/schedules/b/2026/index.html) and [chapter 09](https://www.census.gov/foreign-trade/schedules/b/2026/c09.pdf), pp.1 and 3 | Index codes apply after **1 July 2026**. Chapter 09 is Coffee, Tea, Maté and Spices. This dated export classification does not establish an import classification or cross-period concordance. |
| [Current Schedule C HTML](https://www.census.gov/foreign-trade/schedules/c/countrycodes.html) and [TXT](https://www.census.gov/foreign-trade/schedules/c/country.txt) | Reporting aids lack July 2026 effective-date proof. TXT retains a **31JAN14** production header and includes Western Sahara `7370`, which HTML omits. Current names/membership cannot alone approve historical coverage. |
| [Import variables](https://api.census.gov/data/timeseries/intltrade/imports/hs/variables.html) and [export variables](https://api.census.gov/data/timeseries/intltrade/exports/hs/variables.html) | `LAST_UPDATE` is labelled a 10-character update date, without documented semantics proving statistical revision vintage. Capturing it would preserve a source label, not supply approval. |
| [Import catalog](https://api.census.gov/data/timeseries/intltrade/imports/hs.json) and [export catalog](https://api.census.gov/data/timeseries/intltrade/exports/hs.json) | Both show catalog `modified: 2017-05-02`; that is not a July 2026 observation vintage. |
| [Developer page](https://www.census.gov/data/developers/data-sets/international-trade.html), dated **7 April 2026** | Describes monthly release-day updates and annual revisions with April statistics. It does not identify the revision generation of preserved July response bytes. |

## Dated classification and country-annex follow-up

The [classification evidence record](classification-evidence.md) now binds five captured official import editions, including July 2026 Revisions 11–14 and July 2025 Revision 16, to exact source hashes and retrieval timestamps. Offline extraction preserves unnamed hierarchy rows, six-digit intermediates and standalone detail roots. Chapter 09 row structure/descriptions/units agree in those snapshots, but **57 footnote entries change** in Revisions 13–14. Historical notes, effective intervals, export-byte capture and API normalization remain unresolved; no comparability gate is closed by equal projections.

The captured [Revision 11 Statistical Annexes](https://hts.usitc.gov/reststop/file?release=2026HTSRev11&filename=Statistical%20Annexes), PDF pp.2–9 (A-2–A-9), provides a dated **candidate** Schedule C reference. Every inspected footer agrees with Revision 11 (2026); A-2 says Schedule C applies to both exports and imports and that changes are issued through special notices/Public Bulletins. Its numeric table provisionally yields **240 distinct printed designations**, not 240 approved additive leaves. Western Sahara is absent, but the deletion date or reassignment is not established. Indonesia's inclusion note still names former Portuguese Timor while Timor-Leste is listed separately. Retain this conflict; do not infer non-overlap or interpret territorial history on our own. US code 1000, possessions, unidentified/other statistical buckets and dataset-specific DET world treatment require separate review. The [source identity record](../sources/hts-evidence-2026-07.json) includes the annex's exact captured bytes/hash; this does not approve every July API bucket or effective interval. Current TXT/HTML discrepancy above remains a dated research observation.

The current [Census revisions guide](https://www.census.gov/foreign-trade/guide/revisions.html), labelled last revised **10 September 2026**, distinguishes monthly aggregate/end-use revision treatment from detail-level annual revisions and Canadian corrections. The [data page](https://www.census.gov/foreign-trade/data/index.html) explicitly says prior FT900 releases remain frozen while current historical data may be revised. Those practices and the API guide's release-day update rule do not identify the generation of our exact archived response bytes. `LAST_UPDATE` is still only a documented update-date label. Preserve initial-release, revision and retrieval concepts separately; neither the unchanged catalog date nor a frozen announcement PDF certifies the API vintage.

Next: capture/compare later July country annexes and applicable notices, review territory/special-bucket wording against each flow's private worksheet, and locate a dataset-specific official vintage/revision basis. Prepare a concrete clarification request only if those documents leave a material gap; external communication requires owner authorization. This task sent no such message. Inventory, vintage and publication approval remain false.

## Evidence required before official publication

1. **Period-effective inventory:** review every included/excluded/unresolved code per flow, period and commodity scope. Retain official effective-date documentation or Census clarification covering membership, territories, special statistical buckets and non-overlapping treatment. The July response establishes observed membership only; current Schedule C does not establish all possible members.
2. **Classification contract:** approve the relevant import/export editions, chapter definitions and changes for each period. A future contract must express territory/special-area roles and classification comparability; the public version-1 HS2022 synthetic label cannot carry these decisions. Generalize products/periods only after evidence-backed review.
3. **Compatible vintage and dimensions:** bind approved source generations and official release/revision evidence to exact archived responses. The same response provides a common capture for its world/detail arithmetic, but not official revision proof. A matched month, unchanged code, retrieval time or `LAST_UPDATE` label alone is insufficient.
4. **Exact approved reconciliation:** sum only approved non-overlapping members under compatible flow/value/aggregate dimensions and compare with the corresponding world control. Require exact integer-dollar equality with documented inclusion rules; unresolved rows, missing controls or unsupported value markers block approval. Do not fabricate a residual partner or convert absence to zero.
5. **Separate official producer and public boundary:** review a future versioned manifest/producer that binds inventory, classification, provenance and validation receipts to a public-only projection. Preserve unknown dates and explicit missing statuses; scope selected chapters accurately. Neither a valid checksum nor an approval boolean activates official data.

The [private coverage diagnostic](partner-coverage-diagnostics.md) now implements the evidence-bound worksheet and exact signed residual calculation, defaulting every observed numeric code to unresolved. Runtime verification, review and integration receipts remain in the [handoff](handoff.md). The next statistical decision is the documented period-effective inclusion/exclusion and vintage review described above; operator scenario labels and arithmetic cannot close those gates. No new transport/journal protocol or public toggle follows from this record. See the [public boundary guide](public-release-boundary.md), [approved plan](superpowers/plans/2026-10-02-public-release-boundary.md) and [current implementation status](implementation-status.md) for their separate roles and receipts.
