"""Bounded offline operator scenarios for verified, private partner observations."""
import argparse
from pathlib import Path
import re

from pipeline import partners
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, digest, keys, require
from pipeline.census import SourceError

MAX_REVIEW_BYTES = 256 * 1024
MAX_REPORT_BYTES = 512 * 1024
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_SCOPE_FIELDS = ('planId', 'basis', 'flow', 'period', 'product', 'summaryLevel')
_INPUT_FIELDS = ('scanId', 'receiptId', 'sourceHash', 'objectHash')
_REFERENCE = re.compile(r'[a-z0-9][a-z0-9._-]{0,79}')
_MISSING_WORLD_BLOCKER = 'World control not observed; full control reconciliation not verified'


def _bounded_object(value, maximum, secrets=()):
    raw = canonical(value)
    require(0 < len(raw) <= maximum, 'Oversized private partner review object')
    # Reuse strict duplicate/nonfinite decoding and decoded-string secret checks.
    return partners._decode(raw, secrets)


def _active_scan(state):
    return state['scans'][state['receipt']['scanId']]


def _make_review(state):
    scan, receipt = _active_scan(state), state['receipt']
    return {'schemaVersion': 1, 'state': 'draft-partner-review',
            'decisionAuthority': 'operator-scenario-only',
            'scope': {field: scan[field] for field in _SCOPE_FIELDS},
            'inputs': {field: receipt[field] for field in _INPUT_FIELDS},
            'decisions': [{'code': row['partnerCode'], 'disposition': 'unresolved',
                           'rationale': None, 'references': []}
                          for row in scan['rows'] if row['partnerCode'] != '-']}


def make_review(plan, flow, files, secrets=()):
    """Generate an all-unresolved worksheet bound to a verified complete snapshot."""
    state = partners.validate_snapshot(plan, flow, files, secrets, require_complete=True)
    return _bounded_object(_make_review(state), MAX_REVIEW_BYTES, secrets)


def _validate_review(state, review, secrets=()):
    review = _bounded_object(review, MAX_REVIEW_BYTES, secrets)
    expected = _make_review(state)
    keys(review, expected)
    require(type(review['schemaVersion']) is int and review['schemaVersion'] == 1
            and review['state'] == 'draft-partner-review'
            and review['decisionAuthority'] == 'operator-scenario-only', 'Invalid partner worksheet state')
    for field in ('scope', 'inputs'):
        keys(review[field], expected[field])
        require(review[field] == expected[field], 'Partner worksheet evidence binding mismatch')
    decisions = review['decisions']
    require(type(decisions) is list and len(decisions) == len(expected['decisions']),
            'Incomplete partner worksheet decisions')
    observed = {decision['code'] for decision in expected['decisions']}
    seen = set()
    for decision in decisions:
        keys(decision, ('code', 'disposition', 'rationale', 'references'))
        code, disposition = decision['code'], decision['disposition']
        require(type(code) is str and code in observed and code not in seen,
                'Invalid partner worksheet code')
        seen.add(code)
        require(type(disposition) is str and disposition in ('include', 'exclude', 'unresolved'),
                'Invalid partner worksheet disposition')
        rationale, references = decision['rationale'], decision['references']
        if disposition == 'unresolved' and rationale is None and references == []:
            continue
        require(type(rationale) is str and 0 < len(rationale) <= 250 and rationale.strip()
                and all(ord(character) >= 32 and ord(character) != 127 for character in rationale),
                'Invalid partner worksheet rationale')
        require(type(references) is list and 1 <= len(references) <= 10
                and all(type(reference) is str and _REFERENCE.fullmatch(reference) for reference in references),
                'Invalid partner worksheet references')
        require(len(set(references)) == len(references), 'Duplicate partner worksheet references')
    require(seen == observed, 'Incomplete partner worksheet decisions')
    review['decisions'] = sorted(decisions, key=lambda decision: decision['code'])
    return review


def _build_diagnostics(state, review=None, secrets=()):
    scan = _active_scan(state)
    review = _validate_review(state, _make_review(state) if review is None else review, secrets)
    dispositions = {decision['code']: decision['disposition'] for decision in review['decisions']}
    rows = [{'code': row['partnerCode'], 'name': row['partnerName'], 'status': row['status'],
             'value': row['value'], 'disposition': dispositions[row['partnerCode']]}
            for row in scan['rows'] if row['partnerCode'] != '-']
    control = next((row for row in scan['rows'] if row['partnerCode'] == '-'), None)
    world = {'status': 'unobserved', 'value': None} if control is None else {
        'status': control['status'], 'value': control['value']}
    sums = {'observed': 0, 'included': 0, 'excluded': 0, 'unresolved': 0}
    counts = dict.fromkeys(sums, 0)
    categories = {'include': 'included', 'exclude': 'excluded', 'unresolved': 'unresolved'}
    for row in rows:
        category, value = categories[row['disposition']], int(row['value'])
        sums['observed'] += value
        sums[category] += value
        counts['observed'] += 1
        counts[category] += 1
    world_value = None if control is None else int(control['value'])
    blockers = list(partners.BLOCKERS)
    if control is None:
        blockers.append(_MISSING_WORLD_BLOCKER)
    report = {'schemaVersion': 1, 'state': 'private-coverage-diagnostic',
              'decisionAuthority': 'operator-scenario-only', 'scope': dict(review['scope']),
              'inputs': dict(review['inputs']), 'reviewId': digest(review), 'review': review,
              'rows': rows, 'world': world,
              'totals': {category + 'USD': str(value) for category, value in sums.items()},
              'counts': counts,
              'residuals': {category + 'MinusWorldUSD': None if world_value is None else str(sums[category] - world_value)
                            for category in ('observed', 'included')},
              'provenance': {'officialReleaseDate': None, 'officialRevisionDate': None,
                             'ingestedAt': scan['ingestedAt'], 'revisionDetectedAt': None},
              'coverage': 'observed-partners-only', 'leafInventoryApproved': False,
              'apiVintageVerified': False, 'fullWorldReconciliation': 'not-verified',
              'publicationReady': False, 'publicationBlockers': blockers}
    report['reportId'] = digest(report)
    return _bounded_object(report, MAX_REPORT_BYTES, secrets)


def build_diagnostics(plan, flow, files, review=None, secrets=()):
    """Derive exact integer scenarios; residuals never confer publication approval."""
    state = partners.validate_snapshot(plan, flow, files, secrets, require_complete=True)
    return _build_diagnostics(state, review, secrets)


def _checked_path(path):
    path = Path(path).absolute()
    require(not any(partners._unsafe(ancestor) for ancestor in (path, *path.parents)),
            'Unsafe private partner review path')
    return path.resolve()


def _read_json(path, maximum, secrets=()):
    path = _checked_path(path)
    require(path.is_file() and 0 < path.stat().st_size <= maximum, 'Missing or oversized partner review input')
    with path.open('rb') as input_file:
        raw = input_file.read(maximum + 1)
    require(0 < len(raw) <= maximum, 'Missing or oversized partner review input')
    return partners._decode(raw, secrets)


def _output_path(output, snapshot, inputs):
    output = _checked_path(output)
    local = _checked_path(_REPOSITORY_ROOT / '.local')
    snapshot = _checked_path(snapshot)
    require(output.suffix == '.json' and output.is_relative_to(local)
            and output != local and (not output.exists() or output.is_file()),
            'Partner review output must be a private JSON file')
    require(not output.is_relative_to(snapshot)
            and all(output != _checked_path(path) for path in inputs), 'Partner review output overlaps input evidence')
    return output


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Private partner review arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.partner_review',
                                 description='Review verified private partner observations; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--flow', choices=('imports', 'exports'), required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    try:
        plan = partners.validate_plan(_read_json(args.plan, partners.MAX_OBJECT_BYTES))
        state = partners.read_partner_snapshot(plan, args.flow, args.snapshot)
        review = None if args.review is None else _read_json(args.review, MAX_REVIEW_BYTES)
        report = _build_diagnostics(state, review)
        inputs = [args.plan] + ([] if args.review is None else [args.review])
        output = _output_path(args.output, args.snapshot, inputs)
        raw = canonical(report)
        require(0 < len(raw) <= MAX_REPORT_BYTES, 'Oversized private partner diagnostic')
        atomic_write(output, raw)
        counts = report['counts']
        print(f"Private partner diagnostic validated: {counts['observed']} observed, "
              f"{counts['included']} included, {counts['excluded']} excluded, "
              f"{counts['unresolved']} unresolved; publication remains blocked.")
    except Exception:
        parser.exit(1, 'Private partner review failed. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
