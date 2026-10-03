"""Fabricated private provenance receipts cannot approve official publication."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
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
from pipeline.tests.test_publication import PDF, statement

try:
    from pipeline import provenance
except ImportError:
    provenance = None


SECRET = 'fabricated-provenance-canary'


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch('socket.socket', side_effect=AssertionError('Network is forbidden')).start()
        patch('subprocess.run', side_effect=AssertionError('Subprocesses are forbidden')).start()
        original_getitem = type(os.environ).__getitem__
        def getitem(environment, name):
            if name.upper() in ('CENSUS_API_KEY', 'GITHUB_TOKEN', 'GH_TOKEN'):
                raise AssertionError('Credential access is forbidden')
            return original_getitem(environment, name)
        patch.object(type(os.environ), '__getitem__', getitem).start()

    def module(self):
        self.assertIsNotNone(provenance, 'Private acquisition provenance is missing')
        return provenance

    def build(self, files=None, flow='imports', **kwargs):
        return self.module().build_receipt(PLAN, flow, snapshot(flow=flow) if files is None else files, **kwargs)

    def rehash(self, value):
        value['snapshotId'] = digest({key: item for key, item in value.items() if key != 'snapshotId'})
        return value

    def assert_blocked(self, value):
        self.assertIs(value['leafInventoryApproved'], False)
        self.assertIs(value['apiVintageVerified'], False)
        self.assertIs(value['classificationComparabilityVerified'], False)
        self.assertIs(value['publicationReady'], False)
        self.assertEqual(value['publicationBlockers'], partners.BLOCKERS)
        self.assertIs(value['validation']['archiveConsistencyVerified'], True)
        self.assertIs(value['validation']['sourceAuthenticityAttested'], False)

    def test_binds_active_raw_query_receipt_object_and_current_journal(self):
        files = snapshot()
        value = self.build(files)
        state = partners.validate_snapshot(PLAN, 'imports', files, require_complete=True)
        scan = state['scans'][state['receipt']['scanId']]
        self.assertEqual(value['state'], 'private-acquisition-snapshot')
        self.assertEqual(value['claim'], 'verified-acquisition-snapshot-only')
        self.assertEqual(value['scope'], {key: scan[key] for key in ('planId', 'basis', 'flow', 'period', 'product', 'summaryLevel')})
        self.assertEqual(value['source']['url'], scan['source'])
        self.assertEqual(value['source']['query'], scan['sourceQuery'])
        self.assertNotIn('key', value['source']['query'])
        for field in ('scanId', 'receiptId', 'sourceHash', 'objectHash'):
            self.assertEqual(value['inputs'][field], state['receipt'][field])
        self.assertEqual(value['inputs']['candidateId'], scan['candidateId'])
        self.assertEqual(value['inputs']['journalHash'], digest(state['journal']))
        self.assertEqual(value['inputs']['rawByteLength'], len(state['raws'][scan['sourceHash']]))
        self.assertEqual(value['snapshotId'], self.rehash(copy.deepcopy(value))['snapshotId'])
        self.assert_blocked(value)

    def test_repeatable_derivation_does_not_mutate_inputs_or_include_values(self):
        files = snapshot()
        before = copy.deepcopy(files)
        first = self.build(files)
        self.assertEqual(canonical(first), canonical(self.build(files)))
        self.assertEqual(files, before)
        self.assertNotIn('rows', first)
        self.assertNotIn('value', first)
        self.assertEqual(first['coverage'], {'kind': 'observed-partners-only', 'observedDetailCount': 2,
                                            'worldControl': 'observed', 'quantity': 'not-collected'})

    def test_trade_basis_and_valuation_remain_distinct_between_flows(self):
        imports, exports = self.build(), self.build(flow='exports')
        self.assertEqual(imports['statisticalBasis'], {'reporter': 'US', 'periodKind': 'month',
            'tradeBasis': 'general-imports', 'valuation': 'customs-value', 'measure': 'GEN_VAL_MO',
            'unit': 'USD', 'priceBasis': 'nominal', 'seasonalAdjustment': 'not-seasonally-adjusted',
            'commodityClassification': 'HTS', 'commodityLevel': 'HS2'})
        self.assertEqual(exports['statisticalBasis']['tradeBasis'], 'total-exports-domestic-plus-reexports')
        self.assertEqual(exports['statisticalBasis']['valuation'], 'FAS-value')
        self.assertEqual(exports['statisticalBasis']['measure'], 'ALL_VAL_MO')
        self.assertEqual(exports['statisticalBasis']['commodityClassification'], 'Schedule B')
        self.assertNotEqual(imports['snapshotId'], exports['snapshotId'])

    def test_unknown_official_dates_stay_null_and_attempt_is_not_collection(self):
        value = self.build()
        self.assertEqual(value['officialMetadata'], {'initialAnnouncement': None, 'apiReleaseDate': None,
            'officialRevisionDate': None, 'officialRevisionGeneration': None, 'sourceUpdateLabel': None,
            'publishedAt': None, 'revisionDetectedAt': None})
        self.assertEqual(value['collection'], {'firstRetainedIngestedAt': '2026-10-02T01:02:03Z',
            'archiveAttemptedAt': '2026-10-02T01:02:03Z', 'archiveAttemptGeneration': 1})

    def test_operational_refresh_changes_receipt_but_preserves_first_retained_timestamp(self):
        first_files, refreshed = snapshot(), snapshot(generation=2)
        journal = partners._decode(refreshed['progress.json'], ())
        journal['attemptedAt'] = '2026-10-03T01:02:03Z'
        refreshed['progress.json'] = canonical(journal)
        first, later = self.build(first_files), self.build(refreshed)
        self.assertEqual(first['inputs']['scanId'], later['inputs']['scanId'])
        self.assertEqual(first['inputs']['receiptId'], later['inputs']['receiptId'])
        self.assertEqual(first['collection']['firstRetainedIngestedAt'], later['collection']['firstRetainedIngestedAt'])
        self.assertEqual(later['collection']['archiveAttemptedAt'], '2026-10-03T01:02:03Z')
        self.assertEqual(later['collection']['archiveAttemptGeneration'], 2)
        self.assertNotEqual(first['inputs']['journalHash'], later['inputs']['journalHash'])
        self.assertNotEqual(first['snapshotId'], later['snapshotId'])
        self.assertIsNone(later['officialMetadata']['officialRevisionGeneration'])

    def test_initial_announcement_is_nested_and_does_not_certify_api_vintage(self):
        value = self.build(announcement=statement(), document=PDF)
        proof = value['officialMetadata']['initialAnnouncement']
        self.assertEqual(proof['officialReleaseDate'], '2026-09-03')
        self.assertEqual(proof['claim'], 'initial-monthly-announcement-only')
        self.assertIs(proof['apiVintageVerified'], False)
        self.assertIsNone(value['officialMetadata']['apiReleaseDate'])
        self.assertIsNone(value['officialMetadata']['officialRevisionDate'])
        self.assert_blocked(value)
        self.module().validate_receipt(PLAN, 'imports', snapshot(), value, announcement=statement(), document=PDF)

    def test_half_or_wrong_period_or_corrupt_announcement_rejected(self):
        for args in ({'announcement': statement()}, {'document': PDF},
                     {'announcement': statement(period='2026-06'), 'document': PDF},
                     {'announcement': statement(), 'document': PDF + b'changed'},
                     {'announcement': statement(apiVintageVerified=True), 'document': PDF}):
            with self.subTest(args=list(args)), self.assertRaises(SourceError):
                self.build(**args)

    def test_rehashed_receipt_cannot_change_claims_scope_queries_or_provenance(self):
        module, files = self.module(), snapshot()
        original = self.build(files)
        mutations = [lambda v: v.update(state='official'), lambda v: v.update(claim='certified-vintage'),
                     lambda v: v['scope'].update(flow='exports'), lambda v: v['source'].update(url='https://evil.invalid'),
                     lambda v: v['source']['query'].update(key=SECRET),
                     lambda v: v['inputs'].update(sourceHash='a' * 64),
                     lambda v: v['collection'].update(firstRetainedIngestedAt='2026-10-03T01:02:03Z'),
                     lambda v: v['officialMetadata'].update(officialRevisionDate='2026-10-02'),
                     lambda v: v['officialMetadata'].update(officialRevisionGeneration=2),
                     lambda v: v['officialMetadata'].update(sourceUpdateLabel='2026-10-02'),
                     lambda v: v['officialMetadata'].update(publishedAt='2026-10-02T01:02:03Z'),
                     lambda v: v.update(publicationReady=True),
                     lambda v: v['validation'].update(sourceAuthenticityAttested=True)]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                value = copy.deepcopy(original)
                mutate(value)
                self.rehash(value)
                with self.assertRaises(SourceError):
                    module.validate_receipt(PLAN, 'imports', files, value)

    def test_numeric_flags_are_rejected_even_when_python_equality_would_match(self):
        for field, number in [('schemaVersion', True), ('leafInventoryApproved', 0), ('apiVintageVerified', 0),
                              ('classificationComparabilityVerified', 0), ('publicationReady', 0)]:
            with self.subTest(field=field):
                value = self.build()
                value[field] = number
                self.rehash(value)
                with self.assertRaises(SourceError):
                    self.module().validate_receipt(PLAN, 'imports', snapshot(), value)

    def test_valid_hashes_do_not_skip_source_reparse(self):
        files = snapshot()
        raw_name = next(name for name in files if name.startswith('raw/'))
        files[raw_name] += b'changed'
        with self.assertRaises(SourceError):
            self.build(files)

    def test_failed_or_pending_attempt_cannot_reuse_old_complete_pointer(self):
        files = snapshot()
        for state in ('failed', 'pending'):
            changed = dict(files)
            changed['progress.json'] = canonical(partners._journal(PLAN, 'imports', 2, state=state,
                category='connection_error' if state == 'failed' else None,
                attempted_at='2026-10-03T01:02:03Z'))
            with self.subTest(state=state), self.assertRaises(SourceError):
                self.build(changed)

    def test_missing_world_is_explicit_not_invented_zero_or_complete_coverage(self):
        value = self.build(snapshot([('1220', 'Canada', '0')]))
        self.assertEqual(value['coverage']['worldControl'], 'unobserved')
        self.assertEqual(value['coverage']['observedDetailCount'], 1)
        self.assert_blocked(value)

    def test_secret_reflection_and_oversized_receipt_are_rejected(self):
        files = snapshot([('1220', SECRET, '7')])
        with self.assertRaises(SourceError):
            self.build(files, secrets=(SECRET,))
        value = self.build()
        value['extra'] = 'x' * (16 * 1024)
        with self.assertRaises(SourceError):
            self.module().validate_receipt(PLAN, 'imports', snapshot(), value)

    def test_receipt_from_other_flow_or_generation_rejected(self):
        value = self.build()
        with self.assertRaises(SourceError):
            self.module().validate_receipt(PLAN, 'exports', snapshot(flow='exports'), value)
        with self.assertRaises(SourceError):
            self.module().validate_receipt(PLAN, 'imports', snapshot(generation=2), value)


class ProvenanceCliTests(unittest.TestCase):
    module = ProvenanceTests.module
    assert_blocked = ProvenanceTests.assert_blocked

    def setUp(self):
        ProvenanceTests.setUp(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name) / 'repository'
        self.repository.mkdir()
        self.store = self.repository / '.local' / 'evidence'
        self.plan = self.repository / 'plan.json'
        self.plan.write_bytes(canonical(PLAN))
        self.output = self.repository / '.local' / 'provenance' / 'imports.json'
        for name, raw in snapshot().items():
            path = self.store / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def cli(self, extra=(), output=None, failure=False):
        module = self.module()
        args = ['provenance', '--plan', str(self.plan), '--flow', 'imports', '--snapshot', str(self.store),
                '--output', str(output or self.output), *extra]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(partner_review, '_REPOSITORY_ROOT', self.repository), patch('sys.argv', args), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            if failure:
                with self.assertRaises(SystemExit) as result:
                    module.main()
                self.assertNotEqual(result.exception.code, 0)
            else:
                module.main()
        return stdout.getvalue(), stderr.getvalue()

    def test_cli_is_offline_repeatable_and_does_not_modify_archive(self):
        before = {path.relative_to(self.store).as_posix(): path.read_bytes() for path in self.store.rglob('*.json')}
        stdout, stderr = self.cli()
        first = self.output.read_bytes()
        self.cli()
        self.assertEqual(self.output.read_bytes(), first)
        self.assertEqual(before, {path.relative_to(self.store).as_posix(): path.read_bytes() for path in self.store.rglob('*.json')})
        self.assertIn('publication remains blocked', stdout)
        self.assertEqual(stderr, '')
        self.module().validate_receipt(PLAN, 'imports', before, partners._decode(first, ()))

    def test_cli_writes_nested_verified_announcement(self):
        announcement = self.repository / 'announcement.json'
        document = self.repository / 'announcement.pdf'
        announcement.write_bytes(canonical(statement()))
        document.write_bytes(PDF)
        self.cli(['--announcement', str(announcement), '--document', str(document)])
        value = partners._decode(self.output.read_bytes(), ())
        self.assertEqual(value['officialMetadata']['initialAnnouncement']['documentHash'], statement()['documentHash'])
        self.assert_blocked(value)

    def test_cli_rejects_public_or_overlapping_output(self):
        for path in (self.repository / 'public' / 'provenance.json', self.store / 'receipt.json', self.plan):
            with self.subTest(path=path):
                stdout, stderr = self.cli(output=path, failure=True)
                self.assertEqual(stdout, '')
                self.assertIn('Publication remains blocked', stderr)
        self.assertEqual(self.plan.read_bytes(), canonical(PLAN))

    def test_cli_error_preserves_previous_output_and_redacts_arguments(self):
        self.cli()
        first = self.output.read_bytes()
        self.plan.write_bytes(b'{"schemaVersion":1,"schemaVersion":1}')
        stdout, stderr = self.cli(failure=True)
        self.assertEqual(self.output.read_bytes(), first)
        self.assertEqual(stdout, '')
        self.assertNotIn(str(self.plan), stderr)
        stdout, stderr = self.cli(['--unknown-' + SECRET], failure=True)
        self.assertNotIn(SECRET, stderr)

    def test_cli_rejects_duplicate_nonfinite_and_oversized_json_before_write(self):
        self.cli()
        previous = self.output.read_bytes()
        for raw in (b'{"schemaVersion":1,"schemaVersion":1}', b'{"schemaVersion":NaN}',
                    b' ' * (partners.MAX_OBJECT_BYTES + 1)):
            with self.subTest(size=len(raw)):
                self.plan.write_bytes(raw)
                self.cli(failure=True)
                self.assertEqual(self.output.read_bytes(), previous)

    def test_cli_announcement_arguments_and_failure_preserve_previous_output(self):
        self.cli()
        previous = self.output.read_bytes()
        document = self.repository / 'wrong.pdf'
        announcement = self.repository / 'announcement.json'
        document.write_bytes(PDF + b'changed')
        announcement.write_bytes(canonical(statement()))
        for extra in (['--document', str(document)], ['--announcement', str(announcement)],
                      ['--announcement', str(announcement), '--document', str(document)]):
            with self.subTest(extra=extra):
                self.cli(extra, failure=True)
                self.assertEqual(self.output.read_bytes(), previous)

    def test_cli_rejects_symlink_output_and_unsafe_snapshot(self):
        target = self.repository / 'outside'
        target.mkdir()
        link = self.repository / '.local' / 'linked'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Directory symlinks are unavailable on this platform')
        self.cli(output=link / 'provenance.json', failure=True)
        self.assertFalse((target / 'provenance.json').exists())
        unsafe = self.store / 'raw' / 'alias.json'
        unsafe.symlink_to(self.plan)
        self.cli(failure=True)
        self.assertFalse(self.output.exists())

    def test_cli_rejects_junction_output_without_writes(self):
        target = self.output.parent
        target.mkdir(parents=True)
        original = partners._unsafe
        with patch.object(partners, '_unsafe', side_effect=lambda path: path == target or original(path)):
            self.cli(failure=True)
        self.assertFalse(self.output.exists())
