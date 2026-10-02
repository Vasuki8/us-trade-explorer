"""Private singleton source bytes, independently bound to normalized evidence."""
import hashlib
from pathlib import Path

from pipeline.batch import MAX_FILE_BYTES, atomic_write, validate_slot
from pipeline.candidates import decode, hash_text, require, validate_candidate
from pipeline.census import SourceError, fetch_candidate, parse_rows


def validate_raw_response(raw, candidate, slot, secrets=()):
    """Hash AND reparse the exact response; a valid hash alone is insufficient."""
    validate_slot(slot)
    validate_candidate(candidate, slot)
    require(type(raw) is bytes and 0 < len(raw) <= MAX_FILE_BYTES, 'Missing or oversized raw source object')
    require(hashlib.sha256(raw).hexdigest() == candidate['sourceHash'], 'Raw source checksum mismatch')
    table = decode(raw, secrets)
    rows = parse_rows(table, slot['flow'], slot['period'], expected_summary='DET' if slot['partner'] == '-' else None)
    require(len(rows) == 1 and rows == candidate['rows'], 'Raw source observations differ from normalized evidence')
    return raw


def raw_bytes(root, source_hash):
    hash_text(source_hash)
    path = Path(root) / 'raw' / (source_hash + '.json')
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= MAX_FILE_BYTES,
            'Missing or oversized raw source object')
    try:
        raw = path.read_bytes()
    except OSError:
        raise SourceError('Raw source object could not be read') from None
    require(len(raw) <= MAX_FILE_BYTES and hashlib.sha256(raw).hexdigest() == source_hash, 'Raw source checksum mismatch')
    return raw


def acquire_with_raw(flow, period, key, *, product, partner, root, evidence_secrets=()):
    """Preserve approved raw bytes before the caller marks a normalized slot done."""
    slot = {'flow': flow, 'period': period, 'product': product, 'partner': partner}
    validate_slot(slot)
    captured = []
    candidate = fetch_candidate(flow, period, key, product=product, partner=partner, capture=captured.append)
    require(len(captured) == 1, 'Raw source capture did not complete')
    raw = validate_raw_response(captured[0], candidate, slot, secrets=(key, *evidence_secrets))
    path = Path(root) / 'raw' / (candidate['sourceHash'] + '.json')
    try:
        if path.exists():
            require(raw_bytes(root, candidate['sourceHash']) == raw, 'Raw source identity collision')
        else:
            atomic_write(path, raw)
    except OSError:
        raise SourceError('Raw source object could not be preserved') from None
    return candidate
