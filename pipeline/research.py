"""Assemble private single-period research with reviewed chapter references."""
import argparse
from hashlib import sha256
from pathlib import Path

from pipeline import partner_review, partners, selected_partners
from pipeline.batch import atomic_write
from pipeline.candidates import canonical, digest, keys, require

MAX_SLICE_BYTES = 64 * 1024
# Pins bind reviewed source documents, not an inferred API classification vintage.
CLASSIFICATION_PINS = {
    'imports': (
        ('hts-2026-rev11-chapter09.pdf', 1270970, '8c7258c10d2777553b0a49365bc76dd557284c9e52bcc046e84d91bf5b7130d9'),
        ('hts-2026-rev12-chapter09.pdf', 1270974, 'ebf4ac20cd6b91b424130376f114a291bdbdcdd1e36e6b73af65023bb0244322'),
        ('hts-2026-rev13-chapter09.pdf', 1260048, 'ad13503380b73d476bf1b8f70ae2bf2bc15897343cfbbd97f58dbb1e5dba3987'),
        ('hts-2026-rev14-chapter09.pdf', 1260052, '83fc63ceb2f340cdf88bfc0132a8786c8ae796c751e47a5b43a877f5f37bb7df'),
    ),
    'exports': (
        ('schedule-b-2026-index.html', 80106, 'df8354e83ea8d6450562876a8c7616fc3a250ad63e8ebe8b1426a88882cd9d65'),
        ('schedule-b-2026-chapter09.pdf', 94394, '665700637c011f32bf697a5885653abea2ba8b53ae2372209aecab67f4d19f58'),
    ),
}


def _source_url(name):
    if name.startswith('hts-2026-rev'):
        revision = name.removeprefix('hts-2026-rev').removesuffix('-chapter09.pdf')
        return f'https://hts.usitc.gov/reststop/file?release=2026HTSRev{revision}&filename=Chapter%209'
    suffix = 'index.html' if name.endswith('.html') else 'c09.pdf'
    return 'https://www.census.gov/foreign-trade/schedules/b/2026/' + suffix


def _classification(flow, documents):
    pins = CLASSIFICATION_PINS[flow]
    keys(documents, (name for name, _, _ in pins))
    evidence = []
    for name, size, expected_hash in pins:
        raw = documents[name]
        require(type(raw) is bytes and len(raw) == size and sha256(raw).hexdigest() == expected_hash,
                'Chapter reference evidence mismatch')
        evidence.append({'file': name, 'bytes': size, 'sha256': expected_hash, 'sourceURL': _source_url(name)})
    return {
        'flow': flow, 'system': 'HTSUS' if flow == 'imports' else 'Schedule B',
        'chapter': '09', 'level': 'HS2', 'label': 'Coffee, tea, maté and spices',
        'reviewedUse': 'single-period-chapter-values', 'reviewedReportingPeriod': '2026-07',
        'documents': evidence,
        'editionDateEvidence': None if flow == 'imports' else {'role': 'index-use-after-label', 'date': '2026-07-01'},
        'provisionEffectiveFromVerified': None, 'apiClassificationVintage': 'not-identified',
        'historicalComparability': 'not-established',
        'limitations': [
            'Chapter values retain their source flow and statistical basis.',
            'Import and export detailed codes are separate classifications; no fine-code mapping is approved.',
            'A reference edition date is not the effective date of every provision or an API revision date.',
            'Historical continuity and quantity comparability are not established.',
        ],
    }


def _build_slice(state, annexes, documents, secrets=()):
    selected = selected_partners._build_report(state, annexes, secrets)
    scope = selected['scope']
    require(scope['period'] == '2026-07' and scope['product'] == '09'
            and scope['summaryLevel'] == 'DET', 'Unsupported chapter research scope')
    result = {
        'schemaVersion': 1, 'state': 'private-single-period-research',
        'selectedTrade': selected, 'classification': _classification(scope['flow'], documents),
        'analysisPolicy': {
            'countryValues': 'selected-countries-same-flow-and-period-only',
            'countryWorldShares': 'requires-observed-positive-world-control',
            'historicalGrowth': 'not-supported', 'fineCodeJoins': 'not-supported',
            'quantityMetrics': 'not-supported', 'globalRankingsAndConcentration': 'not-supported',
        },
        'publicationReady': False,
    }
    result['sliceId'] = digest(result)
    return partner_review._bounded_object(result, MAX_SLICE_BYTES, secrets)


def build_slice(plan, flow, files, annexes, documents, secrets=()):
    """Revalidate source observations, selected coverage and chapter references."""
    state = partners.validate_snapshot(plan, flow, files, secrets, require_complete=True)
    return _build_slice(state, annexes, documents, secrets)


def validate_slice(plan, flow, files, annexes, documents, result, secrets=()):
    result = partner_review._bounded_object(result, MAX_SLICE_BYTES, secrets)
    expected = build_slice(plan, flow, files, annexes, documents, secrets)
    require(canonical(result) == canonical(expected), 'Single-period research evidence binding mismatch')
    return result


def _read_documents(directory, pins, inputs, suffix=''):
    documents = {}
    for name, size, _ in pins:
        path = partner_review._checked_path(directory / (name + suffix))
        require(path.is_file() and path.stat().st_size == size, 'Research reference size mismatch')
        with path.open('rb') as source:
            documents[name] = source.read(size + 1)
        inputs.append(path)
    return documents


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Single-period research arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.research', description='Build private single-period research; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--flow', choices=('imports', 'exports'), required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--annex-dir', type=Path, required=True)
    parser.add_argument('--classification-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = partners.validate_plan(partner_review._read_json(args.plan, partners.MAX_OBJECT_BYTES))
        state = partners.read_partner_snapshot(plan, args.flow, args.snapshot)
        inputs = [args.plan]
        annexes = _read_documents(args.annex_dir, selected_partners.ANNEX_PINS, inputs, '.pdf')
        documents = _read_documents(args.classification_dir, CLASSIFICATION_PINS[args.flow], inputs)
        output = partner_review._output_path(args.output, args.snapshot, inputs)
        result = _build_slice(state, annexes, documents)
        atomic_write(output, canonical(result))
        print('Private single-period research validated; publication remains blocked.')
    except Exception:
        parser.exit(1, 'Private single-period research failed. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
