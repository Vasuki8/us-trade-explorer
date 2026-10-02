"""Reviewed publication evidence stays private and never proves an API vintage."""
import copy
import hashlib
import http.client
import io
import json
from pathlib import Path
import socket
import tempfile
import threading
import traceback
import unittest
from unittest.mock import patch

from pipeline.candidates import canonical, decode, digest
from pipeline.census import SourceError

try:
    from pipeline import publication
except ImportError:
    publication = None


PDF = b'%PDF-1.7\nFabricated publication document for offline tests.\n%%EOF\n'
SECRET = 'canary-publication-private-secret'


def statement(document=PDF, **changes):
    return {
        'schemaVersion': 1,
        'publisher': 'US Census Bureau and Bureau of Economic Analysis',
        'basis': 'census-monthly-goods-nsa-usd-v1',
        'period': '2026-07',
        'flows': ['imports', 'exports'],
        'officialReleaseDate': '2026-09-03',
        'officialRevisionDate': None,
        'sourceURL': 'https://www.census.gov/foreign-trade/Press-Release/ft900/ft900_2607.pdf',
        'documentHash': hashlib.sha256(document).hexdigest(),
        'claim': 'initial-monthly-announcement-only',
        'apiVintageVerified': False,
        'reviewedOn': '2026-10-02',
        'releaseIDs': {'census': 'CB26-142', 'bea': 'BEA26-40'},
        **changes,
    }


class FakeResponse:
    def __init__(self, body=PDF, status=200, headers=None, failure=None):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = {k.lower(): v for k, v in ({'Content-Type': 'application/pdf', **(headers or {})}).items()}
        self.failure = failure
        self.closed = False
        self.read_bytes = 0

    def getheader(self, name, default=None):
        return self.headers.get(name.lower(), default)

    def read1(self, maximum):
        if self.failure:
            raise self.failure
        value = self.body.read(maximum)
        self.read_bytes += len(value)
        return value

    def close(self):
        self.closed = True


class FakeSocket:
    def __init__(self):
        self.timeouts = []
        self.shutdowns = []
        self.closed_event = threading.Event()

    def settimeout(self, timeout):
        self.timeouts.append(timeout)

    def shutdown(self, mode):
        self.shutdowns.append(mode)
        self.closed_event.set()


class FakeConnection:
    def __init__(self, response, failure=None):
        self.response = response
        self.failure = failure
        self.sock = FakeSocket()
        self.requests = []
        self.closed = False

    def connect(self):
        if self.failure:
            raise self.failure

    def request(self, method, target, headers):
        self.requests.append((method, target, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(publication, 'Publication evidence module is not implemented')

    def test_reviewed_statement_yields_bound_announcement_only_proof(self):
        value = statement()
        self.assertEqual(publication.validate_statement(value), value)
        proof = publication.verify_publication(value, PDF)
        self.assertEqual(proof['statementId'], digest(value))
        self.assertEqual(proof['documentHash'], hashlib.sha256(PDF).hexdigest())
        self.assertEqual(proof['officialReleaseDate'], '2026-09-03')
        self.assertIsNone(proof['officialRevisionDate'])
        self.assertFalse(proof['apiVintageVerified'])
        self.assertEqual(proof['claim'], 'initial-monthly-announcement-only')
        self.assertNotIn('retrievedAt', proof)

    def test_statement_rejects_unsupported_fields_and_invented_revision_or_vintage(self):
        for changes in ({'privateNote': SECRET}, {'schemaVersion': True}, {'officialRevisionDate': '2026-09-04'},
                        {'apiVintageVerified': True}, {'claim': 'current-api-vintage'},
                        {'publisher': 'Untrusted publisher'}, {'basis': 'seasonally-adjusted-goods-and-services'},
                        {'flows': ['exports', 'imports']}, {'releaseIDs': {'census': 'CB26-142', 'bea': 'BEA25-40'}}):
            with self.subTest(changes=changes), self.assertRaises(SourceError):
                publication.validate_statement(statement(**changes))

    def test_statement_dates_are_real_and_follow_the_data_period(self):
        for changes in ({'officialReleaseDate': '2026-02-30'}, {'officialReleaseDate': '2026-07-31'},
                        {'officialReleaseDate': '2026-10-03'}, {'reviewedOn': '2026-09-02'},
                        {'period': '2026-13'}, {'officialReleaseDate': '2026-9-03'},
                        {'reviewedOn': '2026-10-02T00:00:00Z'}):
            with self.subTest(changes=changes), self.assertRaises(SourceError):
                publication.validate_statement(statement(**changes))

    def test_fixed_official_url_excludes_redirect_and_credential_spellings(self):
        original = statement()['sourceURL']
        for url in (original + '?key=' + SECRET, original + '#fragment', original.replace('https:', 'http:'),
                    original.replace('www.census.gov', 'www.census.gov.evil.example'),
                    original.replace('www.census.gov', 'user@www.census.gov'),
                    original.replace('www.census.gov', 'www.census.gov:443'),
                    original.replace('2607.pdf', '2606.pdf'), original + '\n',
                    original.replace('/ft900/', '/%66t900/')):
            with self.subTest(url=url), self.assertRaises(SourceError):
                publication.validate_statement(statement(sourceURL=url))

    def test_document_must_match_reviewed_hash_and_be_a_bounded_pdf(self):
        for value, body in ((statement(), PDF + b'changed'), (statement(b'<html>error</html>'), b'<html>error</html>'),
                            (statement(b''), b''), (statement(), bytearray(PDF))):
            with self.subTest(body=body), self.assertRaises(SourceError):
                publication.verify_publication(value, body)
        with patch.object(publication, 'MAX_DOCUMENT_BYTES', len(PDF) - 1), self.assertRaises(SourceError):
            publication.verify_publication(statement(), PDF)

    def test_reflected_secret_is_rejected_before_archiving_or_output(self):
        body = PDF + SECRET.encode()
        with self.assertRaises(SourceError) as caught:
            publication.verify_publication(statement(body), body, secrets=(SECRET,))
        self.assertNotIn(SECRET, str(caught.exception))
        # Decode must reject an escaped field before strict statement validation.
        raw = json.dumps({'sourceURL': '\\u0063' + SECRET[1:]}).encode().replace(b'\\\\u0063', b'\\u0063')
        with self.assertRaises(SourceError):
            decode(raw, (SECRET,))

    def test_fetch_is_fixed_https_and_returns_only_verified_pdf_bytes(self):
        response = FakeResponse(headers={'Content-Length': str(len(PDF))})
        connection = FakeConnection(response)
        with patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection) as constructor:
            self.assertEqual(publication.fetch_document(statement()), PDF)
        constructor.assert_called_once_with('www.census.gov', timeout=5)
        method, target, headers = connection.requests[0]
        self.assertEqual((method, target), ('GET', '/foreign-trade/Press-Release/ft900/ft900_2607.pdf'))
        self.assertEqual(headers['Accept-Encoding'], 'identity')
        self.assertNotIn('Authorization', headers)
        self.assertTrue(response.closed and connection.closed)
        self.assertTrue(all(0 < value <= 30 for value in connection.sock.timeouts))

    def test_fetch_rejects_http_redirects_encodings_lengths_and_untrusted_types(self):
        replies = [FakeResponse(status=302, headers={'Location': 'https://evil.example/' + SECRET}),
                   FakeResponse(status=204), FakeResponse(headers={'Content-Encoding': 'gzip'}),
                   FakeResponse(headers={'Content-Length': str(4 * 1024 * 1024 + 1)}),
                   FakeResponse(headers={'Content-Length': 'not-a-number'}),
                   FakeResponse(headers={'Content-Length': str(len(PDF) + 1)}),
                   FakeResponse(headers={'Content-Type': 'text/html'})]
        for response in replies:
            connection = FakeConnection(response)
            with self.subTest(headers=response.headers), patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection):
                with self.assertRaises(SourceError) as caught:
                    publication.fetch_document(statement())
                self.assertNotIn(SECRET, str(caught.exception))
                self.assertEqual(len(connection.requests), 1)
                self.assertTrue(response.closed and connection.closed)

    def test_response_size_is_bounded_when_content_length_is_absent(self):
        response = FakeResponse(body=PDF + b'excess')
        connection = FakeConnection(response)
        with patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection), \
                patch.object(publication, 'MAX_DOCUMENT_BYTES', len(PDF)), self.assertRaises(SourceError):
            publication.fetch_document(statement())
        self.assertLessEqual(response.read_bytes, len(PDF) + 1)

    def test_network_errors_have_safe_diagnostics_without_exception_chain(self):
        for failure, on_connect in ((socket.timeout(SECRET), True),
                                    (http.client.HTTPException(SECRET), False), (OSError(SECRET), False)):
            response = FakeResponse(failure=None if on_connect else failure)
            connection = FakeConnection(response, failure=failure if on_connect else None)
            with self.subTest(failure=failure), patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection):
                with self.assertRaises(SourceError) as caught:
                    publication.fetch_document(statement())
                rendered = ''.join(traceback.format_exception(caught.exception))
                self.assertNotIn(SECRET, rendered)
                self.assertTrue(connection.closed)

    def test_elapsed_deadline_rejects_headers_before_body_read(self):
        response = FakeResponse()
        connection = FakeConnection(response)
        with patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection), \
                patch('pipeline.publication.time.monotonic', side_effect=[0, 31]), self.assertRaises(SourceError):
            publication.fetch_document(statement())
        self.assertEqual(response.read_bytes, 0)

    def test_watchdog_shuts_down_stalled_body_read(self):
        response = FakeResponse()
        connection = FakeConnection(response)

        def stalled_read(_maximum):
            self.assertTrue(connection.sock.closed_event.wait(1), 'Watchdog did not interrupt the body read')
            raise OSError('Upstream connection text ' + SECRET)

        response.read1 = stalled_read
        with patch('pipeline.publication.http.client.HTTPSConnection', return_value=connection), \
                patch.object(publication, 'RESPONSE_SECONDS', 0.02), self.assertRaises(SourceError) as caught:
            publication.fetch_document(statement())
        self.assertEqual(connection.sock.shutdowns, [socket.SHUT_RDWR])
        self.assertNotIn(SECRET, str(caught.exception))
        self.assertTrue(response.closed and connection.closed)

    def test_private_archive_preserves_first_valid_document_and_retrieval_time(self):
        with tempfile.TemporaryDirectory() as directory, patch('pipeline.publication.fetch_document', return_value=PDF) as fetch:
            root = Path(directory)
            first = publication.archive_publication(statement(), root)
            second = publication.archive_publication(statement(), root)
            self.assertEqual(first, second)
            fetch.assert_called_once()
            self.assertEqual((root / 'documents' / (first['documentHash'] + '.pdf')).read_bytes(), PDF)
            self.assertEqual(decode((root / 'proof.json').read_bytes()), first)
            self.assertEqual({p.name for p in root.iterdir()}, {'documents', 'proof.json'})
            self.assertRegex(first['retrievedAt'], r'^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_failed_download_preserves_previous_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('pipeline.publication.fetch_document', return_value=PDF):
                first = publication.archive_publication(statement(), root)
            original = (root / 'proof.json').read_bytes()
            changed = statement(PDF + b'changed')
            with patch('pipeline.publication.fetch_document', side_effect=SourceError('Source unavailable')):
                with self.assertRaises(SourceError):
                    publication.archive_publication(changed, root)
            self.assertEqual((root / 'proof.json').read_bytes(), original)
            self.assertEqual((root / 'documents' / (first['documentHash'] + '.pdf')).read_bytes(), PDF)

    def test_archive_does_not_trust_tampered_proof_or_source_document(self):
        for tamper in ('proof', 'document'):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch('pipeline.publication.fetch_document', return_value=PDF):
                    proof = publication.archive_publication(statement(), root)
                if tamper == 'proof':
                    changed = copy.deepcopy(proof)
                    changed['apiVintageVerified'] = True
                    (root / 'proof.json').write_bytes(canonical(changed))
                else:
                    (root / 'documents' / (proof['documentHash'] + '.pdf')).write_bytes(PDF + b'changed')
                with patch('pipeline.publication.fetch_document') as fetch, self.assertRaises(SourceError):
                    publication.archive_publication(statement(), root)
                fetch.assert_not_called()

    def test_archive_rejects_boolean_and_numeric_type_substitution_in_proof(self):
        for field, value in (('schemaVersion', True), ('apiVintageVerified', 0)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch('pipeline.publication.fetch_document', return_value=PDF):
                    proof = publication.archive_publication(statement(), root)
                proof[field] = value
                (root / 'proof.json').write_bytes(canonical(proof))
                with patch('pipeline.publication.fetch_document') as fetch, self.assertRaises(SourceError):
                    publication.archive_publication(statement(), root)
                fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
