"""Offline selected-country values/shares with bounded, reviewed Schedule C evidence."""
import argparse
from hashlib import sha256
from pathlib import Path

from pipeline import partner_review, partners, provenance
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, digest, keys, require

MAX_REPORT_BYTES = 32 * 1024
# Reviewed July editions. These bind document identity, not a certified effective
# interval or the semantics of every DET bucket. See docs/selected-partners.md.
ANNEX_PINS = (
    ('2026HTSRev11', 2517819, '9e0ef8c30a1afe7673e97ee7cad72f4a6340577fd94d0be66b8aa0f44e7c789d'),
    ('2026HTSRev12', 2517845, '1f6c299c8d7a9418aba2d42e1eaffabb9cb562f84711025d82e2e137356f22e8'),
    ('2026HTSRev13', 2517851, 'eb8b42c03dfd430148e00bc729ee448c02f656d87f6020a45f40cad5d19fac7d'),
    ('2026HTSRev14', 2517852, '592f4bac7c5c8d4724ae2bf84f10c2694d498afcdf65654027225f81eab99194'),
)
# Four named designations, not a caller-provided inventory or implicit approval
# of all numeric codes. Page numbers refer to the source PDF (not printed A-n).
SELECTION = (
    ('1220', 'Canada', 3, None),
    ('2010', 'Mexico', 3, 'Includes Isla de Cozumel and Islas Revillagigedo.'),
    ('5330', 'India', 6, 'Includes the Andaman, Nicobar, and Laccadive Islands.'),
    ('5700', 'China', 6, 'Hong Kong, Macao and Taiwan have separate Schedule C designations.'),
)


def _selection_evidence(documents):
    keys(documents, (edition for edition, _, _ in ANNEX_PINS))
    evidence = []
    for edition, size, expected_hash in ANNEX_PINS:
        raw = documents[edition]
        require(type(raw) is bytes and len(raw) == size and sha256(raw).hexdigest() == expected_hash,
                'Selected-country annex evidence mismatch')
        evidence.append({'edition': edition, 'sha256': expected_hash, 'bytes': size,
                         'sourceURL': f'https://hts.usitc.gov/reststop/file?release={edition}&filename=Statistical%20Annexes'})
    return {'claim': 'selected-schedule-c-designations-only', 'effectiveFromVerified': None,
            'documents': evidence}


def _share(value, world):
    if value is None:
        return None, 'partner-not-observed'
    if world is None:
        return None, 'world-not-observed'
    if world == 0:
        return None, 'zero-world-denominator'
    # Integer dollars throughout; round a nonnegative percentage half-up to two
    # decimal places without binary floats or context-dependent Decimal precision.
    hundredths = (int(value) * 20000 + world) // (2 * world)
    return f'{hundredths // 100}.{hundredths % 100:02d}', None


def _build_report(state, documents, secrets=()):
    evidence = _selection_evidence(documents)
    proof = provenance._build_receipt(state, secrets=secrets)
    scan = partner_review._active_scan(state)
    # Upstream fixed-plan validation already enforces these dimensions. Keep the
    # scope explicit at the selection boundary if the upstream plan later grows.
    require(scan['period'] == '2026-07' and scan['product'] == '09'
            and scan['summaryLevel'] == 'DET', 'Selected-country scope mismatch')
    observed = {row['partnerCode']: row for row in scan['rows']}
    control = observed.get('-')
    world = {'status': 'unobserved', 'value': None} if control is None else {
        'status': control['status'], 'value': control['value']}
    world_value = None if control is None else int(control['value'])
    rows, missing, observed_sum = [], [], 0
    for code, name, page, note in SELECTION:
        observation = observed.get(code)
        value = None if observation is None else observation['value']
        if observation is None:
            missing.append(code)
        else:
            observed_sum += int(value)
        share, reason = _share(value, world_value)
        rows.append({'code': code, 'name': name, 'sourceName': None if observation is None else observation['partnerName'],
                     'annexPage': page, 'geographicNote': note,
                     'status': 'unobserved' if observation is None else observation['status'], 'value': value,
                     'shareOfWorldPercent': share, 'shareUnavailableReason': reason})
    require(world_value is None or observed_sum <= world_value, 'Selected-country subtotal exceeds world control')
    subtotal = None if missing else str(observed_sum)
    subset_share, _ = _share(subtotal, world_value)
    selected_codes = {row['code'] for row in rows}
    report = {
        'schemaVersion': 1, 'state': 'private-selected-partner-report',
        'scope': dict(proof['scope']), 'provenance': proof, 'selectionEvidence': evidence,
        'rows': rows, 'world': world,
        'totals': {'observedSelectedUSD': str(observed_sum), 'selectedTotalUSD': subtotal,
                   'selectedShareOfWorldPercent': subset_share},
        'coverage': {'kind': 'selected-four-country-subset', 'allSelectedObserved': not missing,
                     'missingSelectedCodes': missing,
                     'otherObservedCodes': sorted(set(observed) - selected_codes - {'-'}),
                     'otherCodesDisposition': 'not-assessed', 'globalCoverageComplete': False},
        'concentration': {'status': 'unavailable', 'reason': 'full-partner-inventory-not-approved'},
        'publicationReady': False, 'publicationBlockers': list(partners.BLOCKERS),
    }
    report['reportId'] = digest(report)
    return partner_review._bounded_object(report, MAX_REPORT_BYTES, secrets)


def build_report(plan, flow, files, documents, secrets=()):
    """Revalidate the complete archive; neither fetch nor publish any evidence."""
    state = partners.validate_snapshot(plan, flow, files, secrets, require_complete=True)
    return _build_report(state, documents, secrets)


def validate_report(plan, flow, files, documents, report, secrets=()):
    report = partner_review._bounded_object(report, MAX_REPORT_BYTES, secrets)
    expected = build_report(plan, flow, files, documents, secrets)
    require(canonical(report) == canonical(expected), 'Selected-country report evidence binding mismatch')
    return report


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Selected-country report arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.selected_partners',
                                 description='Calculate private selected-country shares; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--flow', choices=('imports', 'exports'), required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--annex-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = partners.validate_plan(partner_review._read_json(args.plan, partners.MAX_OBJECT_BYTES))
        state = partners.read_partner_snapshot(plan, args.flow, args.snapshot)
        documents, inputs = {}, [args.plan]
        for edition, size, _ in ANNEX_PINS:
            path = partner_review._checked_path(args.annex_dir / f'{edition}.pdf')
            require(path.is_file() and path.stat().st_size == size, 'Selected-country annex size mismatch')
            with path.open('rb') as source:
                documents[edition] = source.read(size + 1)
            inputs.append(path)
        output = partner_review._output_path(args.output, args.snapshot, inputs)
        report = _build_report(state, documents)
        atomic_write(output, canonical(report))
        print('Private selected-country report validated; publication remains blocked.')
    except Exception:
        parser.exit(1, 'Private selected-country report failed. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
