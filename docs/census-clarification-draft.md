# Census clarification draft — unsent

Prepared **2 October 2026 local / 3 October UTC** for review. This draft was not sent and contains no key, private source amounts or unpublished partner payloads. External communication requires owner authorization. Choose the appropriate official Census trade/API contact only after that authorization.

## Proposed questions

We are building a public US merchandise-trade research website from the International Trade API. Our bounded initial review concerns July 2026, chapter 09, DET country detail, general-import customs value (`GEN_VAL_MO`) and total domestic-plus-foreign export FAS value (`ALL_VAL_MO`), monthly, nominal USD and not seasonally adjusted. We preserve source responses and timestamps, and do not infer missing partner rows as zero.

1. Which dated Schedule C or API metadata establishes the July-effective, non-overlapping country/bucket inventory for these two flows? Does DET treat territories, unidentified/other buckets or US code 1000 differently from filing Schedule C? How should the world control `-` relate to those buckets? Please identify documented inclusion/exclusion rules rather than just current code names.
2. The July 2026 HTS Statistical Annex A lists Timor-Leste separately, but Indonesia's inclusion note still mentions former Portuguese Timor. Which statistical designation boundaries govern these API series for July? The 19 January 2021 AES Western Sahara deletion notice establishes export filing treatment; what establishes import/API code 7370 treatment and effective dates?
3. The statistical-program guide §19 explicitly includes the API in annual historical revisions. Is there a field, release identifier or documented response header identifying the generation/revision of an exact detailed HS API response? What does `LAST_UPDATE` mean and what scope does it cover? If no such identifier exists, is reporting the verified API snapshot retrieval time with an unknown official revision date the appropriate provenance description?
4. How are July 2025/2026 chapter aggregates normalized when detailed import/export classifications or statistical notes change? Which official concordances/notes support historical value comparisons, separately from quantity comparisons?

## Reviewed evidence and scope limits

See [coverage review](census-coverage-review.md), [classification evidence](classification-evidence.md), [statistical-program guide](https://www.census.gov/foreign-trade/guide/sec2.html), [revision procedures](https://www.census.gov/foreign-trade/guide/revisions.html) and [AES notice](https://content.govdelivery.com/accounts/USCENSUS/bulletins/2b980d5). Their dated findings narrow these questions without proving every API bucket, exact observation revision or historical comparability. A response would be reviewed, captured and scoped before changing a publication gate.

An engineering proposal is to distinguish a verified acquisition snapshot from a certified statistical vintage, preserving null official revision dates and explicit unknown-vintage labels where necessary. That proposal is **not implemented or approved for publication in this increment**; review the actual producer contract and allowed comparisons before adopting it. No official number is guaranteed unchanged merely because its reporting month or document text matches another capture.
