"""Recovery and evidence-boundary tests; all observations are fabricated."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from pipeline import batch
from pipeline.census import SourceError

KEY = 'private-batch-canary'
SLOT = {'flow': 'imports', 'period': '2026-07', 'product': '09', 'partner': '1220'}
SECOND = {**SLOT, 'flow': 'exports'}
PLAN = {'schemaVersion': 1, 'basis': 'census-monthly-goods-nsa-usd-v1', 'partitions': [SLOT, SECOND]}


def source_response(url, value='123456', extra=False):
    query = parse_qs(urlsplit(url).query)
    prefix = 'I' if '/imports/' in url else 'E'
    value_field = 'GEN_VAL_MO' if prefix == 'I' else 'ALL_VAL_MO'
    header = query['get'][0].split(',') + [name for name in query if name not in ('get', 'key')]
    values = {name: entries[0] for name, entries in query.items() if name not in ('get', 'key')}
    values.update({f'{prefix}_COMMODITY_SDESC': 'Coffee, tea', 'CTY_NAME': 'Canada', value_field: value})
    row = [values[name] for name in header]
    return json.dumps([header, row, *([row] if extra else [])]).encode()


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def complete(self, plan=PLAN, **kwargs):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            return batch.run_batch(copy.deepcopy(plan), self.root, KEY, **kwargs)

    def test_plan_reordering_reuses_identical_bundle_without_network(self):
        first = self.complete()
        second_plan = {**PLAN, 'partitions': list(reversed(PLAN['partitions']))}
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Must reuse verified evidence')):
            second = batch.run_batch(second_plan, self.root, KEY)
        self.assertEqual(second['bundleId'], first['bundleId'])
        self.assertEqual(len(list((self.root / 'objects').glob('*.json'))), 2)
        self.assertEqual(len(second['partitions']), 2)
        self.assertEqual(second['coverage'], 'requested-partitions-only')
        self.assertEqual(second['state'], 'candidate')
        self.assertIsNone(second['officialReleaseDate'])

    def test_invalid_inventory_is_rejected_before_any_request_or_write(self):
        invalid = [
            {**PLAN, 'partitions': [SLOT, SLOT]},
            {**PLAN, 'partitions': [{**SLOT, 'partner': '*'}]},
            {**PLAN, 'partitions': [{**SLOT, 'product': '*'}]},
            {**PLAN, 'partitions': [{**SLOT, 'period': '2026-13'}]},
            {**PLAN, 'schemaVersion': True},
            {**PLAN, 'url': 'https://example.invalid'},
            {**PLAN, 'partitions': [{**SLOT, 'partner': f'{n:04d}'} for n in range(9)]},
        ]
        for plan in invalid:
            with self.subTest(plan=plan), patch('pipeline.census.fetch_bytes', side_effect=AssertionError('No request allowed')):
                with self.assertRaises(SourceError):
                    batch.run_batch(plan, self.root, KEY)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_failed_second_partition_resumes_only_unfinished_work(self):
        calls = []
        def partial(url):
            calls.append(urlsplit(url).path)
            if '/imports/' in url:
                raise SourceError('Rejected', category='no_results', http_status=204)
            return source_response(url)
        # Canonical order is exports, then imports; preserve the first success.
        with patch('pipeline.census.fetch_bytes', side_effect=partial), self.assertRaises(SourceError):
            batch.run_batch(PLAN, self.root, KEY)
        self.assertEqual(len(list((self.root / 'objects').glob('*.json'))), 1)
        self.assertEqual(list((self.root / 'bundles').glob('*.json')), [])
        journal = next((self.root / 'batches').glob('*/progress.json'))
        self.assertIn('no_results', journal.read_text())
        calls.clear()
        def resume(url):
            calls.append(urlsplit(url).path)
            return source_response(url)
        with patch('pipeline.census.fetch_bytes', side_effect=resume):
            bundle = batch.run_batch(PLAN, self.root, KEY)
        self.assertEqual(calls, ['/data/timeseries/intltrade/imports/hs'])
        self.assertEqual(len(bundle['partitions']), 2)

    def test_corrupt_cache_never_satisfies_a_slot(self):
        self.complete()
        path = next((self.root / 'objects').glob('*.json'))
        path.write_text('{}')
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Must fail before network')):
            with self.assertRaises(SourceError):
                batch.run_batch(PLAN, self.root, KEY)
        with self.assertRaises(SourceError):
            batch.verify_bundle(PLAN, self.root)

    def test_failed_refresh_preserves_prior_complete_bundle_and_active_release(self):
        first = self.complete()
        (self.root / 'active.json').write_text('{"release":"last-good"}')
        pointer = next((self.root / 'batches').glob('*/complete.json'))
        previous = pointer.read_bytes()
        def partial(url):
            if '/imports/' in url:
                raise SourceError('Rejected', category='no_results', http_status=204)
            return source_response(url, value='555')
        with patch('pipeline.census.fetch_bytes', side_effect=partial), self.assertRaises(SourceError):
            batch.run_batch(PLAN, self.root, KEY, refresh=True)
        self.assertEqual(pointer.read_bytes(), previous)
        self.assertEqual(batch.verify_bundle(PLAN, self.root)['bundleId'], first['bundleId'])
        self.assertEqual((self.root / 'active.json').read_text(), '{"release":"last-good"}')
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            resumed = batch.run_batch(PLAN, self.root, KEY)
        self.assertNotEqual(resumed['bundleId'], first['bundleId'])
        self.assertEqual(len(list((self.root / 'objects').glob('*.json'))), 3)

    def test_unchanged_refresh_keeps_first_ingestion_and_identity(self):
        first = self.complete()
        objects = {p.name: p.read_bytes() for p in (self.root / 'objects').glob('*.json')}
        second = self.complete(refresh=True)
        self.assertEqual(second['bundleId'], first['bundleId'])
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'objects').glob('*.json')}, objects)

    def test_crash_after_object_write_recovers_without_duplicate_or_overwrite(self):
        original = batch.atomic_write
        def interrupted(path, data):
            if path.name == 'progress.json' and b'"candidateId"' in data:
                raise OSError('Simulated crash before success journal')
            original(path, data)
        with patch('pipeline.census.fetch_bytes', side_effect=source_response), patch('pipeline.batch.atomic_write', side_effect=interrupted), self.assertRaises(SourceError):
            batch.run_batch(PLAN, self.root, KEY)
        objects = {p.name: p.read_bytes() for p in (self.root / 'objects').glob('*.json')}
        self.complete()
        for name, raw in objects.items():
            self.assertEqual((self.root / 'objects' / name).read_bytes(), raw)
        self.assertEqual(len(list((self.root / 'objects').glob('*.json'))), 2)

    def test_reflected_secret_and_unexpected_rows_never_enter_files_or_logs(self):
        for failure in ('reflection', 'extra'):
            with self.subTest(failure=failure):
                def unsafe(url):
                    if failure == 'extra':
                        return source_response(url, extra=True)
                    return source_response(url).replace(b'Canada', KEY.encode())
                logs = io.StringIO()
                with patch('pipeline.census.fetch_bytes', side_effect=unsafe), contextlib.redirect_stderr(logs), self.assertRaises(SourceError):
                    batch.run_batch(PLAN, self.root, KEY)
                self.assertNotIn(KEY, logs.getvalue())
                for path in self.root.rglob('*.json'):
                    self.assertNotIn(KEY, path.read_text())
                self.assertEqual(list((self.root / 'objects').glob('*.json')), [])

    def test_restore_validates_every_file_before_writing(self):
        expected = self.complete()
        snapshot = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*.json')}
        with tempfile.TemporaryDirectory() as other:
            restored = Path(other)
            batch.restore_snapshot(PLAN, snapshot, restored, KEY)
            with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Verified restored slots require no requests')):
                actual = batch.run_batch(PLAN, restored, KEY)
            self.assertEqual(actual['bundleId'], expected['bundleId'])
        object_name = next(name for name in snapshot if name.startswith('objects/'))
        for change in ('tamper', 'secret', 'traversal', 'different_plan'):
            bad = dict(snapshot)
            plan = PLAN
            if change == 'tamper':
                bad[object_name] = bad[object_name].replace(b'123456', b'999999')
            elif change == 'secret':
                bad[object_name] = bad[object_name].replace(b'Canada', KEY.encode())
            elif change == 'traversal':
                bad['../outside.json'] = b'{}'
            else:
                plan = {**PLAN, 'partitions': [SLOT]}
            with self.subTest(change=change), tempfile.TemporaryDirectory() as other:
                restored = Path(other)
                with self.assertRaises(SourceError):
                    batch.restore_snapshot(plan, bad, restored, KEY)
                self.assertEqual(list(restored.iterdir()), [])

    def test_forged_bundle_missing_extra_or_mismatched_reference_fails(self):
        first = self.complete()
        pointer_path = next((self.root / 'batches').glob('*/complete.json'))
        for change in ('missing', 'extra', 'scope'):
            forged = copy.deepcopy(first)
            if change == 'missing':
                forged['partitions'].pop()
            elif change == 'extra':
                forged['partitions'].append(copy.deepcopy(forged['partitions'][0]))
            else:
                forged['partitions'][0]['slot']['partner'] = '5700'
            identity = {k: v for k, v in forged.items() if k != 'bundleId'}
            forged['bundleId'] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            (self.root / 'bundles' / (forged['bundleId'] + '.json')).write_text(json.dumps(forged, sort_keys=True, separators=(',', ':')))
            pointer_path.write_text(json.dumps({'bundleId': forged['bundleId']}))
            with self.subTest(change=change), self.assertRaises(SourceError):
                batch.verify_bundle(PLAN, self.root)

    def test_local_lock_prevents_a_second_writer(self):
        (self.root / 'batch.lock').write_text('other writer')
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('No second writer')):
            with self.assertRaises(SourceError):
                batch.run_batch(PLAN, self.root, KEY)
        self.assertEqual((self.root / 'batch.lock').read_text(), 'other writer')

    def test_restore_without_ingestion_key_does_not_persist_evidence(self):
        self.complete()
        snapshot = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*.json')}
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(SourceError):
                batch.restore_snapshot(PLAN, snapshot, Path(other), '')
            self.assertEqual(list(Path(other).iterdir()), [])

    def test_additional_credentials_are_rejected_after_json_decoding(self):
        token = 'private-github-canary'
        def reflected(url):
            return source_response(url).replace(b'Canada', b'private-github-\\u0063anary')
        with patch('pipeline.census.fetch_bytes', side_effect=reflected), self.assertRaises(SourceError):
            batch.run_batch(PLAN, self.root, KEY, evidence_secrets=(token,))
        for path in self.root.rglob('*.json'):
            self.assertNotIn(token, path.read_text())
        self.assertEqual(list((self.root / 'objects').glob('*.json')), [])

    def test_reported_zero_remains_a_reported_observation(self):
        with patch('pipeline.census.fetch_bytes', side_effect=lambda url: source_response(url, value='0')):
            bundle = batch.run_batch(PLAN, self.root, KEY)
        for entry in bundle['partitions']:
            candidate = json.loads((self.root / 'objects' / (entry['candidateId'] + '.json')).read_bytes())
            self.assertEqual(candidate['rows'][0]['value'], '0')
            self.assertEqual(candidate['rows'][0]['status'], 'reported_zero')

    def test_candidate_contract_rejects_modified_semantics(self):
        self.complete()
        raw = next((self.root / 'objects').glob('*.json')).read_bytes()
        original = json.loads(raw)
        slot = {k: original[k] for k in ('flow', 'period')} | {'product': '09', 'partner': '1220'}
        from pipeline.candidates import validate_candidate
        for change in ('query', 'timestamp', 'fields', 'scope', 'status', 'extra'):
            candidate = copy.deepcopy(original)
            if change == 'query':
                candidate['sourceQuery']['DISTRICT'] = '01'
            elif change == 'timestamp':
                candidate['ingestedAt'] = '2026-02-30T00:00:00Z'
            elif change == 'fields':
                candidate['private'] = 'unexpected'
            elif change == 'scope':
                candidate['rows'][0]['partnerCode'] = '5700'
            elif change == 'status':
                candidate['rows'][0]['status'] = 'reported_zero'
            else:
                candidate['rows'].append(copy.deepcopy(candidate['rows'][0]))
            with self.subTest(change=change), self.assertRaises(SourceError):
                validate_candidate(candidate, slot)

    def test_cli_acquires_the_committed_eight_slot_plan_and_verifies_offline(self):
        plan_path = Path('sources/batches/coffee-markets-2026-07.json')
        args = ['batch', '--plan', str(plan_path), '--output', str(self.root)]
        stdout = io.StringIO()
        with patch.dict(os.environ, {'CENSUS_API_KEY': KEY, 'GH_TOKEN': ''}), patch('sys.argv', args), patch('pipeline.census.fetch_bytes', side_effect=source_response), contextlib.redirect_stdout(stdout):
            batch.main()
        bundle = batch.verify_bundle(json.loads(plan_path.read_text()), self.root)
        self.assertEqual(len(bundle['partitions']), 8)
        self.assertIn('8 requested partitions', stdout.getvalue())
        self.assertNotIn(KEY, stdout.getvalue())
        self.assertEqual({e['slot']['partner'] for e in bundle['partitions']}, {'1220', '2010', '5330', '5700'})

    def test_cli_restore_protects_both_credentials_and_leaves_output_empty(self):
        self.complete()
        snapshot = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*.json')}
        token = 'private-github-canary'
        object_name = next(name for name in snapshot if name.startswith('objects/'))
        snapshot[object_name] = snapshot[object_name].replace(b'Canada', token.encode())
        with tempfile.TemporaryDirectory() as other:
            destination = Path(other) / 'output'
            plan_path = Path(other) / 'plan.json'
            plan_path.write_text(json.dumps(PLAN))
            args = ['batch', '--plan', str(plan_path), '--output', str(destination), '--resume-run', '123']
            stderr = io.StringIO()
            with patch.dict(os.environ, {'CENSUS_API_KEY': KEY, 'GH_TOKEN': token}), patch('sys.argv', args), patch('pipeline.restore.fetch_snapshot', return_value=snapshot), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    batch.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertFalse(destination.exists())
            self.assertNotIn(KEY, stderr.getvalue())
            self.assertNotIn(token, stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
