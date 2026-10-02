"""Subset checks must never certify global coverage or API revision vintage."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.batch import atomic_write, run_batch
from pipeline.candidates import canonical
from pipeline.census import SourceError
from pipeline.controls import build_report, save_report, run_control_report
from pipeline.restore import SnapshotError
from pipeline.tests.test_batches import source_response

KEY = 'control-report-canary'
TOKEN = 'artifact-canary'
SOURCE_ROOT = Path(__file__).resolve().parents[2] / 'sources'
DOCUMENT = b'%PDF-1.7\n fabricated publication fixture\n%%EOF'


def fixture_statement():
    return {
        'schemaVersion': 1, 'publisher': 'US Census Bureau and Bureau of Economic Analysis',
        'basis': 'census-monthly-goods-nsa-usd-v1', 'period': '2026-07',
        'flows': ['imports', 'exports'], 'officialReleaseDate': '2026-09-03',
        'officialRevisionDate': None,
        'sourceURL': 'https://www.census.gov/foreign-trade/Press-Release/ft900/ft900_2607.pdf',
        'documentHash': hashlib.sha256(DOCUMENT).hexdigest(),
        'claim': 'initial-monthly-announcement-only', 'apiVintageVerified': False,
        'reviewedOn': '2026-10-02', 'releaseIDs': {'census': 'CB26-142', 'bea': 'BEA26-40'},
    }


class ControlReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.market_root, self.world_root = self.root / 'markets', self.root / 'world'
        self.market_plan = json.loads((SOURCE_ROOT / 'batches/coffee-markets-2026-07.json').read_bytes())
        self.world_plan = json.loads((SOURCE_ROOT / 'batches/coffee-world-2026-07.json').read_bytes())
        self.check = json.loads((SOURCE_ROOT / 'control-checks/coffee-2026-07.json').read_bytes())
        self.statement = fixture_statement()

    def acquire(self, market='30', world='200', plan=None):
        names = {p['code']: p['name'].upper() for p in self.check['partners']}
        def response(url):
            data = json.loads(source_response(url, value=world if 'CTY_CODE=-' in url else market))
            columns, row = data
            code = row[columns.index('CTY_CODE')]
            row[columns.index('CTY_NAME')] = 'TOTAL FOR ALL COUNTRIES' if code == '-' else names[code]
            return json.dumps(data).encode()
        with patch('pipeline.census.fetch_bytes', side_effect=response):
            run_batch(plan or self.market_plan, self.market_root, KEY)
            run_batch(self.world_plan, self.world_root, KEY)

    def report(self, **kwargs):
        return build_report(kwargs.get('check', self.check), kwargs.get('market_plan', self.market_plan), self.market_root,
                            self.world_plan, self.world_root, kwargs.get('statement', self.statement),
                            kwargs.get('document', DOCUMENT), secrets=(KEY, TOKEN))

    def test_exact_subset_amounts_with_verified_inputs_and_honest_blockers(self):
        self.acquire()
        report = self.report()
        self.assertFalse(report['publicationReady'])
        self.assertEqual(report['publication']['officialReleaseDate'], '2026-09-03')
        self.assertIsNone(report['publication']['officialRevisionDate'])
        self.assertFalse(report['publication']['apiVintageVerified'])
        self.assertEqual(report['coverage'], 'selected-markets-only')
        for check in report['checks']:
            self.assertEqual(check['selectedTotalUSD'], '120')
            self.assertEqual(check['worldControlUSD'], '200')
            self.assertEqual(check['outsideSelectionUSD'], '80')
            self.assertEqual(check['subsetCheck'], 'passed')
            self.assertEqual(check['fullWorldReconciliation'], 'not-verified')
            self.assertEqual(len(check['observations']), 4)
        self.assertTrue(any('inventory' in blocker.lower() for blocker in report['publicationBlockers']))
        self.assertTrue(any('vintage' in blocker.lower() for blocker in report['publicationBlockers']))
        self.assertTrue(any('raw' in blocker.lower() for blocker in report['publicationBlockers']))
        self.assertEqual(report, self.report())

    def test_coincidental_equality_never_certifies_world_reconciliation(self):
        self.acquire(market='50')
        self.assertTrue(all(check['outsideSelectionUSD'] == '0' for check in self.report()['checks']))
        self.assertFalse(self.report()['publicationReady'])
        self.assertTrue(all(check['fullWorldReconciliation'] == 'not-verified' for check in self.report()['checks']))

    def test_large_amounts_remain_exact_and_zero_is_reported(self):
        for selected, world in [('100000000000000000000001', '400000000000000000000005'), ('0', '0')]:
            with self.subTest(selected=selected):
                # Refresh both generations rather than reusing a previous fixture.
                with tempfile.TemporaryDirectory() as directory:
                    self.market_root, self.world_root = Path(directory) / 'markets', Path(directory) / 'world'
                    self.acquire(market=selected, world=world)
                    for check in self.report()['checks']:
                        self.assertEqual(check['selectedTotalUSD'], str(int(selected) * 4))
                        self.assertEqual(check['outsideSelectionUSD'], str(int(world) - int(selected) * 4))

    def test_selected_amount_above_world_fails_without_replacing_prior_report(self):
        self.acquire()
        previous = self.report()
        save_report(previous, self.root / 'reports', secrets=(KEY, TOKEN))
        pointer = (self.root / 'reports/complete.json').read_bytes()
        self.market_root, self.world_root = self.root / 'new-market', self.root / 'new-world'
        self.acquire(market='51')
        with self.assertRaises(SourceError):
            save_report(self.report(), self.root / 'reports')
        self.assertEqual((self.root / 'reports/complete.json').read_bytes(), pointer)

    def test_corruption_and_incomplete_world_bundle_fail_closed(self):
        self.acquire()
        candidate = next((self.market_root / 'objects').glob('*.json'))
        candidate.write_bytes(candidate.read_bytes() + b' ')
        with self.assertRaises(SourceError):
            self.report()
        self.market_root = self.root / 'new-market'
        self.acquire()
        for pointer in (self.world_root / 'batches').glob('*/complete.json'):
            pointer.unlink()
        with self.assertRaises(SourceError):
            self.report()

    def test_period_inventory_and_plan_scope_must_match_reviewed_check(self):
        self.acquire()
        cases = []
        for field, value in [('period', '2026-06'), ('product', '85'), ('basis', 'other')]:
            altered = copy.deepcopy(self.check)
            altered[field] = value
            cases.append(altered)
        for mutation in ('group', 'duplicate', 'name'):
            altered = copy.deepcopy(self.check)
            if mutation == 'group': altered['partners'][0]['code'] = '0003'
            if mutation == 'duplicate': altered['partners'][1] = altered['partners'][0]
            if mutation == 'name': altered['partners'][0]['name'] = 'China'
            cases.append(altered)
        for check in cases:
            with self.subTest(check=check), self.assertRaises(SourceError):
                self.report(check=check)
        altered_plan = copy.deepcopy(self.market_plan)
        altered_plan['partitions'].pop()
        with self.assertRaises(SourceError):
            self.report(market_plan=altered_plan)

    def test_publication_document_and_period_are_independently_verified(self):
        self.acquire()
        with self.assertRaises(SourceError):
            self.report(document=DOCUMENT + b' changed')
        statement = {**self.statement, 'period': '2026-06'}
        with self.assertRaises(SourceError):
            self.report(statement=statement)

    def test_download_failure_creates_no_report_and_diagnostics_hide_tokens(self):
        output = self.root / 'download'
        with patch('pipeline.controls.fetch_snapshot', side_effect=SnapshotError()), self.assertRaises(SourceError) as raised:
            run_control_report(1, 2, output, KEY, TOKEN, 'Vasuki8/us-trade-explorer')
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertFalse((output / 'reports/complete.json').exists())

    def test_trusted_downloads_archive_verified_document_and_complete_private_report(self):
        self.acquire()
        snapshots = [{path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*.json')}
                     for root in (self.market_root, self.world_root)]
        source_root = self.root / 'sources'
        for relative, value in [('batches/coffee-markets-2026-07.json', self.market_plan),
                                ('batches/coffee-world-2026-07.json', self.world_plan),
                                ('control-checks/coffee-2026-07.json', self.check),
                                ('publications/ft900-2026-07.json', self.statement)]:
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical(value))
        output = self.root / 'download'
        with patch('pipeline.controls.SOURCE_ROOT', source_root), patch('pipeline.controls.fetch_snapshot', side_effect=snapshots), \
             patch('pipeline.publication.fetch_document', return_value=DOCUMENT), \
             patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Report must not re-fetch Census statistics')):
            report = run_control_report(1, 2, output, KEY, TOKEN, 'Vasuki8/us-trade-explorer')
        pointer = json.loads((output / 'reports/complete.json').read_bytes())
        self.assertEqual(pointer, {'reportId': report['reportId']})
        self.assertEqual(report, json.loads((output / 'reports' / (report['reportId'] + '.json')).read_bytes()))
        self.assertEqual((output / 'publication/documents' / (self.statement['documentHash'] + '.pdf')).read_bytes(), DOCUMENT)
        self.assertIn('retrievedAt', json.loads((output / 'publication/proof.json').read_bytes()))
        self.assertFalse(report['publicationReady'])
        self.assertFalse((output / 'active.json').exists())

    def test_interrupted_report_activation_preserves_previous_complete_pointer(self):
        self.acquire()
        output = self.root / 'reports'
        save_report(self.report(), output)
        pointer = (output / 'complete.json').read_bytes()
        self.market_root, self.world_root = self.root / 'new-market', self.root / 'new-world'
        self.acquire(world='250')
        updated = self.report()
        def interrupt(path, data):
            if path.name == 'complete.json':
                raise OSError('fabricated crash')
            return atomic_write(path, data)
        with patch('pipeline.controls.atomic_write', side_effect=interrupt), self.assertRaises(OSError):
            save_report(updated, output)
        self.assertEqual((output / 'complete.json').read_bytes(), pointer)
        self.assertTrue((output / (updated['reportId'] + '.json')).exists())
        save_report(updated, output)
        self.assertEqual(json.loads((output / 'complete.json').read_bytes()), {'reportId': updated['reportId']})


if __name__ == '__main__':
    unittest.main()
