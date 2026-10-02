"""Separate archive transport provenance never widens the legacy restore protocol."""
import unittest
from unittest.mock import patch

from pipeline import restore
from pipeline.tests.test_restore import (
    FakeTransport, REPOSITORY, RUN_ID, TOKEN, OBJECT, artifact_metadata,
    make_zip, replies, run_metadata,
)

RAW = 'raw/' + 'e' * 64 + '.json'
RECEIPT = 'archive/' + 'f' * 64 + '.json'


class ArchivedRestoreTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(restore, 'fetch_archived_snapshot'), 'The separately trusted archive transport is missing')

    def fetch(self, responses):
        transport = FakeTransport(responses)
        with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection):
            result = restore.fetch_archived_snapshot(REPOSITORY, RUN_ID, TOKEN)
        return result, transport

    def archived_replies(self, data, **changes):
        return replies(data, run=run_metadata(path='.github/workflows/census-archive.yml', **changes),
                       artifacts={'total_count': 1, 'artifacts': [artifact_metadata(data, name=f'census-archive-{RUN_ID}')]})

    def test_fixed_archive_workflow_and_artifact_accept_raw_and_receipt_paths(self):
        files = [(OBJECT, b'{}'), (RAW, b'[]'), (RECEIPT, b'{}'), ('archive/complete.json', b'{}')]
        result, transport = self.fetch(self.archived_replies(make_zip(files)))
        self.assertEqual(result, dict(files))
        self.assertNotIn('Authorization', transport.requests[-1][3])

    def test_legacy_restore_rejects_archive_workflow_and_raw_members(self):
        archive_data = make_zip([(RAW, b'[]')])
        for responses in (self.archived_replies(archive_data), replies(archive_data)):
            with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=FakeTransport(responses).connection):
                with self.assertRaises(restore.SnapshotError):
                    restore.fetch_snapshot(REPOSITORY, RUN_ID, TOKEN)

    def test_archive_restore_rejects_legacy_workflow_and_artifact(self):
        data = make_zip([(RAW, b'[]')])
        cases = [replies(data), replies(data, run=run_metadata(path='.github/workflows/census-archive.yml'))]
        for responses in cases:
            with self.assertRaises(restore.SnapshotError):
                self.fetch(responses)

    def test_archive_restore_keeps_main_and_manual_run_requirements(self):
        for changes in ({'head_branch': 'feature'}, {'event': 'pull_request'}, {'status': 'in_progress'}):
            with self.subTest(changes=changes), self.assertRaises(restore.SnapshotError):
                self.fetch(self.archived_replies(make_zip([(RAW, b'[]')]), **changes))

    def test_new_directories_are_allowed_but_nested_or_ambiguous_paths_fail(self):
        result, _ = self.fetch(self.archived_replies(make_zip([('raw/', b''), ('archive/', b''), (RAW, b'[]')])))
        self.assertEqual(result, {RAW: b'[]'})
        for name in ('raw/../' + RAW, 'archive/nested/', 'archive/unknown.json', RAW.replace('/', '\\'),
                     'raw/' + 'A' * 64 + '.json', 'archive/complete.json/extra'):
            with self.subTest(name=name), self.assertRaises(restore.SnapshotError):
                self.fetch(self.archived_replies(make_zip([(name, b'[]')])))

    def test_archive_limits_and_digest_still_apply(self):
        for data in (make_zip([(RAW, b'x' * (65536 + 1))]),
                     make_zip([('raw/' + f'{index:064x}' + '.json', b'[]') for index in range(49)])):
            with self.assertRaises(restore.SnapshotError):
                self.fetch(self.archived_replies(data))
        data = make_zip([(RAW, b'[]')])
        metadata = artifact_metadata(data, name=f'census-archive-{RUN_ID}', digest='sha256:' + '0' * 64)
        with self.assertRaises(restore.SnapshotError):
            self.fetch(replies(data, run=run_metadata(path='.github/workflows/census-archive.yml'),
                               artifacts={'total_count': 1, 'artifacts': [metadata]}))


if __name__ == '__main__':
    unittest.main()
