"""Offline companion receipts describe retained acquisitions, not official vintages."""
import argparse
from pathlib import Path

from pipeline import partner_review, partners, publication
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, digest, keys, require

MAX_RECEIPT_BYTES = 16 * 1024
_SCOPE_FIELDS = ('planId', 'basis', 'flow', 'period', 'product', 'summaryLevel')
_INPUT_FIELDS = ('scanId', 'receiptId', 'sourceHash', 'objectHash')


def _bounded_object(value, secrets):
    raw = canonical(value)
    require(0 < len(raw) <= MAX_RECEIPT_BYTES, 'Oversized private provenance receipt')
    return partners._decode(raw, secrets)


def _announcement(scan, statement, document, secrets):
    require((statement is None) == (document is None), 'Incomplete initial announcement evidence')
    if statement is None:
        return None
    proof = publication.verify_publication(statement, document, secrets)
    require(proof['period'] == scan['period'] and proof['basis'] == scan['basis']
            and scan['flow'] in proof['flows'], 'Initial announcement scope mismatch')
    return proof


def _build_receipt(state, announcement=None, document=None, secrets=()):
    receipt, journal = state['receipt'], state['journal']
    scan = state['scans'][receipt['scanId']]
    imports = scan['flow'] == 'imports'
    world_observed = any(row['partnerCode'] == '-' for row in scan['rows'])
    value = {
        'schemaVersion': 1,
        'state': 'private-acquisition-snapshot',
        'claim': 'verified-acquisition-snapshot-only',
        'scope': {field: scan[field] for field in _SCOPE_FIELDS},
        'statisticalBasis': {
            'reporter': 'US', 'periodKind': 'month',
            'tradeBasis': 'general-imports' if imports else 'total-exports-domestic-plus-reexports',
            'valuation': 'customs-value' if imports else 'FAS-value',
            'measure': 'GEN_VAL_MO' if imports else 'ALL_VAL_MO',
            'unit': 'USD', 'priceBasis': 'nominal', 'seasonalAdjustment': 'not-seasonally-adjusted',
            'commodityClassification': 'HTS' if imports else 'Schedule B', 'commodityLevel': 'HS2',
        },
        'inputs': {**{field: receipt[field] for field in _INPUT_FIELDS},
                   'candidateId': scan['candidateId'], 'journalHash': digest(journal),
                   'rawByteLength': len(state['raws'][scan['sourceHash']])},
        'source': {'url': scan['source'], 'query': dict(scan['sourceQuery'])},
        'collection': {'firstRetainedIngestedAt': scan['ingestedAt'],
                       'archiveAttemptedAt': journal['attemptedAt'],
                       'archiveAttemptGeneration': journal['generation']},
        'officialMetadata': {
            'initialAnnouncement': _announcement(scan, announcement, document, secrets),
            'apiReleaseDate': None, 'officialRevisionDate': None, 'officialRevisionGeneration': None,
            'sourceUpdateLabel': None, 'publishedAt': None, 'revisionDetectedAt': None,
        },
        'coverage': {'kind': 'observed-partners-only',
                     'observedDetailCount': sum(row['partnerCode'] != '-' for row in scan['rows']),
                     'worldControl': 'observed' if world_observed else 'unobserved',
                     'quantity': 'not-collected'},
        'validation': {'archiveConsistencyVerified': True, 'sourceAuthenticityAttested': False},
        'leafInventoryApproved': False, 'apiVintageVerified': False,
        'classificationComparabilityVerified': False, 'publicationReady': False,
        'publicationBlockers': list(partners.BLOCKERS),
    }
    value['snapshotId'] = digest(value)
    return _bounded_object(value, secrets)


def build_receipt(plan, flow, files, *, announcement=None, document=None, secrets=()):
    """Reparse complete retained evidence; never access the network or credentials."""
    state = partners.validate_snapshot(plan, flow, files, secrets, require_complete=True)
    return _build_receipt(state, announcement, document, secrets)


def validate_receipt(plan, flow, files, receipt, *, announcement=None, document=None, secrets=()):
    """Rebuild from exact inputs; a rehashed claim cannot approve invented metadata."""
    receipt = _bounded_object(receipt, secrets)
    expected = build_receipt(plan, flow, files, announcement=announcement, document=document, secrets=secrets)
    keys(receipt, expected)
    # Canonical byte equality also distinguishes bool/int and int/float values,
    # which ordinary Python dict equality would otherwise equate.
    require(canonical(receipt) == canonical(expected), 'Private provenance evidence binding mismatch')
    return receipt


def _read_document(path):
    path = partner_review._checked_path(path)
    require(path.is_file() and 5 < path.stat().st_size <= publication.MAX_DOCUMENT_BYTES,
            'Missing or oversized initial announcement document')
    with path.open('rb') as document:
        raw = document.read(publication.MAX_DOCUMENT_BYTES + 1)
    require(5 < len(raw) <= publication.MAX_DOCUMENT_BYTES, 'Missing or oversized initial announcement document')
    return raw


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Private provenance arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.provenance',
                                 description='Describe retained private acquisitions; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--flow', choices=('imports', 'exports'), required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--announcement', type=Path)
    parser.add_argument('--document', type=Path)
    args = parser.parse_args()
    try:
        require((args.announcement is None) == (args.document is None), 'Incomplete initial announcement evidence')
        plan = partners.validate_plan(partner_review._read_json(args.plan, partners.MAX_OBJECT_BYTES))
        state = partners.read_partner_snapshot(plan, args.flow, args.snapshot)
        announcement, document = None, None
        inputs = [args.plan]
        if args.announcement is not None:
            inputs.extend((args.announcement, args.document))
            announcement = partner_review._read_json(args.announcement, MAX_RECEIPT_BYTES)
            document = _read_document(args.document)
        output = partner_review._output_path(args.output, args.snapshot, inputs)
        receipt = _build_receipt(state, announcement, document)
        atomic_write(output, canonical(receipt))
        print('Private acquisition snapshot validated; publication remains blocked.')
    except Exception:
        parser.exit(1, 'Private acquisition provenance failed. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
