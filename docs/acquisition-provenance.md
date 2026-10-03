# Retained acquisition provenance

The [offline receipt builder](../pipeline/provenance.py) describes a fully validated retained partner response. It is a **private acquisition snapshot**, not an approved public release or an officially identified revision generation. It currently supports the existing July 2026, HS2 chapter 09, monthly DET import/export plan only.

It reuses the complete [partner archive validator](../pipeline/partners.py): every retained historical raw response, normalized scan, receipt and current successful journal is rechecked before the active response is used. The companion receipt binds the exact raw source hash/length, normalized object hash, candidate/scan/receipt identities, full current journal digest, allowlisted Census URL and credential-free request parameters. Its `snapshotId` covers all receipt metadata, including the retained timestamp and operational journal. Validation rebuilds the receipt from its inputs; recomputing its hash cannot approve invented metadata. Canonical byte comparison distinguishes booleans from numbers.

The receipt identifies general imports at customs value (`GEN_VAL_MO`) separately from total domestic-plus-re-export exports at FAS value (`ALL_VAL_MO`). Both are US merchandise trade, monthly nominal USD, not seasonally adjusted. Import HTS and export Schedule B classifications are labelled separately; this is not a classification-edition or comparability approval. Quantities were not collected. Observed numeric DET rows remain unreviewed; an observed world row does not establish additive coverage, full reconciliation or country concentration eligibility.

## Four time concepts and operational attempts

| Field | Meaning and limit |
|---|---|
| `scope.period` | Month represented by the trade activity; currently July 2026 |
| `collection.firstRetainedIngestedAt` | The active response's original retained candidate ingestion timestamp; this is recorded archive metadata, not independently signed source evidence |
| `collection.archiveAttemptedAt` and `archiveAttemptGeneration` | Current successful pipeline attempt start and operational counter; neither is official release/revision time or a new response completion time |
| `officialMetadata.initialAnnouncement.officialReleaseDate` | Optional reviewed initial monthly announcement date, bound to its exact PDF and statement; the claim remains `initial-monthly-announcement-only` |
| `officialMetadata.apiReleaseDate`, `officialRevisionDate`, `officialRevisionGeneration`, `sourceUpdateLabel` | Unknown and null; no API update label was collected or certified by this contract |
| `officialMetadata.publishedAt`, `revisionDetectedAt` | Null; this private receipt neither publishes observations nor detects a statistical revision |

Existing candidate/scan identities exclude ingestion time. An identical successful refresh retains the first stored scan bytes/time, but has a new journal attempt/generation. The new companion therefore binds the journal without relabelling its start as collection time. The original attempt can start before ingestion; a later retry can start after the first retained ingestion. There is no required ordering between these two concepts. A pending/failed refresh with an old complete pointer is rejected, preserving the older receipt as historical evidence rather than presenting it as the current successful attempt.

Census's [statistical-program guide §19](https://www.census.gov/foreign-trade/guide/sec2.html) names the International Trade API among annually recompiled historical outputs. Its [revisions guide](https://www.census.gov/foreign-trade/guide/revisions.html) distinguishes aggregate/monthly and detailed/annual revision practices. The [import variables](https://api.census.gov/data/timeseries/intltrade/imports/hs/variables.html) label `LAST_UPDATE` an update date. Reviewed **2 October local / 3 October UTC 2026**, these documents establish policy/field descriptions, not a certified generation identifier for our archived bytes. Retaining unknown metadata is an engineering choice grounded in those limits, not a claim that Census forbids ordinary API analysis without a revision timestamp.

## Offline use and publication boundary

Use previously preserved evidence; this command performs no acquisition, credential lookup, source download or publication:

```sh
python -m pipeline.provenance \
  --plan sources/scans/coffee-partners-2026-07.json \
  --flow imports \
  --snapshot .local/partner-evidence/37043703299 \
  --output .local/acquisition-provenance/imports.json \
  --announcement sources/publications/ft900-2026-07.json \
  --document .local/publication-evidence/reviewed-ft900-2026-07.pdf
```

The last two arguments are optional **as a pair**. Without them the announcement stays null. With them the existing publication verifier binds the PDF hash to a separately reviewed statement and requires matching basis/period/flow. This does not extract/certify the announcement's text or prove the API response matches its original release. API release/revision dates remain null even with the announcement attached.

Output is a bounded JSON object (maximum 16 KiB) under ignored `.local/`, outside its source archive and other inputs. Existing private path protections reject symlink/junction ancestors, public destinations and input overlaps. Inputs are loaded once, validated before writing, and the write is atomic; failures retain previous valid output and print a fixed message without source text, input paths or exception details. CLI output contains no trade values. Receipts include no observation amounts or partner names, but are still private evidence and must not enter Git or browser/build artifacts. Ignored local storage is not an independent durable backup.

`archiveConsistencyVerified=true` means exact retained inputs agree. `sourceAuthenticityAttested=false` explicitly limits that claim: a local checksum/schema check is not a signed Census attestation, verified GitHub workflow identity or proof of who acquired the bytes. Fixture tests remain fabricated; the receipt does not promote fixtures or corrupt input into verified official data. The companion is not a complete directory/ZIP inventory identity.

All inventory, classification-comparability, API-vintage and publication flags remain false, with the existing partner publication blockers. No transport, archive/restore protocol, diagnostic schema, source approval, public producer/manifest, sample pin or hosting setting changes. The public loader continues to reject private state before loading payload bytes. The [public-repository evidence safeguards](private-evidence-visibility.md) still block new private acquisition; this offline tool does not settle repository visibility intent or provision its replacement storage.

Next: implement an evidence-bound **scoped coverage decision contract** expressing reviewed included/excluded/unresolved geography and classification metadata. That contract must distinguish a usable validated acquisition snapshot from unknown official revision generation, without fabricating partner membership or permitting unsupported historical comparisons. New private ingestion and public official activation still require their separate acceptance gates.
