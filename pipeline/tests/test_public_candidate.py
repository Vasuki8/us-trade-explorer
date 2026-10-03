"""Only fabricated statistics are checked into the shared contract fixture."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import partner_review
from pipeline.candidates import canonical, digest
from pipeline.census import SourceError
from pipeline.tests.test_partner_review import snapshot
from pipeline.tests.test_partners import PLAN
from pipeline.tests import test_research
from pipeline.tests.test_research import DOCUMENTS
from pipeline.tests.test_selected_partners import ANNEXES, ROWS

try:
    from pipeline import public_candidate
except ImportError:
    public_candidate = None


class PublicCandidateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(public_candidate, 'Public candidate producer is missing')
        test_research.ResearchTests.setUp(self)
        self.snapshots = {flow: snapshot(ROWS, flow) for flow in ('imports', 'exports')}

    def build(self):
        return public_candidate.build_bundle(PLAN, self.snapshots, ANNEXES, DOCUMENTS)

    def test_shared_fabricated_fixture_matches_python_producer(self):
        fixture = json.loads((Path(__file__).resolve().parents[2] / 'tests/fixtures/research-candidate.example.json').read_bytes())
        self.assertEqual(fixture['fixtureType'], 'fabricated-for-contract-tests-not-official-data')
        self.assertEqual(self.build(), fixture['bundle'])

    def test_allowlisted_projection_excludes_operational_and_untrusted_text(self):
        self.snapshots = {flow: snapshot([(c, 'PRIVATE-CANARY', v) for c, _, v in ROWS], flow)
                          for flow in self.snapshots}
        result = self.build()
        encoded = canonical(result)
        for forbidden in (b'PRIVATE-CANARY', b'sourceName', b'sourceQuery', b'scanId', b'receiptId',
                          b'snapshotId', b'rawByteLength', b'archiveAttempt', b'9999', b'publicationReady'):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(result['data']['flows'][0]['countries'][0]['name'], 'Canada')
        self.assertEqual(result['manifest']['contentHash'], digest(result['data']))
        self.assertEqual(result['manifest']['contentBytes'], len(canonical(result['data'])))

    def test_basis_and_unknown_dates_are_preserved_separately(self):
        result = self.build()['data']
        self.assertEqual(result['geography']['system'], 'Schedule C')
        self.assertIsNone(result['geography']['effectiveFromVerified'])
        self.assertEqual(len(result['geography']['referenceURLs']), 4)
        self.assertEqual([f['flow'] for f in result['flows']], ['imports', 'exports'])
        self.assertEqual([f['statisticalBasis']['measure'] for f in result['flows']], ['GEN_VAL_MO', 'ALL_VAL_MO'])
        for flow in result['flows']:
            self.assertIsNone(flow['times']['publishedAt'])
            self.assertIsNone(flow['times']['officialReleaseDate'])
            self.assertIsNone(flow['times']['officialRevisionDate'])
            self.assertEqual(flow['classification']['apiClassificationVintage'], 'not-identified')
        self.assertFalse(result['coverage']['globalCoverageComplete'])

    def test_missing_and_reported_zero_have_distinct_totals_and_shares(self):
        self.snapshots['imports'] = snapshot([r for r in ROWS if r[0] != '5330'])
        imports, exports = self.build()['data']['flows']
        self.assertEqual(imports['countries'][2]['status'], 'unobserved')
        self.assertIsNone(imports['totals']['selectedTotalUSD'])
        self.assertEqual(imports['totals']['observedSelectedUSD'], '60')
        self.assertEqual(imports['coverage']['missingSelectedCodes'], ['5330'])
        self.assertEqual(exports['countries'][2]['status'], 'reported_zero')
        self.assertEqual(exports['countries'][2]['shareOfWorldPercent'], '0.00')

    def test_absent_and_zero_world_never_produce_shares(self):
        for rows, reason in [([r for r in ROWS if r[0] != '-'], 'world-not-observed'),
                             ([(c, n, '0') for c, n, _ in ROWS], 'zero-world-denominator')]:
            self.snapshots['imports'] = snapshot(rows)
            flow = self.build()['data']['flows'][0]
            self.assertTrue(all(r['shareOfWorldPercent'] is None for r in flow['countries']))
            self.assertTrue(all(r['shareUnavailableReason'] == reason for r in flow['countries']))

    def test_rehashed_invented_values_do_not_pass_source_replay(self):
        result = self.build()
        result['data']['flows'][0]['countries'][0].update(value='11', shareOfWorldPercent='11.00')
        result['data']['flows'][0]['totals'].update(observedSelectedUSD='61', selectedTotalUSD='61', selectedShareOfWorldPercent='61.00')
        result['manifest']['contentHash'] = digest(result['data'])
        result['manifest']['contentBytes'] = len(canonical(result['data']))
        with self.assertRaises(SourceError):
            public_candidate.validate_bundle(PLAN, self.snapshots, ANNEXES, DOCUMENTS, result)

    def test_both_archives_and_exact_document_sets_are_revalidated(self):
        for change in ('missing-flow', 'extra-flow', 'incomplete-export', 'wrong-flow'):
            snapshots = copy.deepcopy(self.snapshots)
            if change == 'missing-flow': snapshots.pop('exports')
            if change == 'extra-flow': snapshots['reexports'] = snapshots['exports']
            if change == 'incomplete-export': snapshots['exports'].pop('complete.json')
            if change == 'wrong-flow': snapshots['exports'] = snapshots['imports']
            with self.subTest(change=change), self.assertRaises(SourceError):
                public_candidate.build_bundle(PLAN, snapshots, ANNEXES, DOCUMENTS)
        with self.assertRaises(SourceError):
            public_candidate.build_bundle(PLAN, self.snapshots, ANNEXES, {'imports': DOCUMENTS['imports']})

    def test_repeatable_inputs_unchanged_and_secret_reflection_rejected(self):
        before = copy.deepcopy((self.snapshots, ANNEXES, DOCUMENTS))
        bundle = self.build()
        self.assertEqual(bundle, public_candidate.validate_bundle(PLAN, self.snapshots, ANNEXES, DOCUMENTS, bundle))
        self.assertEqual((self.snapshots, ANNEXES, DOCUMENTS), before)
        self.snapshots['imports'] = snapshot([(c, 'SECRET-CANARY', v) for c, _, v in ROWS])
        with self.assertRaises(SourceError):
            public_candidate.build_bundle(PLAN, self.snapshots, ANNEXES, DOCUMENTS, secrets=('SECRET-CANARY',))

    def test_oversized_or_private_fields_cannot_validate_as_a_candidate(self):
        for result in ({'payload': 'x' * public_candidate.MAX_BUNDLE_BYTES},
                       {**self.build(), 'receiptId': 'private-identity'}):
            with self.assertRaises(SourceError):
                public_candidate.validate_bundle(PLAN, self.snapshots, ANNEXES, DOCUMENTS, result)

    def test_cli_atomic_pair_and_failure_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archives = {flow: root / '.local' / flow for flow in self.snapshots}
            for flow, files in self.snapshots.items():
                for name, raw in files.items():
                    path = archives[flow] / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
            refs = root / '.local' / 'references'; refs.mkdir()
            for name, raw in ANNEXES.items(): (refs / (name + '.pdf')).write_bytes(raw)
            for documents in DOCUMENTS.values():
                for name, raw in documents.items(): (refs / name).write_bytes(raw)
            plan = root / 'plan.json'; plan.write_bytes(canonical(PLAN))
            output = root / '.local' / 'candidate.json'
            args = ['candidate', '--plan', str(plan), '--imports', str(archives['imports']),
                    '--exports', str(archives['exports']), '--annex-dir', str(refs),
                    '--classification-dir', str(refs), '--output', str(output)]
            with patch.object(partner_review, '_REPOSITORY_ROOT', root), patch('sys.argv', args):
                with redirect_stdout(io.StringIO()) as printed: public_candidate.main()
                self.assertNotIn('60', printed.getvalue())
                previous = output.read_bytes()
                self.assertEqual(json.loads(previous), self.build())
                with patch.object(public_candidate, 'atomic_write', side_effect=OSError('PRIVATE-CANARY')):
                    with redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit): public_candidate.main()
                    self.assertNotIn('PRIVATE-CANARY', errors.getvalue())
                    self.assertEqual(output.read_bytes(), previous)
                for unsafe in (root / 'public/data.json', archives['imports'] / 'new.json', archives['exports'] / 'new.json', plan):
                    with patch('sys.argv', [*args[:-1], str(unsafe)]), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                        public_candidate.main()
                (archives['exports'] / 'complete.json').write_bytes(b'{}')
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): public_candidate.main()
                self.assertEqual(output.read_bytes(), previous)
                self.assertFalse((root / 'public').exists())


if __name__ == '__main__': unittest.main()
