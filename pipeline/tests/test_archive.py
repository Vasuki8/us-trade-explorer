"""Archived acquisition and recovery tests use fabricated Census observations."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import batch
from pipeline.candidates import canonical, decode, digest
from pipeline.census import SourceError
from pipeline.tests.test_batches import KEY, PLAN, SLOT, source_response

try:
    from pipeline import archive
except ImportError:
    archive = None


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*.json')}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(archive, 'The private archived-batch protocol is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'

    def complete(self, **kwargs):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            return archive.run_archived_batch(PLAN, self.root, KEY, **kwargs)

    def reject_without_network(self, **kwargs):
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('No source request permitted')):
            with self.assertRaises(SourceError):
                archive.run_archived_batch(PLAN, self.root, KEY, **kwargs)

    def test_capture_receipt_and_verified_reuse_are_idempotent(self):
        first = self.complete()
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Verified successes must be reused')):
            second = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertEqual(first, second)
        self.assertEqual(len(list((self.root / 'raw').glob('*.json'))), 2)
        self.assertEqual(len(first['rawObjects']), 2)
        self.assertTrue(all(len(entry['candidateIds']) == 1 for entry in first['rawObjects']))
        self.assertEqual(first['coverage'], 'requested-partitions-only')
        self.assertTrue(all(blocker in first['publicationBlockers'] for blocker in batch.BUNDLE_BLOCKERS))
        self.assertIn('Unreferenced raw responses do not validate normalized observations', first['publicationBlockers'])
        self.assertEqual(archive.verify_archived_bundle(PLAN, self.root), first)

    def test_missing_corrupt_or_changed_raw_rejects_before_new_requests(self):
        for mode in ('missing', 'corrupt', 'changed'):
            with self.subTest(mode=mode):
                self.root = Path(self.temp.name) / mode
                self.complete()
                raw = next((self.root / 'raw').glob('*.json'))
                if mode == 'missing':
                    raw.unlink()
                elif mode == 'corrupt':
                    raw.write_bytes(b'{}')
                else:
                    data = json.loads(raw.read_bytes())
                    data[1][data[0].index('CTY_NAME')] = 'Wrong partner label'
                    raw.write_bytes(canonical(data))
                self.reject_without_network(refresh=True)
                with self.assertRaises(SourceError):
                    archive.verify_archived_bundle(PLAN, self.root)

    def test_legacy_normalized_only_cache_cannot_be_silently_upgraded(self):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            batch.run_batch(PLAN, self.root, KEY)
        before = snapshot(self.root)
        self.reject_without_network(refresh=True)
        self.assertEqual(snapshot(self.root), before)

    def test_every_historical_candidate_requires_raw_revalidation(self):
        self.complete()
        with patch('pipeline.census.fetch_bytes', side_effect=lambda url: source_response(url, value='456')):
            archive.run_archived_batch(PLAN, self.root, KEY, refresh=True)
        objects = sorted((self.root / 'objects').glob('*.json'))
        self.assertEqual(len(objects), 4)
        current = archive.verify_archived_bundle(PLAN, self.root)
        bundle = json.loads((self.root / 'bundles' / (current['bundleId'] + '.json')).read_bytes())
        active = {entry['candidateId'] for entry in bundle['partitions']}
        historic = next(path for path in objects if path.stem not in active)
        candidate = json.loads(historic.read_bytes())
        (self.root / 'raw' / (candidate['sourceHash'] + '.json')).unlink()
        self.reject_without_network()

    def test_raw_with_consistent_hash_but_different_observation_rejects(self):
        self.complete()
        files = snapshot(self.root)
        object_path = next(name for name in files if name.startswith('objects/'))
        candidate = json.loads(files[object_path])
        raw_path = 'raw/' + candidate['sourceHash'] + '.json'
        altered = json.loads(files.pop(raw_path))
        field = 'ALL_VAL_MO' if candidate['flow'] == 'exports' else 'GEN_VAL_MO'
        altered[1][altered[0].index(field)] = '987'
        raw = canonical(altered)
        candidate['sourceHash'] = hashlib.sha256(raw).hexdigest()
        candidate['candidateId'] = digest({k: candidate[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
        # Test the underlying all-object preflight, independent of receipt identities.
        files = {object_path: canonical(candidate), 'raw/' + candidate['sourceHash'] + '.json': raw,
                 next(name for name in files if name.endswith('/progress.json')): canonical({
                     'schemaVersion': 1, 'planId': digest(batch.validate_plan(PLAN)),
                     'entries': [batch.pending(slot) for slot in batch.validate_plan(PLAN)['partitions']]})}
        files['objects/' + candidate['candidateId'] + '.json'] = files.pop(object_path)
        destination = Path(self.temp.name) / 'restore'
        with self.assertRaises(SourceError):
            archive.restore_archived_snapshot(PLAN, files, destination, KEY)
        self.assertFalse(destination.exists())

    def test_failed_refresh_preserves_receipt_but_verification_rejects_generation_mismatch(self):
        first = self.complete()
        pointer = self.root / 'archive' / 'complete.json'
        previous = pointer.read_bytes()
        def partial(url):
            if '/imports/' in url:
                raise SourceError('No results', category='no_results', http_status=204)
            return source_response(url, value='999')
        with patch('pipeline.census.fetch_bytes', side_effect=partial), self.assertRaises(SourceError):
            archive.run_archived_batch(PLAN, self.root, KEY, refresh=True)
        self.assertEqual(pointer.read_bytes(), previous)
        with self.assertRaises(SourceError):
            archive.verify_archived_bundle(PLAN, self.root)
        partial_files = snapshot(self.root)
        restored = Path(self.temp.name) / 'recovery'
        archive.restore_archived_snapshot(PLAN, partial_files, restored, KEY)
        calls = []
        def resume(url):
            calls.append(url)
            return source_response(url)
        with patch('pipeline.census.fetch_bytes', side_effect=resume):
            result = archive.run_archived_batch(PLAN, restored, KEY)
        self.assertEqual(len(calls), 1)
        self.assertIn('/imports/', calls[0])
        self.assertNotEqual(result['receiptId'], first['receiptId'])

    def test_crash_before_receipt_activation_retains_old_receipt_and_can_resume(self):
        first = self.complete()
        before = (self.root / 'archive' / 'complete.json').read_bytes()
        original = archive.atomic_write
        def crash(path, data):
            if path == self.root / 'archive' / 'complete.json':
                raise OSError('Simulated interrupted receipt activation')
            original(path, data)
        with patch('pipeline.census.fetch_bytes', side_effect=lambda url: source_response(url, value='888')):
            with patch('pipeline.archive.atomic_write', side_effect=crash), self.assertRaises(SourceError):
                archive.run_archived_batch(PLAN, self.root, KEY, refresh=True)
        self.assertEqual((self.root / 'archive' / 'complete.json').read_bytes(), before)
        with self.assertRaises(SourceError):
            archive.verify_archived_bundle(PLAN, self.root)
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Completed new bundle must resume offline')):
            recovered = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertNotEqual(recovered['receiptId'], first['receiptId'])

    def test_capture_orphan_is_retained_validated_and_does_not_satisfy_slot(self):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            with patch('pipeline.batch.save_candidate', side_effect=OSError('Crash after validated raw write')):
                with self.assertRaises(SourceError):
                    archive.run_archived_batch(PLAN, self.root, KEY)
        before = {path.name: path.read_bytes() for path in (self.root / 'raw').glob('*.json')}
        self.assertEqual(len(before), 1)
        self.assertEqual(list((self.root / 'objects').glob('*.json')), [])
        calls = []
        def changed(url):
            calls.append(url)
            return source_response(url, value='789')
        with patch('pipeline.census.fetch_bytes', side_effect=changed):
            receipt = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sum(not entry['candidateIds'] for entry in receipt['rawObjects']), 1)
        for name, raw in before.items():
            self.assertEqual((self.root / 'raw' / name).read_bytes(), raw)
        self.assertEqual(archive.verify_archived_bundle(PLAN, self.root), receipt)

    def test_escaped_secret_in_matching_raw_orphan_rejects_before_requests(self):
        self.complete()
        response = source_response('https://api.census.gov/data/timeseries/intltrade/imports/hs?get=I_COMMODITY_SDESC,CTY_NAME,GEN_VAL_MO&YEAR=2026&MONTH=07&COMM_LVL=HS2&I_COMMODITY=09&CTY_CODE=1220&DISTRICT=-&CTY_SUBCODE=-&RP=-')
        data = json.loads(response)
        data[1][data[0].index('CTY_NAME')] = KEY
        raw = json.dumps(data).replace(KEY, ''.join(f'\\u{ord(c):04x}' for c in KEY)).encode()
        (self.root / 'raw' / (hashlib.sha256(raw).hexdigest() + '.json')).write_bytes(raw)
        self.reject_without_network()

    def test_malformed_unknown_or_unauthorized_raw_orphan_rejects(self):
        self.complete()
        candidates = list((self.root / 'raw').glob('*.json'))
        good = candidates[0].read_bytes()
        data = json.loads(good)
        data[1][data[0].index('CTY_CODE')] = '2010'
        for raw in (b'not-json', b'{"duplicate":1,"duplicate":2}', canonical(data)):
            path = self.root / 'raw' / (hashlib.sha256(raw).hexdigest() + '.json')
            path.write_bytes(raw)
            self.reject_without_network()
            path.unlink()

    def test_world_raw_control_is_reparsed_with_detailed_summary(self):
        plan = {**PLAN, 'partitions': [{**slot, 'partner': '-'} for slot in PLAN['partitions']]}
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            receipt = archive.run_archived_batch(plan, self.root, KEY)
        self.assertEqual(len(receipt['rawObjects']), 2)
        self.assertTrue(all(entry['slot']['partner'] == '-' for entry in receipt['rawObjects']))
        self.assertEqual(archive.verify_archived_bundle(plan, self.root), receipt)

    def test_archive_directory_symlink_rejects_before_lock_or_network(self):
        destination = Path(self.temp.name) / 'outside'
        destination.mkdir()
        self.root.mkdir()
        try:
            (self.root / 'archive').symlink_to(destination, target_is_directory=True)
        except OSError:
            self.skipTest('The platform cannot create test directory symlinks')
        self.reject_without_network()
        self.assertEqual(list(destination.iterdir()), [])

    def test_valid_restore_is_byte_exact_and_requires_empty_destination(self):
        first = self.complete()
        files = snapshot(self.root)
        destination = Path(self.temp.name) / 'restored'
        archive.restore_archived_snapshot(PLAN, files, destination, KEY)
        self.assertEqual(snapshot(destination), files)
        self.assertEqual(archive.verify_archived_bundle(PLAN, destination), first)
        with self.assertRaises(SourceError):
            archive.restore_archived_snapshot(PLAN, files, destination, KEY)

    def test_restore_rejects_paths_orphans_and_secrets_before_any_write(self):
        self.complete()
        files = snapshot(self.root)
        payloads = [
            {'../secret.json': b'{}'},
            {'raw/' + 'a' * 64 + '.json': b'{}'},
            {'archive/' + 'a' * 64 + '.json': b'{}'},
            {'raw/' + 'b' * 64 + '.json': canonical([['unexpected'], [KEY]])},
        ]
        for index, extra in enumerate(payloads):
            with self.subTest(extra=next(iter(extra))):
                destination = Path(self.temp.name) / f'bad-{index}'
                with self.assertRaises(SourceError):
                    archive.restore_archived_snapshot(PLAN, files | extra, destination, KEY)
                self.assertFalse(destination.exists())

    def test_receipt_identity_inventory_and_active_pointer_are_strict(self):
        self.complete()
        files = snapshot(self.root)
        receipt_path = next(name for name in files if name.startswith('archive/') and name != 'archive/complete.json')
        receipt = json.loads(files[receipt_path])
        mutations = [
            {**receipt, 'schemaVersion': True},
            {**receipt, 'rawObjects': receipt['rawObjects'][:1]},
            {**receipt, 'publicationBlockers': []},
            {**receipt, 'privateWorkspace': 'must-not-exist'},
        ]
        for index, invalid in enumerate(mutations):
            altered = dict(files)
            if set(invalid) == set(receipt):
                invalid['receiptId'] = digest({k: v for k, v in invalid.items() if k != 'receiptId'})
                altered.pop(receipt_path)
                altered['archive/' + invalid['receiptId'] + '.json'] = canonical(invalid)
                altered['archive/complete.json'] = canonical({'receiptId': invalid['receiptId']})
            else:
                altered[receipt_path] = canonical(invalid)
            with self.subTest(index=index), self.assertRaises(SourceError):
                archive.restore_archived_snapshot(PLAN, altered, Path(self.temp.name) / f'changed-{index}', KEY)

    def test_current_receipt_must_include_historical_raw_objects(self):
        self.complete()
        with patch('pipeline.census.fetch_bytes', side_effect=lambda url: source_response(url, value='543')):
            current = archive.run_archived_batch(PLAN, self.root, KEY, refresh=True)
        files = snapshot(self.root)
        bundle = json.loads(files['bundles/' + current['bundleId'] + '.json'])
        active = {entry['candidateId'] for entry in bundle['partitions']}
        forged = copy.deepcopy(current)
        forged['rawObjects'] = [entry for entry in forged['rawObjects'] if any(identity in active for identity in entry['candidateIds'])]
        self.assertLess(len(forged['rawObjects']), len(current['rawObjects']))
        forged['receiptId'] = digest({k: v for k, v in forged.items() if k != 'receiptId'})
        files.pop('archive/' + current['receiptId'] + '.json')
        files['archive/' + forged['receiptId'] + '.json'] = canonical(forged)
        files['archive/complete.json'] = canonical({'receiptId': forged['receiptId']})
        destination = Path(self.temp.name) / 'stripped'
        # A previous valid receipt may omit later retained evidence during recovery.
        archive.restore_archived_snapshot(PLAN, files, destination, KEY)
        with self.assertRaises(SourceError):
            archive.verify_archived_bundle(PLAN, destination)
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Successful slots require no refetch')):
            repaired = archive.run_archived_batch(PLAN, destination, KEY)
        self.assertEqual(repaired['rawObjects'], current['rawObjects'])
        self.assertEqual(archive.verify_archived_bundle(PLAN, destination), repaired)

    def test_extra_valid_orphan_with_completed_old_generation_recovers_offline(self):
        first = self.complete()
        raw = next((self.root / 'raw').glob('*.json')).read_bytes()
        data = json.loads(raw)
        field = 'GEN_VAL_MO' if 'GEN_VAL_MO' in data[0] else 'ALL_VAL_MO'
        data[1][data[0].index(field)] = '2468'
        changed = canonical(data)
        orphan = self.root / 'raw' / (hashlib.sha256(changed).hexdigest() + '.json')
        orphan.write_bytes(changed)
        with self.assertRaises(SourceError):
            archive.verify_archived_bundle(PLAN, self.root)
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('The completed slots must remain cached')):
            expanded = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertNotEqual(expanded['receiptId'], first['receiptId'])
        self.assertEqual(expanded['bundleId'], first['bundleId'])
        self.assertEqual(sum(not entry['candidateIds'] for entry in expanded['rawObjects']), 1)
        self.assertEqual(orphan.read_bytes(), changed)
        self.assertEqual(archive.verify_archived_bundle(PLAN, self.root), expanded)

    def test_atomic_temporary_files_are_retained_but_ignored_as_evidence(self):
        first = self.complete()
        pending = self.root / 'objects' / '.pending-interrupted-write'
        pending.write_bytes(b'partial uncommitted bytes are not JSON')
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('The complete cache requires no source call')):
            restored = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertEqual(restored, first)
        self.assertEqual(pending.read_bytes(), b'partial uncommitted bytes are not JSON')
        self.assertEqual(archive.verify_archived_bundle(PLAN, self.root), first)
        unknown = self.root / 'objects' / 'unknown-state.json'
        unknown.write_bytes(b'{}')
        self.reject_without_network()

    def test_successful_journal_must_match_current_receipt_bundle(self):
        first = self.complete()
        with patch('pipeline.census.fetch_bytes', side_effect=lambda url: source_response(url, value='222')):
            archive.run_archived_batch(PLAN, self.root, KEY, refresh=True)
        # Simulate an old complete receipt retained during a newer completed batch.
        (self.root / 'archive' / 'complete.json').write_bytes(canonical({'receiptId': first['receiptId']}))
        with self.assertRaises(SourceError):
            archive.verify_archived_bundle(PLAN, self.root)
        with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('New successes are already durable')):
            recovered = archive.run_archived_batch(PLAN, self.root, KEY)
        self.assertNotEqual(recovered['receiptId'], first['receiptId'])

    def test_file_and_size_limits_apply_before_destination_writes(self):
        self.complete()
        files = snapshot(self.root)
        for extra in ({'raw/' + f'{index:064x}' + '.json': b'{}' for index in range(49)},
                      {'raw/' + f'{index:064x}' + '.json': b'x' * 65536 for index in range(33)},
                      {'raw/' + 'a' * 64 + '.json': b'x' * (65536 + 1)}):
            destination = Path(self.temp.name) / 'too-large'
            with self.assertRaises(SourceError):
                archive.restore_archived_snapshot(PLAN, files | extra, destination, KEY)
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
