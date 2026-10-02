"""Partner snapshots use a separate trusted workflow and bounded archive protocol."""
import contextlib
import io
import stat
import struct
import traceback
import unittest
import zipfile
from unittest.mock import patch

from pipeline import restore
from pipeline.tests.test_restore import (
    BUNDLE, COMPLETE as BATCH_COMPLETE, FakeResponse, FakeTransport, OBJECT,
    PROGRESS as BATCH_PROGRESS, REPOSITORY, RUN_ID, STORAGE_URL, TOKEN,
    artifact_metadata, make_zip, replies, run_metadata,
)


RAW = 'raw/' + 'a' * 64 + '.json'
SCAN = 'scans/' + 'b' * 64 + '.json'
RECEIPT = 'receipts/' + 'c' * 64 + '.json'
PARTNER_FILES = [(RAW, b'[]'), (SCAN, b'{}'), (RECEIPT, b'{}'),
                 ('progress.json', b'{}'), ('complete.json', b'{}')]


def partner_replies(data=None, *, run=None, artifacts=None, **changes):
    data = make_zip(PARTNER_FILES) if data is None else data
    return replies(
        data,
        run=run_metadata(path='.github/workflows/census-partners.yml') if run is None else run,
        artifacts={'total_count': 1, 'artifacts': [artifact_metadata(data, name=f'census-partners-{RUN_ID}')]} if artifacts is None else artifacts,
        **changes,
    )


class PartnerRestoreTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(restore, 'fetch_partner_snapshot', None)),
                        'The separately trusted partner snapshot transport is missing')

    def fetch(self, responses, **inputs):
        transport = FakeTransport(responses)
        with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection):
            result = restore.fetch_partner_snapshot(inputs.get('repository', REPOSITORY),
                                                    inputs.get('run_id', RUN_ID),
                                                    inputs.get('token', TOKEN))
        return result, transport

    def reject(self, responses, **inputs):
        transport = FakeTransport(responses)
        logs = io.StringIO()
        with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection), \
                contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
            with self.assertRaises(restore.SnapshotError) as raised:
                restore.fetch_partner_snapshot(inputs.get('repository', REPOSITORY),
                                               inputs.get('run_id', RUN_ID),
                                               inputs.get('token', TOKEN))
        diagnostic = str(raised.exception) + logs.getvalue() + ''.join(traceback.format_exception(raised.exception))
        for secret in (TOKEN, STORAGE_URL, 'private-signature', 'https://'):
            self.assertNotIn(secret, diagnostic)
        self.assertIsNone(raised.exception.__context__)
        self.assertTrue(all(connection.closed for connection in transport.connections))
        return transport

    def reject_before_members_open(self, data):
        with patch('pipeline.restore.zipfile.ZipFile.open', side_effect=AssertionError('Member was opened')) as opened:
            self.reject(partner_replies(data))
        opened.assert_not_called()

    def test_fixed_main_partner_workflow_returns_only_new_protocol_members(self):
        result, transport = self.fetch(partner_replies())
        self.assertEqual(result, dict(PARTNER_FILES))
        self.assertEqual([(host, method, target) for host, method, target, _ in transport.requests], [
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/runs/123'),
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/runs/123/artifacts?per_page=100'),
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/artifacts/456/zip'),
            ('artifact.blob.core.windows.net', 'GET', '/results/batch.zip?sig=private-signature'),
        ])
        for _, _, _, headers in transport.requests[:3]:
            self.assertEqual(headers['Authorization'], 'Bearer ' + TOKEN)
        self.assertNotIn('authorization', {key.lower() for key in transport.requests[-1][3]})
        self.assertTrue(all(connection.closed for connection in transport.connections))

    def test_completed_failure_run_can_supply_partial_recovery_evidence(self):
        data = make_zip([(RAW, b'[]'), ('progress.json', b'{"state":"failed"}')])
        result, _ = self.fetch(partner_replies(data, run=run_metadata(
            path='.github/workflows/census-partners.yml', conclusion='failure')))
        self.assertEqual(result, {RAW: b'[]', 'progress.json': b'{"state":"failed"}'})

    def test_rejects_wrong_run_provenance_before_artifact_lookup(self):
        for changes in (
            {'id': True}, {'id': RUN_ID + 1}, {'repository': {'full_name': 'attacker/private-trade'}},
            {'repository': None}, {'event': 'pull_request'}, {'event': 'pull_request_target'},
            {'event': 'push'}, {'head_branch': 'feat/census-partner-discovery'},
            {'path': '.github/workflows/census-batch.yml'}, {'path': '.github/workflows/census-archive.yml'},
            {'path': '.github/workflows/census-partners.yml@main'}, {'status': 'in_progress'},
        ):
            with self.subTest(changes=changes):
                metadata = run_metadata(path='.github/workflows/census-partners.yml', **changes) if 'path' not in changes else run_metadata(**changes)
                transport = self.reject(partner_replies(run=metadata))
                self.assertEqual(len(transport.requests), 1)

    def test_rejects_protocol_confusion_in_artifact_name(self):
        data = make_zip(PARTNER_FILES)
        for name in ('census-batch-123', 'census-archive-123', 'census-partners-124',
                     'census-partners-123-suffix', 'census-partners-True'):
            with self.subTest(name=name):
                artifacts = {'total_count': 1, 'artifacts': [artifact_metadata(data, name=name)]}
                transport = self.reject(partner_replies(data, artifacts=artifacts))
                self.assertEqual(len(transport.requests), 2)

    def test_requires_one_unexpired_sized_sha256_artifact(self):
        data = make_zip(PARTNER_FILES)
        for changes in (
            {'id': True}, {'id': 0}, {'expired': True}, {'expired': 0},
            {'size_in_bytes': True}, {'size_in_bytes': 0}, {'size_in_bytes': 2 * 1024 * 1024 + 1},
            {'digest': None}, {'digest': 'md5:' + 'a' * 64}, {'digest': 'sha256:' + 'A' * 64},
        ):
            with self.subTest(changes=changes):
                artifacts = {'total_count': 1, 'artifacts': [artifact_metadata(data, name=f'census-partners-{RUN_ID}', **changes)]}
                transport = self.reject(partner_replies(data, artifacts=artifacts))
                self.assertEqual(len(transport.requests), 2)
        for artifacts in (
            {'total_count': 0, 'artifacts': []},
            {'total_count': True, 'artifacts': []},
            {'total_count': 2, 'artifacts': []},
            {'total_count': 1, 'artifacts': None},
            {'total_count': 1, 'artifacts': [artifact_metadata(data), artifact_metadata(data)]},
        ):
            with self.subTest(artifacts=artifacts):
                transport = self.reject(partner_replies(data, artifacts=artifacts))
                self.assertEqual(len(transport.requests), 2)

    def test_ignores_metadata_download_url_and_preserves_signed_storage_target(self):
        data = make_zip(PARTNER_FILES)
        artifacts = {'total_count': 1, 'artifacts': [artifact_metadata(
            data, name=f'census-partners-{RUN_ID}', archive_download_url='https://attacker.example/' + TOKEN)]}
        _, transport = self.fetch(partner_replies(
            data, artifacts=artifacts,
            location='https://artifact.actions.githubusercontent.com/a%2Fb/partners.zip?sig=private-signature&x=1'))
        self.assertEqual(transport.requests[2][2], '/repos/example/private-trade/actions/artifacts/456/zip')
        self.assertEqual(transport.requests[-1][2], '/a%2Fb/partners.zip?sig=private-signature&x=1')
        self.assertNotIn('authorization', {key.lower() for key in transport.requests[-1][3]})

    def test_rejects_unsafe_storage_redirects_before_contacting_storage(self):
        for location in (
            'http://artifact.blob.core.windows.net/a.zip', 'https://attacker.example/a.zip',
            'https://artifact.blob.core.windows.net.attacker.example/a.zip',
            'https://blob.core.windows.net/a.zip', 'https://api.github.com/a.zip',
            'https://user@artifact.blob.core.windows.net/a.zip',
            'https://artifact.blob.core.windows.net:0443/a.zip',
            'https://artifact.blob.core.windows.net/a.zip#fragment',
            'https://artifact.blob.core.windows.net/a.zip\n', None,
        ):
            with self.subTest(location=location):
                transport = self.reject(partner_replies(location=location))
                self.assertEqual(len(transport.requests), 3)

    def test_does_not_follow_a_storage_redirect(self):
        transport = self.reject(partner_replies(blob=FakeResponse(
            status=302, headers={'Location': 'https://attacker.example/' + TOKEN})))
        self.assertEqual(len(transport.requests), 4)

    def test_checks_digest_before_opening_members(self):
        data = make_zip(PARTNER_FILES)
        artifacts = {'total_count': 1, 'artifacts': [artifact_metadata(
            data, name=f'census-partners-{RUN_ID}', digest='sha256:' + '0' * 64)]}
        with patch('pipeline.restore.zipfile.ZipFile.open', side_effect=AssertionError('Member was opened')) as opened:
            self.reject(partner_replies(data, artifacts=artifacts))
        opened.assert_not_called()

    def test_accepts_only_partner_directory_prefixes(self):
        data = make_zip([('raw/', b''), ('scans/', b''), ('receipts/', b'')] + PARTNER_FILES)
        result, _ = self.fetch(partner_replies(data))
        self.assertEqual(result, dict(PARTNER_FILES))

    def test_rejects_legacy_and_archive_paths_before_any_decompression(self):
        for name in (OBJECT, BUNDLE, BATCH_PROGRESS, BATCH_COMPLETE, 'archive/' + 'd' * 64 + '.json',
                     'archive/complete.json', 'objects/', 'archive/'):
            with self.subTest(name=name):
                self.reject_before_members_open(make_zip([(RAW, b'[]'), (name, b'{}' if not name.endswith('/') else b'')]))

    def test_rejects_traversal_ambiguous_and_extra_paths_before_any_decompression(self):
        for name in (
            '../' + RAW, '/' + RAW, 'raw/../' + RAW, RAW.replace('/', '\\'),
            'raw/' + 'A' * 64 + '.json', 'scans/' + 'b' * 63 + '.json',
            'receipts/' + 'c' * 64 + '.json.exe', 'scans/nested/', 'unknown/',
            'raw/nested/' + 'a' * 64 + '.json', 'progress.json/extra', 'complete.json.bak',
            '.pending-evidence.json', '.writer.lock', 'secret.json',
        ):
            with self.subTest(name=name):
                self.reject_before_members_open(make_zip([(RAW, b'[]'), (name, b'{}' if not name.endswith('/') else b'')]))

    def test_rejects_duplicates_before_any_decompression(self):
        for entries in (
            [(RAW, b'[]'), (RAW, b'{}')],
            [(RAW, b'[]'), ('raw/', b''), ('raw/', b'')],
            [(RAW, b'[]'), ('complete.json', b'{}'), ('complete.json', b'{}')],
        ):
            with self.subTest(entries=[name for name, _ in entries]):
                self.reject_before_members_open(make_zip(entries))

    def test_rejects_symlinks_and_other_member_types_before_any_decompression(self):
        for kind in (stat.S_IFLNK, stat.S_IFDIR, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK):
            with self.subTest(kind=kind):
                entry = zipfile.ZipInfo(SCAN)
                entry.create_system = 3
                entry.external_attr = (kind | 0o777) << 16
                self.reject_before_members_open(make_zip([(RAW, b'[]'), (entry, b'{}')]))
        for kind in (stat.S_IFLNK, stat.S_IFREG):
            with self.subTest(directory_kind=kind):
                entry = zipfile.ZipInfo('raw/')
                entry.create_system = 3
                entry.external_attr = (kind | 0o777) << 16
                self.reject_before_members_open(make_zip([(RAW, b'[]'), (entry, b'')]))

    def test_rejects_nonempty_directories_before_any_decompression(self):
        self.reject_before_members_open(make_zip([(RAW, b'[]'), ('raw/', b'not-empty')]))

    def test_rejects_encrypted_or_unsupported_compression_before_any_decompression(self):
        data = bytearray(make_zip([(RAW, b'[]')]))
        local = data.index(b'PK\x03\x04')
        central = data.index(b'PK\x01\x02')
        for offset in (local + 6, central + 8):
            struct.pack_into('<H', data, offset, struct.unpack_from('<H', data, offset)[0] | 1)
        self.reject_before_members_open(bytes(data))
        entry = zipfile.ZipInfo(RAW)
        entry.compress_type = zipfile.ZIP_BZIP2
        self.reject_before_members_open(make_zip([(entry, b'[]')]))

    def test_rejects_null_terminated_names_before_any_decompression(self):
        data = bytearray(make_zip([(RAW, b'[]')]))
        needle = RAW.encode()
        positions = [index for index in range(len(data)) if data.startswith(needle, index)]
        self.assertEqual(len(positions), 2)
        for index in positions:
            data[index + len(needle) - 1] = 0
        self.reject_before_members_open(bytes(data))

    def test_accepts_members_above_legacy_limit_through_512_kib(self):
        for length in (64 * 1024 + 1, 512 * 1024):
            with self.subTest(length=length):
                content = b'x' * length
                result, _ = self.fetch(partner_replies(make_zip([(RAW, content)])))
                self.assertEqual(result, {RAW: content})

    def test_rejects_members_over_512_kib_before_any_decompression(self):
        self.reject_before_members_open(make_zip([(RAW, b'[]'), (SCAN, b'x' * (512 * 1024 + 1))]))

    def test_accepts_two_mib_unpacked_and_rejects_more_before_any_decompression(self):
        entries = [('raw/' + f'{index:064x}' + '.json', b'x' * (512 * 1024)) for index in range(4)]
        result, _ = self.fetch(partner_replies(make_zip(entries)))
        self.assertEqual(len(result), 4)
        self.assertEqual(sum(map(len, result.values())), 2 * 1024 * 1024)
        self.reject_before_members_open(make_zip(entries + [(SCAN, b'x')]))

    def test_accepts_twenty_files_and_rejects_twenty_one_before_any_decompression(self):
        entries = [('raw/' + f'{index:064x}' + '.json', b'[]') for index in range(20)]
        directories = [('raw/', b''), ('scans/', b''), ('receipts/', b'')]
        result, _ = self.fetch(partner_replies(make_zip(directories + entries)))
        self.assertEqual(len(result), 20)
        self.reject_before_members_open(make_zip(entries + [(SCAN, b'{}')]))

    def test_rejects_more_than_twenty_four_zip_entries_before_any_decompression(self):
        entries = [('raw/' + f'{index:064x}' + '.json', b'[]') for index in range(25)]
        self.reject_before_members_open(make_zip(entries))

    def test_bounds_metadata_and_compressed_archive_before_decompression(self):
        for phase, maximum in ((0, 64 * 1024), (1, 64 * 1024), (3, 2 * 1024 * 1024)):
            with self.subTest(phase=phase):
                responses = partner_replies()
                oversized = FakeResponse(body=b'x' * (maximum + 1024), headers={'Content-Type': 'application/json'})
                responses[phase] = oversized
                with patch('pipeline.restore.zipfile.ZipFile.open', side_effect=AssertionError('Member was opened')) as opened:
                    self.reject(responses)
                opened.assert_not_called()
                self.assertLessEqual(oversized.read_bytes, maximum + 1)
                responses = partner_replies()
                declared = FakeResponse(body=b'{}', headers={'Content-Type': 'application/json', 'Content-Length': str(maximum + 1)})
                responses[phase] = declared
                self.reject(responses)
                self.assertEqual(declared.read_bytes, 0)

    def test_normalized_and_archived_modes_reject_partner_workflow_and_members(self):
        for fetcher in (restore.fetch_snapshot, restore.fetch_archived_snapshot):
            for responses in (partner_replies(),):
                with self.subTest(fetcher=fetcher.__name__), \
                        patch('pipeline.restore.http.client.HTTPSConnection', side_effect=FakeTransport(responses).connection):
                    with self.assertRaises(restore.SnapshotError):
                        fetcher(REPOSITORY, RUN_ID, TOKEN)
        for archived in (False, True):
            for name in (SCAN, RECEIPT, 'progress.json', 'complete.json', 'scans/', 'receipts/'):
                with self.subTest(archived=archived, name=name), self.assertRaises(ValueError):
                    restore._members(make_zip([(name, b'' if name.endswith('/') else b'{}')]), archived=archived)
            path = RAW if archived else OBJECT
            with self.subTest(archived=archived, oversized=path), self.assertRaises(ValueError):
                restore._members(make_zip([(path, b'x' * (64 * 1024 + 1))]), archived=archived)
        with self.assertRaises(ValueError):
            restore._members(make_zip([(RAW, b'[]')]))

    def test_legacy_private_keywords_keep_exact_paths_and_entry_limits(self):
        legacy = [(OBJECT, b'{}'), (BUNDLE, b'{}'), (BATCH_PROGRESS, b'{}'), (BATCH_COMPLETE, b'{}')]
        self.assertEqual(restore._members(make_zip(legacy)), dict(legacy))
        archived = legacy + [(RAW, b'[]'), ('archive/' + 'd' * 64 + '.json', b'{}'), ('archive/complete.json', b'{}')]
        self.assertEqual(restore._members(make_zip(archived), archived=True), dict(archived))
        entries = [('raw/' + f'{index:064x}' + '.json', b'[]') for index in range(48)]
        self.assertEqual(len(restore._members(make_zip(entries), archived=True)), 48)
        with self.assertRaises(ValueError):
            restore._members(make_zip(entries + [('raw/', b'')]), archived=True)

    def test_rejects_unsafe_inputs_before_connecting(self):
        for inputs in ({'repository': '../private-trade'}, {'repository': 'owner/repo?token=' + TOKEN},
                       {'run_id': True}, {'run_id': 0}, {'token': ''}, {'token': TOKEN + '\r\n'}):
            with self.subTest(inputs=inputs):
                transport = self.reject([], **inputs)
                self.assertEqual(transport.requests, [])


if __name__ == '__main__':
    unittest.main()
