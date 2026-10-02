"""Private DET discovery tests use fabricated bytes, never Census credentials."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from unittest.mock import patch

from pipeline.candidates import canonical, digest
from pipeline.census import SourceError

try:
    from pipeline import partners
except ImportError:
    partners = None

KEY = 'fabricated-census-key'
PLAN = {'schemaVersion': 1, 'basis': 'census-monthly-goods-nsa-usd-v1',
        'period': '2026-07', 'product': '09', 'summaryLevel': 'DET',
        'flows': ['exports', 'imports']}


def evidence(flow='imports', observations=None, timestamp='2026-10-02T01:02:03Z'):
    observations = observations or [('9999', 'Unreviewed numeric group', '7'),
                                    ('-', 'World', '100'), ('1220', 'Canada', '0')]
    prefix, value = ('I', 'GEN_VAL_MO') if flow == 'imports' else ('E', 'ALL_VAL_MO')
    dims = {'DISTRICT': '-', **({'CTY_SUBCODE': '-', 'RP': '-'} if flow == 'imports' else {'DF': '-'})}
    query = {'get': f'{prefix}_COMMODITY_SDESC,CTY_NAME,{value}', 'YEAR': '2026', 'MONTH': '07',
             'COMM_LVL': 'HS2', f'{prefix}_COMMODITY': '09', 'CTY_CODE': '*',
             **dims, 'SUMMARY_LVL': 'DET'}
    header = [f'{prefix}_COMMODITY', f'{prefix}_COMMODITY_SDESC', 'CTY_CODE', 'CTY_NAME', value,
              'COMM_LVL', 'SUMMARY_LVL', 'YEAR', 'MONTH', *dims]
    table = [header] + [['09', 'Coffee, tea, mate and spices', code, name, amount,
                        'HS2', 'DET', '2026', '07', *dims.values()]
                       for code, name, amount in observations]
    raw = json.dumps(table, indent=1).encode()
    rows = [{'product': '09', 'description': 'Coffee, tea, mate and spices', 'partnerCode': code,
             'partnerName': name, 'flow': flow, 'period': '2026-07', 'value': amount,
             'status': 'reported_zero' if amount == '0' else 'reported'}
            for code, name, amount in observations]
    identity = {'schemaVersion': 2, 'flow': flow, 'period': '2026-07', 'sourceQuery': query,
                'sourceHash': hashlib.sha256(raw).hexdigest()}
    candidate = {**identity, 'candidateId': digest(identity), 'state': 'candidate',
                 'source': f'https://api.census.gov/data/timeseries/intltrade/{flow}/hs',
                 'scope': {'commodityLevel': 'HS2', 'product': '09', 'partner': '*', 'coverage': 'unverified'},
                 'officialReleaseDate': None, 'officialRevisionDate': None, 'ingestedAt': timestamp,
                 'rows': rows, 'publicationBlockers': ['Live dimensions and coverage not yet reconciled',
                                                     'Official publication evidence not yet attached']}
    return candidate, raw


def files_at(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*.json') if not path.name.startswith('.pending-')}


class PartnerDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(partners, 'Private partner discovery is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'imports'

    def complete(self, observations=None, timestamp='2026-10-02T01:02:03Z', **options):
        candidate, raw = evidence(observations=observations, timestamp=timestamp)
        def acquire(flow, period, key, **kwargs):
            self.assertEqual((flow, period, key), ('imports', '2026-07', KEY))
            self.assertEqual({k: v for k, v in kwargs.items() if k != 'capture'},
                             {'product': '09', 'partner': '*', 'summary': 'DET',
                              'response_limit': 524288, 'row_limit': 500})
            kwargs['capture'](raw)
            return candidate
        with patch('pipeline.partners.fetch_candidate', side_effect=acquire):
            return partners.run_partner_scan(PLAN, 'imports', self.root, KEY, **options)

    def reject_without_network(self, **options):
        with patch('pipeline.partners.fetch_candidate', side_effect=AssertionError('Network must not be reached')) as acquire:
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY, **options)
            acquire.assert_not_called()

    def test_fixed_plan_rejects_changed_scope_and_extra_fields(self):
        self.assertEqual(partners.validate_plan(PLAN), PLAN)
        for field, value in [('schemaVersion', True), ('basis', 'other'), ('period', '2026-06'),
                             ('product', '*'), ('summaryLevel', 'CGP'), ('flows', ['imports']),
                             ('extra', None)]:
            with self.subTest(field=field):
                bad = copy.deepcopy(PLAN)
                bad[field] = value
                with self.assertRaises(SourceError):
                    partners.validate_plan(bad)

    def test_sorted_observed_roles_zero_and_private_blockers(self):
        for flow in ('imports', 'exports'):
            candidate, raw = evidence(flow)
            scan = partners.normalize_scan(candidate, raw, plan=PLAN, flow=flow)
            self.assertEqual([row['partnerCode'] for row in scan['rows']], ['-', '1220', '9999'])
            self.assertEqual(scan['observedPartners'], [
                {'code': '-', 'name': 'World', 'role': 'world-control'},
                {'code': '1220', 'name': 'Canada', 'role': 'unreviewed-detail'},
                {'code': '9999', 'name': 'Unreviewed numeric group', 'role': 'unreviewed-detail'}])
            self.assertEqual(scan['rows'][1]['status'], 'reported_zero')
            self.assertEqual(scan['state'], 'private-partner-discovery')
            self.assertEqual(scan['coverage'], 'observed-partners-only')
            self.assertFalse(scan['leafInventoryApproved'])
            self.assertFalse(scan['apiVintageVerified'])
            self.assertFalse(scan['publicationReady'])
            self.assertIsNone(scan['officialReleaseDate'])
            self.assertGreaterEqual(len(scan['publicationBlockers']), 4)

    def test_absent_world_is_unobserved_and_unknown_code_is_retained(self):
        candidate, raw = evidence(observations=[('9999', 'Numeric group', '0')])
        scan = partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')
        self.assertEqual(scan['observedPartners'], [{'code': '9999', 'name': 'Numeric group', 'role': 'unreviewed-detail'}])
        self.assertEqual(scan['rows'][0]['value'], '0')

    def test_candidate_strict_contract_rejects_schema_query_scope_dates_and_identity(self):
        candidate, raw = evidence()
        mutations = [('schemaVersion', 1), ('scope', {**candidate['scope'], 'partner': '1220'}),
                     ('sourceQuery', {**candidate['sourceQuery'], 'SUMMARY_LVL': 'CGP'}),
                     ('officialReleaseDate', '2026-09-03'), ('officialRevisionDate', '2026-10-01'),
                     ('source', 'https://evil.example'), ('candidateId', 'a' * 64),
                     ('sourceHash', 'b' * 64), ('publicationBlockers', []), ('extra', '')]
        for field, value in mutations:
            with self.subTest(field=field):
                altered = copy.deepcopy(candidate)
                altered[field] = value
                with self.assertRaises(SourceError):
                    partners.normalize_scan(altered, raw, plan=PLAN, flow='imports')

    def test_raw_reparsing_rejects_mismatch_even_with_fresh_consistent_hash(self):
        candidate, raw = evidence()
        table = json.loads(raw)
        table[1][table[0].index('GEN_VAL_MO')] = '8'
        raw = canonical(table)
        candidate['sourceHash'] = hashlib.sha256(raw).hexdigest()
        candidate['candidateId'] = digest({k: candidate[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
        with self.assertRaises(SourceError):
            partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')

    def test_raw_strict_det_dimensions_duplicates_suppression_and_text(self):
        for field, value in [('SUMMARY_LVL', 'CGP'), ('DISTRICT', '01'), ('YEAR', '2025'),
                             ('I_COMMODITY', '10'), ('GEN_VAL_MO', '(D)'), ('CTY_NAME', 'Bad\x7ftext')]:
            with self.subTest(field=field):
                candidate, raw = evidence()
                table = json.loads(raw)
                table[1][table[0].index(field)] = value
                raw = canonical(table)
                candidate['sourceHash'] = hashlib.sha256(raw).hexdigest()
                candidate['candidateId'] = digest({k: candidate[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
                with self.assertRaises(SourceError):
                    partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')
        for observations in [[('1220', 'Canada', '1'), ('1220', 'Canada', '1')],
                             [('1220', 'Canada', 'NaN')]]:
            candidate, raw = evidence(observations=observations)
            with self.assertRaises(SourceError):
                partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')

    def test_known_secret_escaped_reflection_is_rejected_before_persistence(self):
        candidate, raw = evidence(observations=[('1220', KEY, '1')])
        raw = raw.replace(KEY.encode(), ''.join('\\u%04x' % ord(c) for c in KEY).encode())
        candidate['sourceHash'] = hashlib.sha256(raw).hexdigest()
        candidate['candidateId'] = digest({k: candidate[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
        with self.assertRaises(SourceError):
            partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports', secrets=(KEY,))
        with patch('pipeline.partners.fetch_candidate', side_effect=lambda *a, **kw: (kw['capture'](raw), candidate)[1]):
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        self.assertFalse((self.root / 'raw').exists())
        self.assertNotIn(KEY.encode(), b''.join(files_at(self.root).values()))

    def test_known_secret_quotes_backslashes_and_non_ascii_reflections_reject(self):
        for secret in ('fabricated"quoted-key', 'fabricated\\backslash-key', 'fabricated-é-key'):
            with self.subTest(secret=secret):
                candidate, raw = evidence(observations=[('1220', secret, '1')])
                with self.assertRaises(SourceError):
                    partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports', secrets=(secret,))

    def test_five_hundred_rows_allowed_and_more_rejected(self):
        observations = [(f'{i:04d}', 'Detail', '1') for i in range(500)]
        candidate, raw = evidence(observations=observations)
        self.assertEqual(len(partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')['rows']), 500)
        candidate, raw = evidence(observations=observations + [('0500', 'Detail', '1')])
        with self.assertRaises(SourceError):
            partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')

    def test_large_strict_json_allowed_within_new_object_bound(self):
        observations = [(f'{i:04d}', 'N' * 200, '1') for i in range(400)]
        candidate, raw = evidence(observations=observations)
        self.assertGreater(len(raw), 65536)
        self.assertEqual(len(partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')['rows']), 400)
        oversized = raw + b' ' * 524288
        with self.assertRaises(SourceError):
            partners.normalize_scan(candidate, oversized, plan=PLAN, flow='imports')

    def test_raw_nan_and_duplicate_object_fields_are_strictly_rejected(self):
        candidate, _ = evidence()
        for raw in (b'{"a":1,"a":2}', b'[[NaN]]'):
            altered = copy.deepcopy(candidate)
            altered['sourceHash'] = hashlib.sha256(raw).hexdigest()
            altered['candidateId'] = digest({k: altered[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
            with self.assertRaises(SourceError):
                partners.normalize_scan(altered, raw, plan=PLAN, flow='imports')

    def test_cache_and_identical_refresh_preserve_first_immutable_bytes(self):
        receipt = self.complete()
        first = files_at(self.root)
        with patch('pipeline.partners.fetch_candidate', side_effect=AssertionError('Cache must be reused')):
            self.assertEqual(partners.run_partner_scan(PLAN, 'imports', self.root, KEY), receipt)
        self.assertEqual(self.complete(refresh=True, timestamp='2026-10-02T02:03:04Z'), receipt)
        second = files_at(self.root)
        for name, raw in first.items():
            if name != 'progress.json':
                self.assertEqual(second[name], raw)
        self.assertEqual(partners.verify_partner_scan(PLAN, 'imports', self.root), receipt)
        self.assertEqual(json.loads(second['progress.json'])['generation'], 2)

    def test_all_historical_scans_raws_and_receipts_checked_before_network(self):
        for prefix, mutation in [('raw/', 'missing'), ('raw/', 'corrupt'), ('scans/', 'corrupt'), ('receipts/', 'corrupt')]:
            with self.subTest(prefix=prefix, mutation=mutation):
                self.root = Path(self.temp.name) / (prefix[:-1] + mutation)
                self.complete()
                self.complete(observations=[('1220', 'Canada', '2')], refresh=True)
                paths = list((self.root / prefix[:-1]).glob('*.json'))
                current = json.loads((self.root / 'complete.json').read_bytes())['receiptId']
                active_receipt = json.loads((self.root / 'receipts' / (current + '.json')).read_bytes())
                active = active_receipt['sourceHash'] if prefix == 'raw/' else active_receipt['scanId'] if prefix == 'scans/' else current
                old = next(path for path in paths if path.stem != active)
                if mutation == 'missing':
                    old.unlink()
                else:
                    old.write_bytes(b'{}')
                self.reject_without_network(refresh=True)

    def test_valid_raw_orphan_and_atomic_temporary_retained_but_do_not_complete(self):
        candidate, raw = evidence(observations=[('9999', 'Orphan detail', '1')])
        raw_path = self.root / 'raw' / (candidate['sourceHash'] + '.json')
        raw_path.parent.mkdir(parents=True)
        raw_path.write_bytes(raw)
        temporary = self.root / 'raw' / '.pending-interrupted'
        temporary.write_bytes(b'partial-not-json')
        with self.assertRaises(SourceError):
            partners.verify_partner_scan(PLAN, 'imports', self.root)
        receipt = self.complete()
        self.assertEqual(receipt['rowCount'], 3)
        self.assertEqual(raw_path.read_bytes(), raw)
        self.assertEqual(temporary.read_bytes(), b'partial-not-json')

    def test_wrong_flow_or_secret_raw_orphan_blocks_before_network(self):
        for mode in ('flow', 'secret'):
            with self.subTest(mode=mode):
                self.root = Path(self.temp.name) / mode
                candidate, raw = evidence('exports' if mode == 'flow' else 'imports',
                                          observations=[('1220', KEY if mode == 'secret' else 'Canada', '1')])
                path = self.root / 'raw' / (candidate['sourceHash'] + '.json')
                path.parent.mkdir(parents=True)
                path.write_bytes(raw)
                self.reject_without_network()

    def test_capture_missing_multiple_or_mismatched_rejects_without_raw_objects(self):
        candidate, raw = evidence()
        for mode in ('missing', 'multiple', 'mismatch'):
            with self.subTest(mode=mode):
                self.root = Path(self.temp.name) / mode
                def acquire(*args, **kw):
                    if mode != 'missing':
                        kw['capture'](raw if mode != 'mismatch' else b'[]')
                    if mode == 'multiple':
                        kw['capture'](raw)
                    return candidate
                with patch('pipeline.partners.fetch_candidate', side_effect=acquire):
                    with self.assertRaises(SourceError):
                        partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
                self.assertFalse((self.root / 'raw').exists())

    def test_failed_refresh_keeps_pointer_rejects_verification_and_resume_retries_current_generation(self):
        receipt = self.complete()
        pointer = (self.root / 'complete.json').read_bytes()
        with patch('pipeline.partners.fetch_candidate', side_effect=SourceError(KEY, category='no_results', http_status=204)):
            with self.assertRaises(SourceError) as caught:
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY, refresh=True)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertEqual((self.root / 'complete.json').read_bytes(), pointer)
        journal = json.loads((self.root / 'progress.json').read_bytes())
        self.assertEqual((journal['state'], journal['generation'], journal['category'], journal['httpStatus']),
                         ('failed', 2, 'no_results', 204))
        self.assertIsNone(journal['scanId'])
        self.assertIsNone(journal['receiptId'])
        with self.assertRaises(SourceError):
            partners.verify_partner_scan(PLAN, 'imports', self.root)
        self.assertEqual(self.complete(), receipt)
        self.assertEqual(json.loads((self.root / 'progress.json').read_bytes())['generation'], 2)
        self.assertEqual(partners.verify_partner_scan(PLAN, 'imports', self.root), receipt)

    def test_complete_objects_without_successful_journal_are_reacquired(self):
        receipt = self.complete()
        (self.root / 'progress.json').unlink()
        with self.assertRaises(SourceError):
            partners.verify_partner_scan(PLAN, 'imports', self.root)
        self.assertEqual(self.complete(), receipt)

    def test_successful_journal_must_match_active_receipt(self):
        first = self.complete()
        self.complete(observations=[('1220', 'Canada', '9')], refresh=True)
        (self.root / 'complete.json').write_bytes(canonical({'receiptId': first['receiptId']}))
        with self.assertRaises(SourceError):
            partners.verify_partner_scan(PLAN, 'imports', self.root)

    def test_prospective_file_bound_fails_refresh_and_preserves_old_pointer(self):
        self.complete()
        for index in range(15):
            candidate, raw = evidence(observations=[(f'{index:04d}', 'Orphan', str(index + 1))])
            (self.root / 'raw' / (candidate['sourceHash'] + '.json')).write_bytes(raw)
        self.assertEqual(len(files_at(self.root)), 20)
        pointer = (self.root / 'complete.json').read_bytes()
        with self.assertRaises(SourceError):
            self.complete(observations=[('1220', 'Canada', '25')], refresh=True)
        self.assertEqual((self.root / 'complete.json').read_bytes(), pointer)
        self.assertEqual(len(files_at(self.root)), 20)
        self.assertEqual(json.loads((self.root / 'progress.json').read_bytes())['state'], 'failed')

    def test_prospective_total_byte_bound_fails_without_activating_pointer(self):
        self.complete()
        pointer = (self.root / 'complete.json').read_bytes()
        candidate, raw = evidence(observations=[('9999', 'Orphan', '2')])
        for padding in (510000, 510001, 510002):
            padded = raw + b' ' * padding
            (self.root / 'raw' / (hashlib.sha256(padded).hexdigest() + '.json')).write_bytes(padded)
        candidate, raw = evidence(observations=[('9998', 'More orphan', '3')])
        padded = raw + b' ' * 500000
        (self.root / 'raw' / (hashlib.sha256(padded).hexdigest() + '.json')).write_bytes(padded)
        self.assertLess(sum(map(len, files_at(self.root).values())), 2097152)
        observations = [(f'{i:04d}', 'N' * 200, '1') for i in range(400)]
        with self.assertRaises(SourceError):
            self.complete(observations=observations, refresh=True)
        self.assertEqual((self.root / 'complete.json').read_bytes(), pointer)
        self.assertEqual(json.loads((self.root / 'progress.json').read_bytes())['state'], 'failed')

    def padded_partial_snapshot(self, files, spare=0):
        files = dict(files)
        for index in range(4):
            _, raw = evidence(observations=[(f'{index:04d}', 'Detail', '1')])
            size = min(524288, 2097152 - spare - sum(map(len, files.values())))
            self.assertGreaterEqual(size, len(raw))
            raw += b' ' * (size - len(raw))
            files['raw/' + hashlib.sha256(raw).hexdigest() + '.json'] = raw
        self.assertEqual(sum(map(len, files.values())), 2097152 - spare)
        partners.validate_snapshot(PLAN, 'imports', files)
        return files

    def test_full_pending_snapshot_rejects_before_network_and_keeps_prior_valid_bytes(self):
        attempted = '2026-10-02T01:02:03Z'
        journal = {'schemaVersion': 1, 'planId': digest(PLAN), 'flow': 'imports', 'generation': 1,
                   'state': 'pending', 'scanId': None, 'receiptId': None, 'category': None,
                   'httpStatus': None, 'attemptedAt': attempted}
        files = self.padded_partial_snapshot({'progress.json': canonical(journal)})
        before = dict(files)
        def write(path, raw):
            files[path.relative_to(self.root).as_posix()] = raw
        with patch('pipeline.partners._stored_files', side_effect=lambda root: dict(files)), \
             patch('pipeline.partners.writer', return_value=nullcontext()), patch('pipeline.partners._now', return_value=attempted), \
             patch('pipeline.partners.atomic_write', side_effect=write) as writes, \
             patch('pipeline.partners.fetch_candidate', side_effect=SourceError('safe', category='upstream_unavailable', http_status=503)) as acquire:
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        self.assertLessEqual(sum(map(len, files.values())), 2097152)
        self.assertEqual(files, before)
        partners.validate_snapshot(PLAN, 'imports', files)
        writes.assert_not_called()
        acquire.assert_not_called()

    def test_headroom_rejection_retains_prior_pointer_and_pending_generation(self):
        self.complete()
        files = files_at(self.root)
        journal = json.loads(files['progress.json'])
        journal.update(generation=2, state='pending', scanId=None, receiptId=None,
                       attemptedAt='2026-10-02T01:02:03Z')
        files['progress.json'] = canonical(journal)
        files = self.padded_partial_snapshot(files)
        before = dict(files)
        def write(path, raw):
            files[path.relative_to(self.root).as_posix()] = raw
        with patch('pipeline.partners._stored_files', side_effect=lambda root: dict(files)), \
             patch('pipeline.partners._now', return_value='2026-10-02T01:02:03Z'), \
             patch('pipeline.partners.atomic_write', side_effect=write), \
             patch('pipeline.partners.fetch_candidate', side_effect=SourceError('safe', category='upstream_unavailable', http_status=503)) as acquire:
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        self.assertEqual(files, before)
        partners.validate_snapshot(PLAN, 'imports', files)
        acquire.assert_not_called()

    def test_source_failure_with_reserved_capacity_records_valid_failed_generation(self):
        attempted = '2026-10-02T01:02:03Z'
        journal = {'schemaVersion': 1, 'planId': digest(PLAN), 'flow': 'imports', 'generation': 1,
                   'state': 'pending', 'scanId': None, 'receiptId': None, 'category': None,
                   'httpStatus': None, 'attemptedAt': attempted}
        files = self.padded_partial_snapshot({'progress.json': canonical(journal)}, spare=64)
        def write(path, raw):
            files[path.relative_to(self.root).as_posix()] = raw
        with patch('pipeline.partners._stored_files', side_effect=lambda root: dict(files)), \
             patch('pipeline.partners.writer', return_value=nullcontext()), patch('pipeline.partners._now', return_value=attempted), \
             patch('pipeline.partners.atomic_write', side_effect=write), \
             patch('pipeline.partners.fetch_candidate', side_effect=SourceError('safe', category='upstream_unavailable', http_status=503)):
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        state = partners.validate_snapshot(PLAN, 'imports', files)
        self.assertEqual((state['journal']['state'], state['journal']['category'], state['journal']['httpStatus']),
                         ('failed', 'upstream_unavailable', 503))
        self.assertLessEqual(sum(map(len, files.values())), 2097152)

    def test_failure_after_partial_object_writes_revalidates_retained_snapshot(self):
        self.complete()
        pointer = (self.root / 'complete.json').read_bytes()
        original_write = partners.atomic_write
        def fail_after_scan(path, raw):
            original_write(path, raw)
            if path.parent.name == 'scans':
                raise OSError('fabricated storage failure')
        with patch('pipeline.partners.atomic_write', side_effect=fail_after_scan):
            with self.assertRaises(SourceError):
                self.complete(observations=[('1220', 'Canada', '2')], refresh=True)
        state = partners.validate_snapshot(PLAN, 'imports', files_at(self.root))
        self.assertEqual((self.root / 'complete.json').read_bytes(), pointer)
        self.assertEqual(state['journal']['state'], 'failed')
        self.assertEqual(len(state['scans']), 2)

    def test_failed_journal_is_not_written_over_unexpected_oversized_retained_state(self):
        self.complete()
        actual_files = files_at(self.root)
        overflow = dict(actual_files)
        overflow['raw/' + 'f' * 64 + '.json'] = b' ' * 2097152
        with patch('pipeline.partners._stored_files', side_effect=[actual_files, overflow]), \
             patch('pipeline.partners.atomic_write') as writes, \
             patch('pipeline.partners.fetch_candidate', side_effect=SourceError('safe', category='upstream_unavailable', http_status=503)):
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY, refresh=True)
        self.assertEqual(writes.call_count, 1)
        self.assertEqual(json.loads(writes.call_args.args[1])['state'], 'pending')

    def test_restore_is_byte_exact_and_reusable_without_network(self):
        receipt = self.complete()
        files = files_at(self.root)
        restored = Path(self.temp.name) / 'restored'
        partners.restore_partner_snapshot(PLAN, 'imports', files, restored, KEY)
        self.assertEqual(files_at(restored), files)
        with patch('pipeline.partners.fetch_candidate', side_effect=AssertionError('Restored success must be reusable')):
            self.assertEqual(partners.run_partner_scan(PLAN, 'imports', restored, KEY), receipt)

    def test_failed_generation_snapshot_restores_and_retries(self):
        self.complete()
        with patch('pipeline.partners.fetch_candidate', side_effect=SourceError('safe', category='no_results')):
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY, refresh=True)
        files = files_at(self.root)
        restored = Path(self.temp.name) / 'recovery'
        partners.restore_partner_snapshot(PLAN, 'imports', files, restored, KEY)
        with self.assertRaises(SourceError):
            partners.verify_partner_scan(PLAN, 'imports', restored)
        self.root = restored
        self.complete()
        partners.verify_partner_scan(PLAN, 'imports', restored)

    def test_restore_rejects_all_bad_paths_and_bounds_before_destination_write(self):
        self.complete()
        files = files_at(self.root)
        variants = [files | {'../escape.json': b'{}'}, files | {'objects/' + 'a' * 64 + '.json': b'{}'},
                    files | {'raw/' + 'a' * 64 + '.json': b' ' * 524289},
                    files | {f'raw/{i:064x}.json': b'[]' for i in range(21)},
                    {f'raw/{i:064x}.json': b' ' * 524288 for i in range(5)},
                    files | {'progress.json': b'{"schemaVersion":1,"schemaVersion":1}'}]
        for index, bad in enumerate(variants):
            destination = Path(self.temp.name) / ('reject' + str(index))
            with self.subTest(index=index), self.assertRaises(SourceError):
                partners.restore_partner_snapshot(PLAN, 'imports', bad, destination, KEY)
            self.assertFalse(destination.exists())

    def test_flow_specific_store_rejects_other_flow_reuse(self):
        self.complete()
        with patch('pipeline.partners.fetch_candidate', side_effect=AssertionError('Wrong store must fail before network')):
            with self.assertRaises(SourceError):
                partners.run_partner_scan(PLAN, 'exports', self.root, KEY)

    def test_writer_lock_prevents_requests_and_is_retained(self):
        self.root.mkdir()
        lock = self.root / 'batch.lock'
        lock.write_bytes(b'other-writer')
        self.reject_without_network()
        self.assertEqual(lock.read_bytes(), b'other-writer')

    def test_pending_symlink_is_rejected_before_network_or_cleanup(self):
        self.root.mkdir()
        target = Path(self.temp.name) / 'outside'
        target.write_bytes(b'outside-content')
        link = self.root / '.pending-symlink'
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest('Creating symlinks is unavailable in this environment')
        self.reject_without_network()
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_bytes(), b'outside-content')

    def test_invalid_journal_generations_categories_or_failure_references_block_requests(self):
        for index, (field, value) in enumerate([('generation', True), ('generation', 0), ('category', KEY), ('scanId', 'a' * 64),
                                              ('httpStatus', True), ('attemptedAt', '2026-02-30T00:00:00Z')]):
            with self.subTest(field=field, value=value):
                self.root = Path(self.temp.name) / ('journal-' + str(index))
                self.complete()
                path = self.root / 'progress.json'
                journal = json.loads(path.read_bytes())
                journal.update(state='failed', scanId=None, receiptId=None, category='no_results', httpStatus=None)
                journal[field] = value
                path.write_bytes(canonical(journal))
                self.reject_without_network()

    def test_active_receipt_hash_and_counts_are_independently_checked(self):
        receipt = self.complete()
        files = files_at(self.root)
        path = 'receipts/' + receipt['receiptId'] + '.json'
        for field, value in [('objectHash', 'a' * 64), ('rawHash', 'b' * 64), ('rowCount', 2),
                             ('partnerCount', 2), ('publicationReady', True)]:
            with self.subTest(field=field):
                altered = copy.deepcopy(receipt)
                altered[field] = value
                altered['receiptId'] = digest({k: v for k, v in altered.items() if k != 'receiptId'})
                bad = dict(files)
                del bad[path]
                bad['receipts/' + altered['receiptId'] + '.json'] = canonical(altered)
                bad['complete.json'] = canonical({'receiptId': altered['receiptId']})
                with self.assertRaises(SourceError):
                    partners.validate_snapshot(PLAN, 'imports', bad)

    def test_scan_and_receipt_flags_reject_boolean_lookalike_numbers(self):
        receipt = self.complete()
        files = files_at(self.root)
        scan_path = 'scans/' + receipt['scanId'] + '.json'
        for flag in ('publicationReady', 'apiVintageVerified', 'leafInventoryApproved'):
            with self.subTest(flag=flag):
                altered = json.loads(files[scan_path])
                altered[flag] = 0
                with self.assertRaises(SourceError):
                    partners.validate_snapshot(PLAN, 'imports', {scan_path: canonical(altered),
                        'raw/' + receipt['sourceHash'] + '.json': files['raw/' + receipt['sourceHash'] + '.json']})
                altered = copy.deepcopy(receipt)
                altered[flag] = 0
                altered['receiptId'] = digest({k: v for k, v in altered.items() if k != 'receiptId'})
                receipt_path = 'receipts/' + altered['receiptId'] + '.json'
                with self.assertRaises(SourceError):
                    partners.validate_snapshot(PLAN, 'imports', {**files, receipt_path: canonical(altered)})

    def test_unexpected_adapter_failure_is_sanitized_and_journaled(self):
        with patch('pipeline.partners.fetch_candidate', side_effect=RuntimeError('https://example/?key=' + KEY)):
            with self.assertRaises(SourceError) as caught:
                partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        self.assertNotIn(KEY, str(caught.exception))
        journal = json.loads((self.root / 'progress.json').read_bytes())
        self.assertEqual((journal['state'], journal['category']), ('failed', 'validation_failed'))
        self.assertNotIn(KEY.encode(), b''.join(files_at(self.root).values()))

    def test_atomic_interruption_at_each_object_and_pointer_is_recoverable(self):
        original_write = partners.atomic_write
        for stage in ('raw', 'scans', 'receipts', 'successful-journal', 'pointer'):
            with self.subTest(stage=stage):
                self.root = Path(self.temp.name) / stage
                def interrupt(path, data):
                    original_write(path, data)
                    match = path.parent.name == stage or (stage == 'successful-journal' and path.name == 'progress.json'
                             and json.loads(data)['state'] == 'successful') or (stage == 'pointer' and path.name == 'complete.json')
                    if match:
                        raise KeyboardInterrupt()
                with patch('pipeline.partners.atomic_write', side_effect=interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        self.complete()
                self.assertFalse((self.root / 'batch.lock').exists())
                before = files_at(self.root)
                receipt = self.complete(timestamp='2026-10-02T02:03:04Z')
                for name, raw in before.items():
                    if name.startswith(('raw/', 'scans/', 'receipts/')):
                        self.assertEqual(files_at(self.root)[name], raw)
                self.assertEqual(partners.verify_partner_scan(PLAN, 'imports', self.root), receipt)

    def test_real_source_capture_is_independently_bound_to_scan(self):
        _, raw = evidence()
        with patch('pipeline.census.fetch_bytes', return_value=raw) as transport:
            receipt = partners.run_partner_scan(PLAN, 'imports', self.root, KEY)
        self.assertEqual(receipt['rowCount'], 3)
        self.assertEqual(transport.call_args.kwargs, {'maximum': 524288})
        self.assertEqual((self.root / 'raw' / (hashlib.sha256(raw).hexdigest() + '.json')).read_bytes(), raw)

    def test_cli_restore_then_cache_prints_counts_and_private_blocked_state(self):
        self.complete()
        files = files_at(self.root)
        destination = Path(self.temp.name) / 'cli-restore'
        plan_path = Path(self.temp.name) / 'plan.json'
        plan_path.write_bytes(canonical(PLAN))
        args = ['partners', '--plan', str(plan_path), '--flow', 'imports', '--output', str(destination),
                '--resume-run', '123', '--repository', 'owner/repository']
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'CENSUS_API_KEY': KEY, 'GH_TOKEN': 'fabricated-github-token'}), \
             patch('sys.argv', args), patch('pipeline.restore.fetch_partner_snapshot', return_value=files) as download, \
             patch('pipeline.partners.fetch_candidate', side_effect=AssertionError('Cache should be reused')), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            partners.main()
        self.assertEqual(files_at(destination), files)
        self.assertEqual(download.call_args.args, ('owner/repository', 123, 'fabricated-github-token'))
        self.assertIn('3 observed rows, 3 observed partners', stdout.getvalue())
        self.assertIn('publication remains blocked', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), '')

    def test_cli_parse_and_runtime_failures_do_not_echo_credentials_or_urls(self):
        plan_path = Path(self.temp.name) / 'plan.json'
        plan_path.write_bytes(canonical(PLAN))
        cases = [(['partners', '--flow', KEY], None),
                 (['partners', '--plan', str(plan_path), '--flow', 'imports', '--output', str(self.root)],
                  RuntimeError('https://example/?key=' + KEY))]
        for args, failure in cases:
            with self.subTest(args=args):
                stderr = io.StringIO()
                with patch.dict(os.environ, {'CENSUS_API_KEY': KEY}), patch('sys.argv', args), \
                     patch('pipeline.partners.fetch_candidate', side_effect=failure), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as caught:
                        partners.main()
                self.assertNotEqual(caught.exception.code, 0)
                self.assertNotIn(KEY, stderr.getvalue())
                self.assertNotIn('https://', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
