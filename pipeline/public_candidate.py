"""Project validated archives into an unpublished, public-field-only review bundle."""
import argparse
from pathlib import Path

from pipeline import partner_review, partners, research, selected_partners
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, digest, keys, require

FLOWS = ('imports', 'exports')
MAX_DATA_BYTES = 64 * 1024
MAX_BUNDLE_BYTES = MAX_DATA_BYTES + 8 * 1024
_BASIS_FIELDS = ('reporter', 'periodKind', 'tradeBasis', 'valuation', 'measure', 'unit',
                 'priceBasis', 'seasonalAdjustment', 'commodityClassification', 'commodityLevel')
_COUNTRY_FIELDS = ('code', 'name', 'geographicNote', 'status', 'value', 'shareOfWorldPercent', 'shareUnavailableReason')


def _project_flow(value):
    selected, classification = value['selectedTrade'], value['classification']
    proof = selected['provenance']
    return {
        'flow': selected['scope']['flow'],
        'statisticalBasis': {field: proof['statisticalBasis'][field] for field in _BASIS_FIELDS},
        'source': {'agency': 'US Census Bureau', 'datasetURL': proof['source']['url']},
        'times': {'retrievedAt': proof['collection']['firstRetainedIngestedAt'],
                  'officialReleaseDate': None, 'officialRevisionDate': None,
                  'revisionDetectedAt': None, 'publishedAt': None},
        'classification': {
            'system': classification['system'],
            'referenceURLs': [document['sourceURL'] for document in classification['documents']],
            'apiClassificationVintage': 'not-identified', 'provisionEffectiveFromVerified': None,
            'historicalComparability': 'not-established',
        },
        'world': {field: selected['world'][field] for field in ('status', 'value')},
        'countries': [{field: row[field] for field in _COUNTRY_FIELDS} for row in selected['rows']],
        'totals': {field: selected['totals'][field] for field in
                   ('observedSelectedUSD', 'selectedTotalUSD', 'selectedShareOfWorldPercent')},
        'coverage': {'allSelectedObserved': selected['coverage']['allSelectedObserved'],
                     'missingSelectedCodes': list(selected['coverage']['missingSelectedCodes'])},
    }


def _assemble(slices, secrets=()):
    data = {
        'schemaVersion': 2, 'artifact': 'public-research-candidate-data', 'source': 'census',
        'publicationState': 'unpublished-review',
        'scope': {'reporter': 'US', 'period': '2026-07', 'periodKind': 'month',
                  'product': {'code': '09', 'name': 'Coffee, tea, maté and spices', 'level': 'HS2'}},
        'coverage': {'kind': 'selected-four-country-subset', 'globalCoverageComplete': False},
        'geography': {'system': 'Schedule C', 'claim': 'selected-schedule-c-designations-only',
                      'effectiveFromVerified': None,
                      'referenceURLs': [document['sourceURL'] for document in
                                        slices['imports']['selectedTrade']['selectionEvidence']['documents']]},
        'analysisPolicy': {field: slices['imports']['analysisPolicy'][field] for field in
                           ('countryValues', 'countryWorldShares', 'historicalGrowth', 'fineCodeJoins',
                            'quantityMetrics', 'globalRankingsAndConcentration')},
        'flows': [_project_flow(slices[flow]) for flow in FLOWS],
    }
    raw = canonical(data)
    require(0 < len(raw) <= MAX_DATA_BYTES, 'Oversized research candidate')
    manifest = {
        'schemaVersion': 2, 'artifact': 'public-research-candidate', 'source': 'census',
        'publicationState': 'unpublished-review', 'period': '2026-07', 'productCode': '09',
        'flows': list(FLOWS), 'countryCodes': [row[0] for row in selected_partners.SELECTION],
        'contentHash': digest(data), 'contentBytes': len(raw),
    }
    return partner_review._bounded_object({'manifest': manifest, 'data': data}, MAX_BUNDLE_BYTES, secrets)


def build_bundle(plan, snapshots, annexes, documents, secrets=()):
    """Rebuild both flows from source evidence; never accept saved reports as proof."""
    keys(snapshots, FLOWS)
    keys(documents, FLOWS)
    slices = {flow: research.build_slice(plan, flow, snapshots[flow], annexes, documents[flow], secrets)
              for flow in FLOWS}
    return _assemble(slices, secrets)


def validate_bundle(plan, snapshots, annexes, documents, bundle, secrets=()):
    bundle = partner_review._bounded_object(bundle, MAX_BUNDLE_BYTES, secrets)
    expected = build_bundle(plan, snapshots, annexes, documents, secrets)
    require(canonical(bundle) == canonical(expected), 'Public candidate source binding mismatch')
    return bundle


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Public candidate arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.public_candidate', description='Prepare an unpublished review bundle')
    for name in ('plan', 'imports', 'exports', 'annex-dir', 'classification-dir', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = partners.validate_plan(partner_review._read_json(args.plan, partners.MAX_OBJECT_BYTES))
        inputs = [args.plan]
        annexes = research._read_documents(args.annex_dir, selected_partners.ANNEX_PINS, inputs, '.pdf')
        documents = {flow: research._read_documents(args.classification_dir, research.CLASSIFICATION_PINS[flow], inputs)
                     for flow in FLOWS}
        # Both paths must be safe before either flow can be written. Read each
        # bounded archive once and validate it before projecting any fields.
        for flow in FLOWS:
            partner_review._output_path(args.output, getattr(args, flow), inputs)
        snapshots = {flow: partners._stored_files(getattr(args, flow)) for flow in FLOWS}
        result = build_bundle(plan, snapshots, annexes, documents)
        output = partner_review._output_path(args.output, args.imports, inputs)
        atomic_write(output, canonical(result))
        print('Paired research candidate validated; publication remains blocked.')
    except Exception:
        parser.exit(1, 'Public candidate preparation failed. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
