"""Private snapshot transport tests use fabricated HTTPS replies and archives."""
import contextlib
import hashlib
import http.client
import io
import json
import socket
import stat
import struct
import traceback
import unittest
import warnings
import zipfile
from unittest.mock import patch

try:
    from pipeline import restore
except ImportError:
    restore = None


REPOSITORY = 'example/private-trade'
RUN_ID = 123
TOKEN = 'canary-private-github-secret'
STORAGE_URL = 'https://artifact.blob.core.windows.net/results/batch.zip?sig=private-signature'
OBJECT = 'objects/' + 'a' * 64 + '.json'
BUNDLE = 'bundles/' + 'b' * 64 + '.json'
PROGRESS = 'batches/' + 'c' * 64 + '/progress.json'
COMPLETE = 'batches/' + 'c' * 64 + '/complete.json'


def make_zip(entries=None):
    output = io.BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        warnings.simplefilter('ignore', UserWarning)
        for name, contents in entries if entries is not None else [(OBJECT, b'{"value":1}'), (PROGRESS, b'{"state":"partial"}')]:
            if isinstance(name, str) and '\\' in name:
                # ZipInfo normally converts Windows separators when creating a ZIP;
                # preserve this deliberately malicious spelling on the wire.
                entry = zipfile.ZipInfo(name)
                entry.filename = name
                entry.orig_filename = name
                name = entry
            archive.writestr(name, contents)
    return output.getvalue()


def run_metadata(**changes):
    return {
        'id': RUN_ID, 'repository': {'id': 42, 'full_name': REPOSITORY},
        'event': 'workflow_dispatch', 'head_branch': 'main',
        'path': '.github/workflows/census-batch.yml', 'status': 'completed',
        'conclusion': 'failure', 'head_sha': 'd' * 40,
        **changes,
    }


def artifact_metadata(archive, **changes):
    return {
        'id': 456, 'name': f'census-batch-{RUN_ID}', 'expired': False,
        'size_in_bytes': len(archive), 'digest': 'sha256:' + hashlib.sha256(archive).hexdigest(),
        'archive_download_url': f'https://api.github.com/repos/{REPOSITORY}/actions/artifacts/456/zip',
        'workflow_run': {'id': RUN_ID, 'repository_id': 42, 'head_repository_id': 42,
                         'head_branch': 'main', 'head_sha': 'd' * 40},
        **changes,
    }


class FakeResponse:
    def __init__(self, status=200, body=b'', headers=None, failure=None):
        self.status = status
        self.body = io.BytesIO(body)
        self.headers = {key.lower(): value for key, value in (headers or {}).items()}
        self.failure = failure
        self.closed = False
        self.read_bytes = 0
        self.read_sizes = []

    def getheader(self, name, default=None):
        return self.headers.get(name.lower(), default)

    def read1(self, size):
        if self.failure:
            raise self.failure
        self.read_sizes.append(size)
        data = self.body.read(size)
        self.read_bytes += len(data)
        return data

    def close(self):
        self.closed = True


def json_reply(data):
    return FakeResponse(body=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})


class FakeSocket:
    def __init__(self):
        self.timeouts = []
        self.shutdown_calls = []

    def settimeout(self, seconds):
        self.timeouts.append(seconds)

    def shutdown(self, how):
        self.shutdown_calls.append(how)


class FakeConnection:
    def __init__(self, transport, host, timeout):
        self.transport = transport
        self.host = host
        self.timeout = timeout
        self.sock = FakeSocket()
        self.closed = False

    def connect(self):
        if self.transport.connect_failure:
            raise self.transport.connect_failure

    def request(self, method, target, *, headers):
        self.transport.requests.append((self.host, method, target, dict(headers)))

    def getresponse(self):
        if not self.transport.responses:
            raise AssertionError('Unexpected extra request')
        reply = self.transport.responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def close(self):
        self.closed = True


class FakeTransport:
    def __init__(self, responses, *, connect_failure=None):
        self.responses = list(responses)
        self.connect_failure = connect_failure
        self.requests = []
        self.connections = []

    def connection(self, host, timeout):
        connection = FakeConnection(self, host, timeout)
        self.connections.append(connection)
        return connection


def replies(archive=None, *, run=None, artifacts=None, location=STORAGE_URL, blob=None):
    archive = make_zip() if archive is None else archive
    return [
        json_reply(run_metadata() if run is None else run),
        json_reply({'total_count': 1, 'artifacts': [artifact_metadata(archive)]} if artifacts is None else artifacts),
        FakeResponse(status=302, headers={'Location': location}),
        FakeResponse(body=archive) if blob is None else blob,
    ]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(restore, 'The bounded snapshot transport has not been implemented')

    def fetch(self, responses, **inputs):
        transport = FakeTransport(responses)
        with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection):
            result = restore.fetch_snapshot(inputs.get('repository', REPOSITORY), inputs.get('run_id', RUN_ID), inputs.get('token', TOKEN))
        return result, transport

    def reject(self, responses, **inputs):
        transport = FakeTransport(responses)
        logs = io.StringIO()
        with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection), contextlib.redirect_stderr(logs), contextlib.redirect_stdout(logs):
            with self.assertRaises(restore.SnapshotError) as raised:
                restore.fetch_snapshot(inputs.get('repository', REPOSITORY), inputs.get('run_id', RUN_ID), inputs.get('token', TOKEN))
        diagnostic = str(raised.exception) + logs.getvalue() + ''.join(traceback.format_exception(raised.exception))
        for secret in [TOKEN, 'private-signature', 'https://', STORAGE_URL]:
            self.assertNotIn(secret, diagnostic)
        self.assertIsNone(raised.exception.__context__)
        self.assertTrue(all(connection.closed for connection in transport.connections))
        return transport

    def test_returns_only_member_bytes_and_authenticates_only_the_api(self):
        archive = make_zip([(OBJECT, b'{"value":1}'), (BUNDLE, b'{}'), (PROGRESS, b'{}'), (COMPLETE, b'{}')])
        result, transport = self.fetch(replies(archive))
        self.assertEqual(result, {OBJECT: b'{"value":1}', BUNDLE: b'{}', PROGRESS: b'{}', COMPLETE: b'{}'})
        self.assertEqual([(host, method, target) for host, method, target, _ in transport.requests], [
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/runs/123'),
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/runs/123/artifacts?per_page=100'),
            ('api.github.com', 'GET', '/repos/example/private-trade/actions/artifacts/456/zip'),
            ('artifact.blob.core.windows.net', 'GET', '/results/batch.zip?sig=private-signature'),
        ])
        for _, _, _, headers in transport.requests[:3]:
            self.assertEqual(headers['Authorization'], 'Bearer ' + TOKEN)
        self.assertNotIn('authorization', {key.lower() for key in transport.requests[-1][3]})
        self.assertTrue(all(connection.timeout == 5 for connection in transport.connections))
        self.assertTrue(all(0 < timeout <= 30 for connection in transport.connections for timeout in connection.sock.timeouts))
        self.assertTrue(all(connection.sock.timeouts and connection.closed for connection in transport.connections))

    def test_rejects_unsafe_inputs_before_connecting(self):
        for inputs in [
            {'repository': '../private-trade'}, {'repository': 'owner/repo?token=' + TOKEN},
            {'repository': 'owner/repo/more'}, {'repository': 'owner/repo\n'},
            {'repository': True}, {'repository': 'owner/-'}, {'repository': 'owner/..'},
            {'run_id': True}, {'run_id': 0}, {'run_id': -1}, {'run_id': '123'},
            {'token': ''}, {'token': TOKEN + '\r\nBad: injected'}, {'token': None},
        ]:
            with self.subTest(inputs=inputs):
                transport = self.reject([], **inputs)
                self.assertEqual(transport.requests, [])

    def test_rejects_wrong_run_provenance_before_artifact_lookup(self):
        for changes in [
            {'id': True}, {'id': 124}, {'repository': {'full_name': 'attacker/private-trade'}},
            {'repository': {'full_name': REPOSITORY + '/' + TOKEN}}, {'repository': None},
            {'event': 'pull_request'}, {'event': 'push'}, {'head_branch': 'feat/census-batches'},
            {'path': '.github/workflows/other.yml'}, {'status': 'in_progress'},
        ]:
            with self.subTest(changes=changes):
                transport = self.reject(replies(run=run_metadata(**changes)))
                self.assertEqual(len(transport.requests), 1)

    def test_requires_one_exact_nonexpired_artifact_and_a_sha256_digest(self):
        archive = make_zip()
        for changes in [
            {'id': True}, {'id': 0}, {'id': '456'}, {'expired': True}, {'expired': 0},
            {'name': 'census-batch-123-suffix'}, {'name': 'census-batch-124'},
            {'size_in_bytes': True}, {'size_in_bytes': -1}, {'size_in_bytes': 0},
            {'size_in_bytes': 2 * 1024 * 1024 + 1}, {'digest': None},
            {'digest': 'md5:' + 'a' * 64}, {'digest': 'sha256:' + 'A' * 64},
            {'digest': 'sha256:' + 'a' * 63},
        ]:
            with self.subTest(changes=changes):
                metadata = {'total_count': 1, 'artifacts': [artifact_metadata(archive, **changes)]}
                transport = self.reject(replies(archive, artifacts=metadata))
                self.assertEqual(len(transport.requests), 2)
        for metadata in [
            {'total_count': 0, 'artifacts': []},
            {'total_count': True, 'artifacts': [artifact_metadata(archive)]},
            {'total_count': 2, 'artifacts': [artifact_metadata(archive)]},
            {'total_count': 2, 'artifacts': [artifact_metadata(archive), artifact_metadata(archive)]},
            {'total_count': 1, 'artifacts': None},
        ]:
            with self.subTest(metadata=metadata):
                self.reject(replies(archive, artifacts=metadata))

    def test_ignores_metadata_download_url_and_builds_fixed_api_path(self):
        archive = make_zip()
        metadata = {'total_count': 1, 'artifacts': [artifact_metadata(archive, archive_download_url='https://attacker.example/' + TOKEN)]}
        _, transport = self.fetch(replies(archive, artifacts=metadata))
        self.assertEqual(transport.requests[2][2], '/repos/example/private-trade/actions/artifacts/456/zip')

    def test_rejects_wrong_checksum_before_returning_members(self):
        archive = make_zip()
        metadata = {'total_count': 1, 'artifacts': [artifact_metadata(archive, digest='sha256:' + '0' * 64)]}
        self.reject(replies(archive, artifacts=metadata))

    def test_accepts_only_storage_subdomains_and_does_not_forward_credentials(self):
        for host in ['artifact.blob.core.windows.net', 'artifact.actions.githubusercontent.com', 'artifact.githubusercontent.com', 'actions.githubusercontent.com']:
            with self.subTest(host=host):
                result, transport = self.fetch(replies(location='https://' + host + ':443/archive.zip?sig=private-signature'))
                self.assertIn(OBJECT, result)
                self.assertEqual(transport.requests[-1][0], host)
                self.assertNotIn('authorization', {key.lower() for key in transport.requests[-1][3]})

    def test_rejects_nonallowlisted_and_ambiguous_redirects_without_contacting_storage(self):
        for location in [
            'http://artifact.blob.core.windows.net/a.zip', 'https://attacker.example/a.zip',
            'https://artifact.blob.core.windows.net.attacker.example/a.zip',
            'https://blob.core.windows.net/a.zip',
            'https://githubusercontent.com/a.zip', 'https://api.github.com/a.zip',
            'https://user@artifact.blob.core.windows.net/a.zip',
            'https://artifact.blob.core.windows.net:444/a.zip',
            'https://artifact.blob.core.windows.net/a.zip#fragment',
            'https://artifact.blob.core.windows.net/a.zip\n',
            'https://artifact.blob.core.windows.net./a.zip', None,
        ]:
            with self.subTest(location=location):
                transport = self.reject(replies(location=location))
                self.assertEqual(len(transport.requests), 3)

    def test_does_not_follow_a_second_redirect(self):
        transport = self.reject(replies(blob=FakeResponse(status=302, headers={'Location': 'https://attacker.example/' + TOKEN})))
        self.assertEqual(len(transport.requests), 4)

    def test_rejects_wrong_http_status_at_every_phase(self):
        for index, status in [(0, 302), (0, 403), (1, 500), (2, 200), (2, 307), (3, 403), (3, 500)]:
            with self.subTest(index=index, status=status):
                responses = replies()
                responses[index] = FakeResponse(status=status, body=(TOKEN + STORAGE_URL).encode())
                transport = self.reject(responses)
                self.assertEqual(len(transport.requests), index + 1)

    def test_rejects_oversized_or_inconsistent_content_length_before_reading(self):
        for index, maximum in [(0, 64 * 1024), (1, 64 * 1024), (3, 2 * 1024 * 1024)]:
            for declared in [str(maximum + 1), '-1', 'invalid-' + TOKEN, '9' * 5000]:
                with self.subTest(index=index, declared=declared[:20]):
                    responses = replies()
                    response = FakeResponse(body=b'{}', headers={'Content-Length': declared, 'Content-Type': 'application/json'})
                    responses[index] = response
                    self.reject(responses)
                    self.assertEqual(response.read_bytes, 0)
        responses = replies()
        responses[0].headers['content-length'] = '999'
        self.reject(responses)

    def test_bounds_streamed_metadata_and_archive_without_content_length(self):
        for index, maximum in [(0, 64 * 1024), (1, 64 * 1024), (3, 2 * 1024 * 1024)]:
            with self.subTest(index=index):
                responses = replies()
                response = FakeResponse(body=b'x' * (maximum + 1024), headers={'Content-Type': 'application/json'})
                responses[index] = response
                self.reject(responses)
                self.assertLessEqual(response.read_bytes, maximum + 1)
                self.assertTrue(all(0 < size <= 65536 for size in response.read_sizes))

    def test_rejects_encoded_non_json_and_malformed_metadata(self):
        for response in [
            FakeResponse(body=b'{}', headers={'Content-Type': 'application/json', 'Content-Encoding': 'gzip'}),
            FakeResponse(body=b'{}', headers={'Content-Type': 'text/html'}),
            FakeResponse(body=b'not-json-' + TOKEN.encode(), headers={'Content-Type': 'application/json'}),
            json_reply([]),
            FakeResponse(body=b'{"id":123,"id":123}', headers={'Content-Type': 'application/json'}),
        ]:
            with self.subTest(body=response.body.getvalue()[:30]):
                responses = replies()
                responses[0] = response
                self.reject(responses)

    def test_redacts_transport_errors_and_closes_connections(self):
        for failure in [socket.timeout(TOKEN + STORAGE_URL), OSError(TOKEN), http.client.HTTPException(STORAGE_URL)]:
            for phase in ['connect', 'headers', 'body']:
                with self.subTest(phase=phase, failure=type(failure).__name__):
                    responses = replies()
                    transport = FakeTransport(responses, connect_failure=failure if phase == 'connect' else None)
                    if phase == 'headers':
                        transport.responses[0] = failure
                    if phase == 'body':
                        transport.responses[0].failure = failure
                    with patch('pipeline.restore.http.client.HTTPSConnection', side_effect=transport.connection):
                        with self.assertRaises(restore.SnapshotError) as raised:
                            restore.fetch_snapshot(REPOSITORY, RUN_ID, TOKEN)
                    self.assertNotIn(TOKEN, ''.join(traceback.format_exception(raised.exception)))
                    self.assertNotIn('https://', str(raised.exception))
                    self.assertIsNone(raised.exception.__context__)
                    self.assertTrue(all(connection.closed for connection in transport.connections))

    def test_rejects_unknown_or_traversing_archive_paths(self):
        for name in ['../' + OBJECT, '/' + OBJECT, 'objects/../' + OBJECT, OBJECT.replace('/', '\\'),
                     'objects/' + 'a' * 63 + '.json', 'objects/' + 'A' * 64 + '.json',
                     'objects/' + 'a' * 64 + '.json.exe', 'batch.json', 'batches/' + 'c' * 64 + '/secret.json',
                     'unknown/', 'batches/invalid/', 'objects/nested/']:
            with self.subTest(name=name):
                self.reject(replies(make_zip([(name, b'{}')])))

    def test_ignores_only_valid_directory_prefixes(self):
        archive = make_zip([('objects/', b''), ('bundles/', b''), ('batches/', b''), ('batches/' + 'c' * 64 + '/', b''), (OBJECT, b'{}')])
        result, _ = self.fetch(replies(archive))
        self.assertEqual(result, {OBJECT: b'{}'})

    def test_rejects_duplicate_zip_entries(self):
        self.reject(replies(make_zip([(OBJECT, b'{}'), (OBJECT, b'{"changed":true}') ])))
        self.reject(replies(make_zip([('objects/', b''), ('objects/', b''), (OBJECT, b'{}')])))

    def test_rejects_zip_symlinks(self):
        entry = zipfile.ZipInfo(OBJECT)
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.reject(replies(make_zip([(entry, b'/etc/passwd')])))

    def test_rejects_encrypted_zip_entries(self):
        archive = bytearray(make_zip([(OBJECT, b'{}')]))
        local = archive.index(b'PK\x03\x04')
        central = archive.index(b'PK\x01\x02')
        for offset in [local + 6, central + 8]:
            struct.pack_into('<H', archive, offset, struct.unpack_from('<H', archive, offset)[0] | 1)
        self.reject(replies(bytes(archive)))

    def test_rejects_null_terminated_zip_names(self):
        archive = bytearray(make_zip([(OBJECT, b'{}')]))
        needle = OBJECT.encode()
        positions = [index for index in range(len(archive)) if archive.startswith(needle, index)]
        self.assertEqual(len(positions), 2)
        for index in positions:
            archive[index + len(needle) - 1] = 0
        self.reject(replies(bytes(archive)))

    def test_rejects_member_larger_than_64_kib(self):
        self.reject(replies(make_zip([(OBJECT, b'x' * (64 * 1024 + 1))])))

    def test_rejects_total_unpacked_size_over_two_mib(self):
        entries = [('objects/' + f'{index:064x}' + '.json', b'x' * (64 * 1024)) for index in range(33)]
        self.reject(replies(make_zip(entries)))

    def test_accepts_exact_member_and_total_unpacked_limits(self):
        entries = [('objects/' + f'{index:064x}' + '.json', b'x' * (64 * 1024)) for index in range(32)]
        result, _ = self.fetch(replies(make_zip(entries)))
        self.assertEqual(len(result), 32)
        self.assertEqual(sum(map(len, result.values())), 2 * 1024 * 1024)

    def test_rejects_more_than_48_entries_including_directories(self):
        entries = [('objects/' + f'{index:064x}' + '.json', b'{}') for index in range(48)]
        self.fetch(replies(make_zip(entries)))
        self.reject(replies(make_zip(entries + [('objects/', b'')])))

    def test_rejects_corrupt_archives_with_valid_download_digests(self):
        for archive in [b'not-zip-' + TOKEN.encode(), make_zip()[:50], b'']:
            with self.subTest(length=len(archive)):
                self.reject(replies(archive))


if __name__ == '__main__':
    unittest.main()
