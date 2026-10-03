# July chapter 09 classification evidence

Reviewed **2 October 2026 local time**. Public document capture occurred **3 October UTC**, as recorded in the [source identity record](../sources/hts-evidence-2026-07.json). This is import-classification research, not an official-data release or historical/quantity comparability approval. Private trade observations and the public sample are unchanged.

## Captured editions and date roles

The [USITC archive](https://www.usitc.gov/harmonized_tariff_information/hts/archive/list) identifies 2026 Revisions 11–14 with July labels. Its [previous-year page](https://www.usitc.gov/harmonized_tariff_information/hts/archive/list?page=1) identifies 2025 Revision 16 with a 1 July label. Five complete JSON documents were retrieved over HTTPS, bounded to 30 MiB each and hashed. Revision 11's chapter 09 and Statistical Annexes PDFs and the July statistical changes PDF were also captured; raw files remain ignored under `.local/official-evidence/`, outside static/public artifacts and Git history. Checksums, sizes, URLs, retrieval timestamps and HTTP/content-type receipts are committed in the identity record. These local copies are not an independent durable backup.

| Edition | Archive date label | Other date evidence | Verified provision-effective interval |
|---|---|---|---|
| 2025 Revision 16 | 1 July 2025 | Historical comparison snapshot | Unknown |
| 2026 Revision 11 | 1 July 2026 | Starting July snapshot | Unknown |
| 2026 Revision 12 | 21 July 2026 | Later July snapshot | Unknown |
| 2026 Revision 13 | 29 July 2026 | [Publication announcement](https://www.usitc.gov/harmonized_tariff_information/announcement_archive) says 28 July; retain both labels | Unknown |
| 2026 Revision 14 | 31 July 2026 | Later July snapshot | Unknown |

An edition publication/archive date is not every provision's effective date. JSON does not contain the chapter, section or general statistical notes. Reporting July, capture October, official announcement dates and eventual website publication are different concepts. None establishes the Census observation revision generation.

## Repeatable inspection and actual findings

[The offline reader/comparator](../pipeline/classification.py) consumes source bytes and separately supplied reviewed SHA-256 identities. It verifies the hash, byte/row bounds, JSON keys/encoding, code syntax, types, units, footnotes, hierarchy and duplicate/noncontiguous chapter records. It retains exact untrusted descriptions, original source order/positions and unnamed parents. It makes no network request, reads no credentials, writes no artifact and supplies no approval path. Current verification covers chapter 09 in the captured editions; accepting another chapter argument is not a reviewed source contract for that chapter.

Every inspected edition contains **154 scoped rows: 118 coded and 36 unnamed hierarchy rows**, with **91 ten-digit statistical detail rows** and **39 distinct HS6 prefixes**. All 91 declare `kg` as their only unit. These declarations do not establish valid chapter-wide quantity aggregation, available quantities or value-per-unit calculations.

The hierarchy includes six-digit intermediate rows and a standalone ten-digit root for maté. A leaf such as `0901.11.00.15` only says “Certified organic”; its ancestors specify coffee, not roasted, not decaffeinated and Arabica. Dropping unnamed rows loses that meaning. The reader preserves source text artifacts rather than silently correcting them.

| Compared with 2026 Revision 11 | Row structure/descriptions/units | Footnotes in inspected projection |
|---|---|---|
| 2025 Revision 16 | Equal | Equal |
| 2026 Revision 12 | Equal | Equal |
| 2026 Revision 13 | Equal | **57 coded rows differ** |
| 2026 Revision 14 | Equal | Same 57 differences; equals Revision 13 |

The changed arrays remove general-duty-column endnotes referring to `9903.88.15`. USITC's [29 July update article](https://www.usitc.gov/featured_news/hts_updates_2026_hts_revision_13_rollout_new_hts) discusses cleanup of outdated references. This is contextual support, not an assessment of the referenced provisions or customs advice. **Full metadata is not unchanged.** The helper compares structure separately from footnotes; tariff-rate fields remain in raw evidence outside this statistical-metadata projection. Independent source inspection also compared the complete chapter row objects and found only those footnote differences in these snapshots.

Changes to a parent's description are reported for affected coded descendants even when their leaf labels remain unchanged. Added/removed codes, units, descriptions, footnotes and selected-chapter ordering are observable. Unnamed-parent changes also have a separate before/after report, ordered by ordinal among unnamed nodes; this positional comparison does not infer a stable code identity, split/merge or concordance. Absolute row offsets caused by changes in preceding chapters do not create false semantic changes. Both equal and unequal results retain `comparabilityApproved=false` and `publicationReady=false`.

For local replay, load the committed identity record, read each corresponding ignored JSON, and call `extract_hts_chapter(raw, document['sha256'])` / `compare_hts_chapters(before, after, before_hash, after_hash)`. The task's replay blocked socket creation and subprocess/credential commands and retained detailed results only in ignored `replay.json`. Unit fixtures are expressly illustrative, not official trade data. Run `python -m unittest pipeline.tests.test_classification -v`; Linux CI also runs the complete pipeline suite. Reviewed JSON represents codes/indentation/rates as text: numeric literals, including exponent overflow, are rejected. Omitted duty fields still receive bounded nullable-text validation but are not evaluated as tariffs.

## Import and export classifications remain separate

The [2026 Schedule B index](https://www.census.gov/foreign-trade/schedules/b/2026/index.html) directs use after 1 July. Its [chapter 09 table](https://www.census.gov/foreign-trade/schedules/b/2026/c09.pdf) was inspected through the web reader: 43 export detail rows over the same 39 HS6 prefixes, with displayed kg units and blank secondary-quantity columns. Export unroasted non-decaffeinated coffee has one `0901.11.0000` row; the actual July import edition has six Arabica/Robusta/other and organic subdivisions. Packaged green tea similarly has one export row and four import rows. Shared chapter/HS6 labels do not justify one shared ten-digit dictionary.

Schedule B's [introduction](https://www.census.gov/foreign-trade/schedules/b/2026/introduction.pdf) discusses six-digit alignment and finer mapping differences, but retains inconsistent opening edition/effective-date wording; do not use it as July effectiveness or historical-concordance proof. [July changes](https://www.census.gov/foreign-trade/schedules/b/2026/July_obsoletetonew.pdf) and the [6 July AES bulletin](https://content.govdelivery.com/accounts/USCENSUS/bulletins/41e825d) support the July export change process. AES acceptance/grace periods do not prove API classification normalization. Direct Census PDF capture failed; no captured-byte identity or pinned export edition is claimed for the web-read PDFs.

## Remaining release gates and next work

Revision 11's captured chapter PDF has eight pages; every footer identifies **Revision 11 (2026)**. Its notes include mixture/exclusion rules, foreign matter and packaging treatment, and an organic rule that refers to **General Statistical Note 6** outside this document. Historical chapter/section/general notes, referenced effective intervals and intermediate changes outside these snapshots remain unreviewed. Identical row projections alone cannot certify July 2025/2026 value or quantity continuity.

Keep separate evidence decisions for chapter-value comparability, fine-code mappings and quantity comparability. Complete partner membership/non-overlap and API-vintage review remains required by [the coverage review](census-coverage-review.md). The source record is documentary evidence, not a production manifest; neither it nor these helper outputs can activate official data or override the sample-only public boundary.

Next: bind the dated Schedule C annex and relevant statistical notes to the preserved per-flow partner snapshots, review territories/special buckets and identify an official basis for the detailed API's release/revision generation. Capture missing historical/general/export documents as available. External Census communication remains a separately authorized business action; no message was sent during this task.

Annex A now provides a captured candidate reference: 240 distinct printed designations, with an unresolved Indonesia/Timor-Leste inclusion conflict. See the [coverage follow-up](census-coverage-review.md) for exact limits; this is additional source evidence, not an approved additive country inventory.
