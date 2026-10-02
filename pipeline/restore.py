"""Bounded private batch downloads. Members remain in memory for caller validation."""
import hashlib
import hmac
import http.client
import io
import json
import re
import socket
import stat
import threading
import time
import zipfile
from urllib.parse import urlsplit


API_HOST = 'api.github.com'
MAX_METADATA_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024
MAX_MEMBER_BYTES = 64 * 1024
MAX_ENTRIES = 48
MAX_PARTNER_MEMBER_BYTES = 512 * 1024
MAX_PARTNER_FILES = 20
MAX_PARTNER_ENTRIES = 24
READ_SECONDS = 30
STORAGE_SUFFIXES = ('.blob.core.windows.net', '.actions.githubusercontent.com', '.githubusercontent.com')
MEMBER_PATH = re.compile(r'(?:objects/[0-9a-f]{64}\.json|bundles/[0-9a-f]{64}\.json|batches/[0-9a-f]{64}/(?:progress|complete)\.json)')
DIRECTORY_PATH = re.compile(r'(?:objects/|bundles/|batches/|batches/[0-9a-f]{64}/)')
ARCHIVED_MEMBER_PATH = re.compile(r'(?:' + MEMBER_PATH.pattern + r'|raw/[0-9a-f]{64}\.json|archive/(?:[0-9a-f]{64}|complete)\.json)')
ARCHIVED_DIRECTORY_PATH = re.compile(r'(?:' + DIRECTORY_PATH.pattern + r'|raw/|archive/)')
PARTNER_MEMBER_PATH = re.compile(r'(?:(?:raw|scans|receipts)/[0-9a-f]{64}\.json|progress\.json|complete\.json)')
PARTNER_DIRECTORY_PATH = re.compile(r'(?:raw/|scans/|receipts/)')


class SnapshotError(Exception):
    """Fixed diagnostic without upstream text, URLs, credentials, or exception chains."""

    def __init__(self):
        super().__init__('Private batch snapshot could not be restored')


def _require(condition):
    if not condition:
        raise ValueError('Snapshot rejected')


def _positive_integer(value):
    return type(value) is int and value > 0


def _validate_inputs(repository, run_id, token):
    _require(isinstance(repository, str))
    _require(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9_.-]{1,100}', repository) is not None)
    _require(any(character.isalnum() for character in repository.split('/')[1]))
    _require(_positive_integer(run_id))
    _require(isinstance(token, str) and 0 < len(token) <= 4096)
    _require(all(33 <= ord(character) <= 126 for character in token))


def _request(host, target, headers, *, status, maximum, metadata=False):
    """One HTTPS request, with a five-second connect and thirty-second response budget."""
    connection = http.client.HTTPSConnection(host, timeout=5)
    response = None
    watchdog = None
    expired = threading.Event()
    try:
        connection.connect()
        transport = connection.sock
        deadline = time.monotonic() + READ_SECONDS

        def abort_response():
            expired.set()
            try:
                transport.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        watchdog = threading.Timer(READ_SECONDS, abort_response)
        watchdog.daemon = True
        watchdog.start()
        transport.settimeout(READ_SECONDS)
        connection.request('GET', target, headers=headers)
        response = connection.getresponse()
        _require(type(response.status) is int and response.status == status)
        _require(not expired.is_set() and time.monotonic() < deadline)
        if status == 302:
            return response.getheader('Location')
        _require(response.getheader('Content-Encoding', 'identity').lower() == 'identity')
        if metadata:
            _require(response.getheader('Content-Type', '').split(';')[0].strip().lower() == 'application/json')
        declared = response.getheader('Content-Length')
        if declared is not None:
            _require(isinstance(declared, str) and re.fullmatch(r'[0-9]{1,10}', declared) is not None)
            declared = int(declared)
            _require(declared <= maximum)
        chunks = []
        length = 0
        while True:
            remaining = deadline - time.monotonic()
            _require(remaining > 0 and not expired.is_set())
            transport.settimeout(remaining)
            chunk = response.read1(min(65536, maximum + 1 - length))
            if not chunk:
                break
            _require(isinstance(chunk, bytes))
            length += len(chunk)
            _require(length <= maximum)
            chunks.append(chunk)
        _require(not expired.is_set() and time.monotonic() < deadline)
        _require(declared is None or length == declared)
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


def _json_object(raw):
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            _require(key not in value)
            value[key] = item
        return value

    def reject_constant(_value):
        raise ValueError('Snapshot rejected')

    result = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object, parse_constant=reject_constant)
    _require(type(result) is dict)
    return result


def _storage_target(location):
    _require(isinstance(location, str) and 0 < len(location) <= MAX_METADATA_BYTES)
    _require(all(33 <= ord(character) <= 126 for character in location))
    parsed = urlsplit(location)
    host = parsed.hostname
    _require(parsed.scheme == 'https' and parsed.username is None and parsed.password is None)
    _require(not parsed.fragment and parsed.port in (None, 443))
    _require(isinstance(host, str) and re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+', host) is not None)
    _require(all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?', label) for label in host.split('.')))
    _require(any(host.endswith(suffix) and len(host) > len(suffix) for suffix in STORAGE_SUFFIXES))
    # Checking the original authority rejects ambiguous spellings such as :0443.
    _require(parsed.netloc.lower() in (host, host + ':443'))
    target = parsed.path or '/'
    if parsed.query:
        target += '?' + parsed.query
    return host, target


def _members(raw, archived=False, *, partners=False):
    _require(type(partners) is bool and not (partners and archived))
    result = {}
    member_path = ARCHIVED_MEMBER_PATH if archived else MEMBER_PATH
    directory_path = ARCHIVED_DIRECTORY_PATH if archived else DIRECTORY_PATH
    maximum_member = MAX_MEMBER_BYTES
    maximum_entries = MAX_ENTRIES
    if partners:
        _require(len(raw) <= MAX_ARCHIVE_BYTES)
        member_path = PARTNER_MEMBER_PATH
        directory_path = PARTNER_DIRECTORY_PATH
        maximum_member = MAX_PARTNER_MEMBER_BYTES
        maximum_entries = MAX_PARTNER_ENTRIES
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        _require(0 < len(entries) <= maximum_entries)
        seen = set()
        unpacked = 0
        file_count = 0
        for entry in entries:
            name = entry.filename
            _require(entry.orig_filename == name and name not in seen)
            seen.add(name)
            _require(not entry.flag_bits & 1)
            mode = entry.external_attr >> 16
            _require(not stat.S_ISLNK(mode))
            _require(entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED))
            if entry.is_dir():
                _require(directory_path.fullmatch(name) is not None and entry.file_size == 0)
                _require(stat.S_IFMT(mode) in (0, stat.S_IFDIR))
                continue
            _require(member_path.fullmatch(name) is not None)
            _require(stat.S_IFMT(mode) in (0, stat.S_IFREG))
            _require(0 <= entry.file_size <= maximum_member)
            file_count += 1
            _require(not partners or file_count <= MAX_PARTNER_FILES)
            unpacked += entry.file_size
            _require(unpacked <= MAX_ARCHIVE_BYTES)
        # Validate the complete index before decompressing any member.
        for entry in entries:
            if entry.is_dir():
                continue
            with archive.open(entry) as member:
                contents = member.read(maximum_member + 1)
            _require(len(contents) == entry.file_size and len(contents) <= maximum_member)
            result[entry.filename] = contents
    _require(bool(result))
    return result


def _fetch_snapshot(repository, run_id, token, archived=False, *, partners=False):
    _validate_inputs(repository, run_id, token)
    _require(type(partners) is bool and not (partners and archived))
    api_headers = {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.github+json',
        'Accept-Encoding': 'identity',
        'User-Agent': 'US-Trade-Explorer/0.1',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    run_path = f'/repos/{repository}/actions/runs/{run_id}'
    run = _json_object(_request(API_HOST, run_path, api_headers, status=200, maximum=MAX_METADATA_BYTES, metadata=True))
    _require(_positive_integer(run.get('id')) and run['id'] == run_id)
    _require(type(run.get('repository')) is dict and run['repository'].get('full_name') == repository)
    _require(run.get('event') == 'workflow_dispatch' and run.get('head_branch') == 'main')
    workflow = '.github/workflows/census-archive.yml' if archived else '.github/workflows/census-batch.yml'
    artifact_name = f'census-archive-{run_id}' if archived else f'census-batch-{run_id}'
    if partners:
        workflow = '.github/workflows/census-partners.yml'
        artifact_name = f'census-partners-{run_id}'
    _require(run.get('path') == workflow and run.get('status') == 'completed')
    artifacts = _json_object(_request(API_HOST, run_path + '/artifacts?per_page=100', api_headers, status=200, maximum=MAX_METADATA_BYTES, metadata=True))
    _require(type(artifacts.get('total_count')) is int and artifacts['total_count'] == 1)
    _require(type(artifacts.get('artifacts')) is list and len(artifacts['artifacts']) == 1)
    artifact = artifacts['artifacts'][0]
    _require(type(artifact) is dict and _positive_integer(artifact.get('id')))
    _require(artifact.get('name') == artifact_name and artifact.get('expired') is False)
    _require(_positive_integer(artifact.get('size_in_bytes')) and artifact['size_in_bytes'] <= MAX_ARCHIVE_BYTES)
    digest = artifact.get('digest')
    _require(isinstance(digest, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', digest) is not None)
    archive_path = f"/repos/{repository}/actions/artifacts/{artifact['id']}/zip"
    location = _request(API_HOST, archive_path, api_headers, status=302, maximum=MAX_METADATA_BYTES)
    host, target = _storage_target(location)
    storage_headers = {'Accept': 'application/zip', 'Accept-Encoding': 'identity', 'User-Agent': 'US-Trade-Explorer/0.1'}
    raw = _request(host, target, storage_headers, status=200, maximum=MAX_ARCHIVE_BYTES)
    _require(hmac.compare_digest(hashlib.sha256(raw).hexdigest(), digest[7:]))
    if partners:
        return _members(raw, partners=True)
    return _members(raw, archived=archived)


def fetch_snapshot(repository: str, run_id: int, token: str) -> dict[str, bytes]:
    """Return only allowlisted member bytes; the caller must validate all JSON before writing."""
    try:
        return _fetch_snapshot(repository, run_id, token)
    except Exception:
        # Raise outside the handler so even __context__ cannot retain a secret.
        pass
    raise SnapshotError() from None


def fetch_archived_snapshot(repository: str, run_id: int, token: str) -> dict[str, bytes]:
    """Trust only the fixed main archive workflow; callers validate raw and normalized evidence."""
    try:
        return _fetch_snapshot(repository, run_id, token, archived=True)
    except Exception:
        pass
    raise SnapshotError() from None


def fetch_partner_snapshot(repository: str, run_id: int, token: str) -> dict[str, bytes]:
    """Trust only main partner discovery; callers validate partial or complete generations."""
    try:
        return _fetch_snapshot(repository, run_id, token, partners=True)
    except Exception:
        pass
    raise SnapshotError() from None
