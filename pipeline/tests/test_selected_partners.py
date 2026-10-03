"""Selected-country arithmetic never stands in for worldwide coverage approval."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import partner_review, partners
from pipeline.candidates import canonical, digest
from pipeline.census import SourceError
from pipeline.tests.test_partner_review import snapshot
from pipeline.tests.test_partners import PLAN

try:
    from pipeline import selected_partners
except ImportError:
    selected_partners = None


ROWS = [('-', 'WORLD', '100'), ('1220', 'CANADA', '10'), ('2010', 'MEXICO', '20'),
        ('5330', 'INDIA', '0'), ('5700', 'CHINA', '30'), ('9999', 'Unreviewed bucket', '40')]
# Deliberately fabricated evidence: production pins are replaced only inside tests.
ANNEXES = {f'2026HTSRev{revision}': f'%PDF-fabricated-annex-{revision}'.encode()
           for revision in (11, 12, 13, 14)}


class SelectedPartnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(selected_partners, 'Selected-country coverage report is missing')
        self.addCleanup(patch.stopall)
        patch.object(selected_partners, 'ANNEX_PINS', tuple(
            (edition, len(raw), selected_partners.sha256(raw).hexdigest())
            for edition, raw in ANNEXES.items())).start()
        patch('socket.socket', side_effect=AssertionError('Network forbidden')).start()
        patch('subprocess.run', side_effect=AssertionError('Subprocess forbidden')).start()
        original = type(os.environ).__getitem__
        def getitem(environment, name):
            if name.upper() in ('CENSUS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'):
                raise AssertionError('Credentials forbidden')
            return original(environment, name)
        patch.object(type(os.environ), '__getitem__', getitem).start()

    def build(self, rows=None, flow='imports', files=None, annexes=None):
        return selected_partners.build_report(PLAN, flow,
            snapshot(ROWS if rows is None else rows, flow) if files is None else files,
            ANNEXES if annexes is None else annexes)

    def test_selected_values_and_world_shares_do_not_use_subset_as_denominator(self):
        report = self.build()
        self.assertEqual([row['code'] for row in report['rows']], ['1220', '2010', '5330', '5700'])
        self.assertEqual([row['shareOfWorldPercent'] for row in report['rows']], ['10.00', '20.00', '0.00', '30.00'])
        self.assertEqual(report['totals'], {'observedSelectedUSD': '60', 'selectedTotalUSD': '60',
                                          'selectedShareOfWorldPercent': '60.00'})
        self.assertEqual(report['coverage']['otherObservedCodes'], ['9999'])
        self.assertIs(report['coverage']['allSelectedObserved'], True)
        self.assertIs(report['coverage']['globalCoverageComplete'], False)
        self.assertEqual(report['concentration'], {'status': 'unavailable', 'reason': 'full-partner-inventory-not-approved'})
        self.assertIs(report['publicationReady'], False)
        self.assertIs(report['provenance']['leafInventoryApproved'], False)

    def test_missing_is_not_zero_or_exclusion_and_partial_sum_is_labelled(self):
        report = self.build([row for row in ROWS if row[0] != '5330'])
        missing = report['rows'][2]
        self.assertEqual((missing['status'], missing['value'], missing['sourceName']), ('unobserved', None, None))
        self.assertIsNone(missing['shareOfWorldPercent'])
        self.assertEqual(missing['shareUnavailableReason'], 'partner-not-observed')
        self.assertEqual(report['coverage']['missingSelectedCodes'], ['5330'])
        self.assertEqual(report['totals']['observedSelectedUSD'], '60')
        self.assertIsNone(report['totals']['selectedTotalUSD'])
        self.assertIsNone(report['totals']['selectedShareOfWorldPercent'])
        self.assertEqual(report['rows'][0]['shareOfWorldPercent'], '10.00')

    def test_absent_world_does_not_use_observed_sum_as_control(self):
        report = self.build([row for row in ROWS if row[0] != '-'])
        self.assertEqual(report['world'], {'status': 'unobserved', 'value': None})
        self.assertEqual(report['totals']['selectedTotalUSD'], '60')
        self.assertIsNone(report['totals']['selectedShareOfWorldPercent'])
        self.assertTrue(all(row['shareUnavailableReason'] == 'world-not-observed' for row in report['rows']))

    def test_reported_zero_world_is_not_missing_or_a_division(self):
        report = self.build([(code, name, '0') for code, name, _ in ROWS])
        self.assertEqual(report['world']['status'], 'reported_zero')
        self.assertEqual(report['totals']['selectedTotalUSD'], '0')
        self.assertIsNone(report['totals']['selectedShareOfWorldPercent'])
        self.assertTrue(all(row['shareUnavailableReason'] == 'zero-world-denominator' for row in report['rows']))

    def test_selected_subtotal_above_world_fails_even_when_a_selected_row_is_missing(self):
        for world, remove in [('59', None), ('0', '5330')]:
            rows = [(code, name, world if code == '-' else value) for code, name, value in ROWS if code != remove]
            with self.subTest(world=world), self.assertRaises(SourceError):
                self.build(rows)

    def test_exact_integer_arithmetic_above_javascript_safe_integer_and_half_up_rounding(self):
        report = self.build([('-', 'World', '20000'), ('1220', 'Canada', '1'),
                            ('2010', 'Mexico', '0'), ('5330', 'India', '0'), ('5700', 'China', '0')])
        self.assertEqual(report['rows'][0]['shareOfWorldPercent'], '0.01')
        large = '9007199254740993'
        report = self.build([('-', 'World', large), ('1220', 'Canada', large),
                            ('2010', 'Mexico', '0'), ('5330', 'India', '0'), ('5700', 'China', '0')])
        self.assertEqual(report['totals']['selectedTotalUSD'], large)
        self.assertEqual(report['totals']['selectedShareOfWorldPercent'], '100.00')

    def test_both_flows_have_distinct_definitions_and_unknown_revision_metadata(self):
        for flow, basis, valuation in [('imports', 'general-imports', 'customs-value'),
                                       ('exports', 'total-exports-domestic-plus-reexports', 'FAS-value')]:
            report = self.build(flow=flow)
            self.assertEqual(report['scope']['flow'], flow)
            self.assertEqual(report['provenance']['statisticalBasis']['tradeBasis'], basis)
            self.assertEqual(report['provenance']['statisticalBasis']['valuation'], valuation)
            self.assertIsNone(report['provenance']['officialMetadata']['officialRevisionDate'])

    def test_all_four_exact_annex_editions_required_and_bound_to_report(self):
        report = self.build()
        self.assertEqual(len(report['selectionEvidence']['documents']), 4)
        self.assertEqual(report['selectionEvidence']['claim'], 'selected-schedule-c-designations-only')
        self.assertIsNone(report['selectionEvidence']['effectiveFromVerified'])
        self.assertEqual([row['annexPage'] for row in report['rows']], [3, 3, 6, 6])
        for change in ('missing', 'extra', 'changed', 'wrong-type'):
            documents = dict(ANNEXES)
            if change == 'missing': documents.pop('2026HTSRev12')
            if change == 'extra': documents['extra'] = b'%PDF-extra'
            if change == 'changed': documents['2026HTSRev11'] += b'changed'
            if change == 'wrong-type': documents['2026HTSRev11'] = 'not bytes'
            with self.subTest(change=change), self.assertRaises(SourceError):
                self.build(annexes=documents)

    def test_rebuild_rejects_rehashed_invented_coverage_amounts_evidence_and_boolean_numbers(self):
        report = self.build()
        for mutate in [lambda r: r.update(publicationReady=True),
                       lambda r: r['coverage'].update(globalCoverageComplete=True),
                       lambda r: r['rows'][0].update(value='11'),
                       lambda r: r['rows'][0].update(shareOfWorldPercent='16.67'),
                       lambda r: r['selectionEvidence'].update(effectiveFromVerified='2026-07-01'),
                       lambda r: r.update(schemaVersion=True)]:
            changed = copy.deepcopy(report)
            mutate(changed)
            changed['reportId'] = digest({k: v for k, v in changed.items() if k != 'reportId'})
            with self.assertRaises(SourceError):
                selected_partners.validate_report(PLAN, 'imports', snapshot(ROWS), ANNEXES, changed)

    def test_failed_or_incomplete_archive_does_not_reuse_prior_success(self):
        files = snapshot(ROWS)
        del files['complete.json']
        with self.assertRaises(SourceError):
            self.build(files=files)

    def test_repeatable_offline_derivation_preserves_inputs(self):
        files, documents = snapshot(ROWS), dict(ANNEXES)
        before = copy.deepcopy((files, documents))
        one = self.build(files=files, annexes=documents)
        self.assertEqual(one, self.build(files=files, annexes=documents))
        self.assertEqual((files, documents), before)
        self.assertEqual(selected_partners.validate_report(PLAN, 'imports', files, documents, one), one)

    def test_reflected_secret_is_rejected(self):
        rows = [(code, 'canary-secret' if code == '1220' else name, amount) for code, name, amount in ROWS]
        with self.assertRaises(SourceError):
            selected_partners.build_report(PLAN, 'imports', snapshot(rows), ANNEXES, secrets=('canary-secret',))

    def test_cli_local_output_and_failed_retry_preserve_prior_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, annex_dir = root / '.local' / 'archive', root / '.local' / 'annexes'
            annex_dir.mkdir(parents=True)
            for name, raw in snapshot(ROWS).items():
                path = archive / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            for edition, raw in ANNEXES.items():
                (annex_dir / f'{edition}.pdf').write_bytes(raw)
            plan = root / 'plan.json'
            plan.write_bytes(canonical(PLAN))
            output = root / '.local' / 'reports' / 'selected.json'
            arguments = ['selected', '--plan', str(plan), '--flow', 'imports', '--snapshot', str(archive),
                         '--annex-dir', str(annex_dir), '--output', str(output)]
            with patch.object(partner_review, '_REPOSITORY_ROOT', root), patch('sys.argv', arguments):
                stdout = io.StringIO()
                with redirect_stdout(stdout): selected_partners.main()
                self.assertNotIn('60', stdout.getvalue())
                before = output.read_bytes()
                for unsafe in (root / 'public' / 'data.json', archive / 'new.json',
                               annex_dir / '2026HTSRev11.pdf', plan):
                    with patch('sys.argv', [*arguments[:-1], str(unsafe)]), redirect_stderr(io.StringIO()), \
                         self.assertRaises(SystemExit):
                        selected_partners.main()
                self.assertFalse((root / 'public').exists())
                self.assertEqual(output.read_bytes(), before)
                (annex_dir / '2026HTSRev14.pdf').write_bytes(b'%PDF-changed')
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    selected_partners.main()
                self.assertEqual(error.exception.code, 1)
                self.assertEqual(output.read_bytes(), before)
                self.assertFalse(list(output.parent.glob('.pending-*')))


class ReviewedSelectionPinsTests(unittest.TestCase):
    def test_production_pins_match_retained_source_registry(self):
        root = Path(__file__).resolve().parents[2]
        registry = {}
        for filename in ('hts-evidence-2026-07.json', 'partner-evidence-2026-07.json'):
            registry.update({row['file']: row for row in json.loads((root / 'sources' / filename).read_bytes())['documents']})
        self.assertEqual(len(selected_partners.ANNEX_PINS), 4)
        for edition, size, hash_value in selected_partners.ANNEX_PINS:
            revision = edition.removeprefix('2026HTSRev')
            record = registry[f'hts-2026-rev{revision}-annexes.pdf']
            self.assertEqual((size, hash_value), (record['bytes'], record['sha256']))
        self.assertEqual([row[0] for row in selected_partners.SELECTION], ['1220', '2010', '5330', '5700'])


if __name__ == '__main__':
    unittest.main()
