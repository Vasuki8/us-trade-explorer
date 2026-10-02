"""Bound a reviewed announcement statement to its private source PDF.

The statement is reviewed in Git. These checks do not extract the release date
from PDF text or establish the vintage of any current API observation.
"""
from datetime import date, datetime, timezone
import hashlib
import http.client
from pathlib import Path
import re
import socket
import ssl
import threading
import time

from pipeline.batch import BASIS, atomic_write, read, writer
from pipeline.candidates import canonical, decode, digest, hash_text, keys, require, timestamp
from pipeline.census import SourceError, validate_period

HOST = 'www.census.gov'
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
RESPONSE_SECONDS = 30
PUBLISHER = 'US Census Bureau and Bureau of Economic Analysis'
CLAIM = 'initial-monthly-announcement-only'
STATEMENT_FIELDS = ['schemaVersion', 'publisher', 'basis', 'period', 'flows', 'officialReleaseDate',
                    'officialRevisionDate', 'sourceURL', 'documentHash', 'claim', 'apiVintageVerified',
                    'reviewedOn', 'releaseIDs']


def _date(value):
    require(type(value) is str and re.fullmatch(r'20\d{2}-\d{2}-\d{2}', value), 'Invalid publication date')
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise SourceError('Invalid publication date') from None


def validate_statement(statement):
    """Accept only an explicit, reviewed announcement claim and fixed official URL."""
    keys(statement, STATEMENT_FIELDS)
    require(type(statement['schemaVersion']) is int and statement['schemaVersion'] == 1)
    require(statement['publisher'] == PUBLISHER and statement['basis'] == BASIS)
    validate_period(statement['period'])
    require(type(statement['flows']) is list and statement['flows'] == ['imports', 'exports'])
    require(statement['claim'] == CLAIM and statement['apiVintageVerified'] is False)
    require(statement['officialRevisionDate'] is None, 'Revision evidence has not been established')
    release_date = _date(statement['officialReleaseDate'])
    reviewed_date = _date(statement['reviewedOn'])
    period = statement['period']
    # A monthly announcement cannot precede completion of the referenced month.
    require(release_date.strftime('%Y-%m') > period and release_date <= reviewed_date,
            'Publication date is inconsistent with the reviewed period')
    expected_url = f'https://{HOST}/foreign-trade/Press-Release/ft900/ft900_{period[2:4]}{period[5:]}.pdf'
    require(type(statement['sourceURL']) is str and statement['sourceURL'] == expected_url,
            'Publication source is not allowlisted')
    hash_text(statement['documentHash'])
    keys(statement['releaseIDs'], ['census', 'bea'])
    for key, pattern in (('census', rf'CB{release_date.year % 100:02d}-[0-9]{{1,4}}'),
                         ('bea', rf'BEA{release_date.year % 100:02d}-[0-9]{{1,4}}')):
        require(type(statement['releaseIDs'][key]) is str and re.fullmatch(pattern, statement['releaseIDs'][key]),
                'Invalid official release identity')
    return statement


def _secrets(secrets):
    values = (secrets,) if type(secrets) is str else secrets
    require(type(values) in (tuple, list) and all(type(value) is str for value in values), 'Invalid evidence safety inputs')
    return tuple(value for value in values if value)


def verify_publication(statement, document, secrets=()):
    """Pure verification; a digest binds the PDF to a separately reviewed statement."""
    statement = validate_statement(statement)
    secrets = _secrets(secrets)
    decode(canonical(statement), secrets)
    require(type(document) is bytes and 5 < len(document) <= MAX_DOCUMENT_BYTES,
            'Missing or oversized publication document')
    require(document.startswith(b'%PDF-'), 'Publication document is not a PDF')
    require(all(value.encode('utf-8') not in document for value in secrets), 'Evidence safety check failed')
    document_hash = hashlib.sha256(document).hexdigest()
    require(document_hash == statement['documentHash'], 'Publication document checksum mismatch')
    proof = {
        'schemaVersion': 1,
        'statementId': digest(statement),
        'documentHash': document_hash,
        **{key: statement[key] for key in ('period', 'basis', 'flows', 'officialReleaseDate',
                                         'officialRevisionDate', 'sourceURL', 'claim', 'apiVintageVerified')},
    }
    decode(canonical(proof), secrets)
    return proof


def _download(statement):
    """One fixed HTTPS request with a bounded body and an absolute response budget."""
    connection = http.client.HTTPSConnection(HOST, timeout=5)
    response = None
    watchdog = None
    expired = threading.Event()
    try:
        connection.connect()
        transport = connection.sock
        deadline = time.monotonic() + RESPONSE_SECONDS

        def abort_response():
            expired.set()
            try:
                transport.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        watchdog = threading.Timer(RESPONSE_SECONDS, abort_response)
        watchdog.daemon = True
        watchdog.start()
        transport.settimeout(RESPONSE_SECONDS)
        target = statement['sourceURL'][len('https://' + HOST):]
        connection.request('GET', target, headers={
            'Accept': 'application/pdf', 'Accept-Encoding': 'identity',
            'User-Agent': 'US-Trade-Explorer-private-publication-verification/1',
        })
        response = connection.getresponse()
        require(type(response.status) is int and response.status == 200, 'Publication source request was rejected')
        require(not expired.is_set() and time.monotonic() < deadline, 'Publication source request timed out')
        require(response.getheader('Content-Encoding', 'identity').lower() == 'identity', 'Unsupported publication encoding')
        require(response.getheader('Content-Type', '').split(';')[0].strip().lower() == 'application/pdf',
                'Unsupported publication response type')
        declared = response.getheader('Content-Length')
        if declared is not None:
            require(type(declared) is str and re.fullmatch(r'[0-9]{1,10}', declared), 'Invalid publication response length')
            declared = int(declared)
            require(0 < declared <= MAX_DOCUMENT_BYTES, 'Oversized publication response')
        chunks = []
        length = 0
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0 and not expired.is_set(), 'Publication source request timed out')
            transport.settimeout(remaining)
            chunk = response.read1(min(65536, MAX_DOCUMENT_BYTES + 1 - length))
            require(type(chunk) is bytes, 'Invalid publication response')
            if not chunk:
                break
            length += len(chunk)
            require(length <= MAX_DOCUMENT_BYTES, 'Oversized publication response')
            chunks.append(chunk)
        require(not expired.is_set() and time.monotonic() < deadline, 'Publication source request timed out')
        require(declared is None or length == declared, 'Incomplete publication response')
        return b''.join(chunks)
    finally:
        if watchdog is not None:
            watchdog.cancel()
            watchdog.join()
        try:
            if response is not None:
                response.close()
        finally:
            connection.close()


def fetch_document(statement, secrets=()):
    """Download and verify without redirects, credentials, or upstream diagnostics."""
    validate_statement(statement)
    secrets = _secrets(secrets)
    decode(canonical(statement), secrets)
    try:
        document = _download(statement)
        verify_publication(statement, document, secrets)
        return document
    except (OSError, ssl.SSLError, http.client.HTTPException, ValueError, TypeError, AttributeError):
        raise SourceError('Publication document could not be retrieved') from None


def _stored_document(path):
    require(path.is_file() and not path.is_symlink() and 5 < path.stat().st_size <= MAX_DOCUMENT_BYTES,
            'Missing or oversized publication document')
    return path.read_bytes()


def archive_publication(statement, root, secrets=()):
    """Keep immutable source bytes and publish a proof only after full verification.

    A valid existing archive is reused, including its original retrieval time.
    A changed reviewed statement belongs in a separate archive root.
    """
    validate_statement(statement)
    secrets = _secrets(secrets)
    decode(canonical(statement), secrets)
    root = Path(root)
    path = root / 'documents' / (statement['documentHash'] + '.pdf')
    proof_path = root / 'proof.json'
    try:
        with writer(root):
            if proof_path.exists():
                stored = read(proof_path, secrets)
                expected = verify_publication(statement, _stored_document(path), secrets)
                keys(stored, [*expected, 'retrievedAt'])
                timestamp(stored['retrievedAt'])
                require(canonical({key: stored[key] for key in expected}) == canonical(expected),
                        'Publication proof mismatch')
                return stored
            document = fetch_document(statement, secrets)
            proof = verify_publication(statement, document, secrets)
            proof['retrievedAt'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            decode(canonical(proof), secrets)
            if path.exists():
                require(_stored_document(path) == document, 'Publication archive identity collision')
            else:
                atomic_write(path, document)
            atomic_write(proof_path, canonical(proof))
            return proof
    except (OSError, KeyError, TypeError):
        raise SourceError('Publication evidence could not be archived') from None
