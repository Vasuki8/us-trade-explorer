"""Private raw-response archives. A receipt proves reparsing, never public release eligibility."""
import argparse
import hashlib
import os
from pathlib import Path
import re

from pipeline import batch
from pipeline.batch import atomic_write
from pipeline.candidates import MAX_FILE_BYTES, canonical, decode, digest, hash_text, keys, require
from pipeline.census import SourceError, parse_rows

ARCHIVE_BLOCKERS = batch.BUNDLE_BLOCKERS + ['Unreferenced raw responses do not validate normalized observations']
RAW_PATH = re.compile(r'raw/([a-f0-9]{64})\.json')
RECEIPT_PATH = re.compile(r'archive/([a-f0-9]{64})\.json')


def _inventory(files):
    require(type(files) is dict and 1 <= len(files) <= batch.MAX_SNAPSHOT_FILES, 'Invalid archive inventory')
    require(all(type(name) is str and type(value) is bytes and len(value) <= MAX_FILE_BYTES
                for name, value in files.items()), 'Invalid or oversized archive object')
    require(sum(map(len, files.values())) <= batch.MAX_SNAPSHOT_BYTES, 'Oversized archive snapshot')


def _stored_files(root):
    """Read bounded evidence; retain and ignore locks and known uncommitted atomic temporaries."""
    require(not root.is_symlink(), 'Unsafe archive destination')
    if not root.exists():
        return {}
    require(root.is_dir(), 'Invalid archive destination')
    files = {}
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Unsafe archive object')
        if path.is_dir():
            continue
        require(path.is_file(), 'Unsafe archive object')
        if path.name.startswith('.pending-'):
            # A process kill may leave mkstemp bytes before os.replace. They are
            # neither evidence nor safe to remove automatically during recovery.
            continue
        name = path.relative_to(root).as_posix()
        if name in ('batch.lock', 'archive/batch.lock'):
            continue
        require(path.stat().st_size <= MAX_FILE_BYTES, 'Oversized archive object')
        files[name] = path.read_bytes()
        require(len(files) <= batch.MAX_SNAPSHOT_FILES, 'Too many archive objects')
        require(sum(map(len, files.values())) <= batch.MAX_SNAPSHOT_BYTES, 'Oversized archive snapshot')
    return files


def _orphan_slot(raw, plan, secrets):
    """An interrupted raw write has no candidate provenance; it cannot satisfy a batch slot."""
    value = decode(raw, secrets)
    matches = []
    for slot in plan['partitions']:
        try:
            rows = parse_rows(value, slot['flow'], slot['period'],
                              expected_summary='DET' if slot['partner'] == '-' else None)
        except SourceError:
            continue
        if len(rows) == 1 and (rows[0]['product'], rows[0]['partnerCode']) == (slot['product'], slot['partner']):
            matches.append(slot)
    require(len(matches) == 1, 'Unreferenced raw response does not match one authorized slot')
    return matches[0]


def _raw_inventory(plan, normalized, raws, secrets):
    from pipeline.raw import validate_raw_response
    references = {}
    for candidate_id, candidate_bytes in normalized['objects'].items():
        candidate = decode(candidate_bytes, secrets)
        slot = {'flow': candidate['flow'], 'period': candidate['period'],
                'product': candidate['scope']['product'], 'partner': candidate['scope']['partner']}
        source_hash = candidate['sourceHash']
        require(source_hash in raws, 'Missing archived Census response')
        validate_raw_response(raws[source_hash], candidate, slot, secrets=secrets)
        entry = references.setdefault(source_hash, {'sourceHash': source_hash, 'slot': slot, 'candidateIds': []})
        require(entry['slot'] == slot, 'Raw response scope collision')
        entry['candidateIds'].append(candidate_id)
    for source_hash, raw in raws.items():
        require(hashlib.sha256(raw).hexdigest() == source_hash, 'Archived response checksum mismatch')
        if source_hash not in references:
            references[source_hash] = {'sourceHash': source_hash, 'slot': _orphan_slot(raw, plan, secrets), 'candidateIds': []}
    for entry in references.values():
        entry['candidateIds'].sort()
    return [references[source_hash] for source_hash in sorted(references)]


def _receipt(plan, bundle_id, raw_objects):
    value = {'schemaVersion': 1, 'planId': digest(plan), 'bundleId': bundle_id, 'basis': batch.BASIS,
             'state': 'private-archive', 'coverage': 'requested-partitions-only',
             'publicationBlockers': ARCHIVE_BLOCKERS, 'rawObjects': raw_objects}
    value['receiptId'] = digest(value)
    return value


def _validate_receipt(value, plan, normalized, raw_objects):
    keys(value, ['schemaVersion', 'receiptId', 'planId', 'bundleId', 'basis', 'state', 'coverage',
                 'publicationBlockers', 'rawObjects'])
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 1)
    require(value['planId'] == digest(plan) and value['basis'] == batch.BASIS, 'Archive plan mismatch')
    require(value['state'] == 'private-archive' and value['coverage'] == 'requested-partitions-only')
    require(value['publicationBlockers'] == ARCHIVE_BLOCKERS, 'Missing archive publication blockers')
    hash_text(value['receiptId'])
    hash_text(value['bundleId'])
    require(value['receiptId'] == digest({k: v for k, v in value.items() if k != 'receiptId'}), 'Archive receipt identity mismatch')
    require(value['bundleId'] in normalized['bundles'], 'Missing archived bundle')
    require(type(value['rawObjects']) is list and 1 <= len(value['rawObjects']) <= batch.MAX_SNAPSHOT_FILES, 'Invalid receipt inventory')
    known = {entry['sourceHash']: entry for entry in raw_objects}
    seen, included_ids = set(), set()
    for entry in value['rawObjects']:
        keys(entry, ['sourceHash', 'slot', 'candidateIds'])
        hash_text(entry['sourceHash'])
        require(entry['sourceHash'] not in seen and entry['sourceHash'] in known, 'Invalid receipt raw reference')
        seen.add(entry['sourceHash'])
        require(entry['slot'] == known[entry['sourceHash']]['slot'], 'Receipt raw scope mismatch')
        require(type(entry['candidateIds']) is list and entry['candidateIds'] == sorted(set(entry['candidateIds'])), 'Invalid receipt candidate inventory')
        for candidate_id in entry['candidateIds']:
            hash_text(candidate_id)
            require(candidate_id in known[entry['sourceHash']]['candidateIds'], 'Receipt candidate and raw mismatch')
            included_ids.add(candidate_id)
    require([entry['sourceHash'] for entry in value['rawObjects']] == sorted(seen), 'Receipt inventory order mismatch')
    require(all(entry['candidateId'] in included_ids for entry in normalized['bundles'][value['bundleId']]['partitions']), 'Incomplete receipt bundle coverage')
    return value


def _same_generation(normalized, receipt):
    pointer, journal = normalized['pointer'], normalized['journal']
    if pointer is None or receipt['bundleId'] != pointer['bundleId']:
        return False
    entries = journal['entries']
    if not all(entry['state'] == 'successful' for entry in entries):
        return False
    bundle = normalized['bundles'][pointer['bundleId']]
    return all((entry['slot'], entry['candidateId'], entry['objectHash']) ==
               (part['slot'], part['candidateId'], part['objectHash'])
               for entry, part in zip(entries, bundle['partitions']))


def _validate_snapshot(plan, files, secrets=(), require_complete=False):
    _inventory(files)
    normalized_files, raws, receipts, pointer = {}, {}, {}, None
    for name, raw in files.items():
        raw_match, receipt_match = RAW_PATH.fullmatch(name), RECEIPT_PATH.fullmatch(name)
        if raw_match:
            raws[raw_match.group(1)] = raw
        elif receipt_match:
            value = decode(raw, secrets)
            require(type(value) is dict and value.get('receiptId') == receipt_match.group(1), 'Archive filename identity mismatch')
            receipts[receipt_match.group(1)] = value
        elif name == 'archive/complete.json':
            pointer = decode(raw, secrets)
            keys(pointer, ['receiptId'])
            hash_text(pointer['receiptId'])
        else:
            normalized_files[name] = raw
    normalized = batch.validate_snapshot(plan, normalized_files, secrets=secrets)
    raw_objects = _raw_inventory(plan, normalized, raws, secrets)
    for receipt in receipts.values():
        _validate_receipt(receipt, plan, normalized, raw_objects)
    require(pointer is None or pointer['receiptId'] in receipts, 'Missing active archive receipt')
    receipt = None if pointer is None else receipts[pointer['receiptId']]
    complete = receipt is not None and _same_generation(normalized, receipt)
    if complete and require_complete:
        require(receipt['rawObjects'] == raw_objects, 'Active archive inventory mismatch')
    require(not require_complete or complete, 'Archive receipt and successful batch generation do not match')
    return {'normalized': normalized, 'rawObjects': raw_objects, 'receipts': receipts, 'receipt': receipt}


def run_archived_batch(plan, root, key, refresh=False, evidence_secrets=()):
    """Validate the entire private cache before requests, then activate one verified receipt."""
    from pipeline.raw import acquire_with_raw
    plan = batch.validate_plan(plan)
    batch.validate_key(key)
    secrets = (key, *evidence_secrets)
    root = Path(root)
    try:
        require(not root.is_symlink() and not (root / 'archive').is_symlink(), 'Unsafe archive destination')
        with batch.writer(root / 'archive'):
            files = _stored_files(root)
            if files:
                _validate_snapshot(plan, files, secrets)
            def acquire(flow, period, source_key, *, product, partner):
                return acquire_with_raw(flow, period, source_key, product=product, partner=partner,
                                        root=root, evidence_secrets=evidence_secrets)
            bundle = batch.run_batch(plan, root, key, refresh=refresh, evidence_secrets=evidence_secrets, acquire=acquire)
            state = _validate_snapshot(plan, _stored_files(root), secrets)
            receipt = _receipt(plan, bundle['bundleId'], state['rawObjects'])
            _validate_receipt(receipt, plan, state['normalized'], state['rawObjects'])
            require(_same_generation(state['normalized'], receipt), 'Incomplete archived batch generation')
            receipt_path = root / 'archive' / (receipt['receiptId'] + '.json')
            if receipt_path.exists():
                require(batch.read(receipt_path, secrets) == receipt, 'Archive identity collision')
            else:
                atomic_write(receipt_path, canonical(receipt))
            # Check prospective limits before replacing the last valid receipt pointer.
            prospective = _stored_files(root) | {'archive/complete.json': canonical({'receiptId': receipt['receiptId']})}
            _validate_snapshot(plan, prospective, secrets, require_complete=True)
            atomic_write(root / 'archive' / 'complete.json', prospective['archive/complete.json'])
            return receipt
    except (OSError, KeyError, TypeError, ValueError):
        raise SourceError('Private archive storage or verification failed; prior receipt retained') from None


def verify_archived_bundle(plan, root, secrets=()):
    """Recheck all source bytes and require matching wholly successful journal/bundle/receipt."""
    plan = batch.validate_plan(plan)
    try:
        return _validate_snapshot(plan, _stored_files(Path(root)), secrets, require_complete=True)['receipt']
    except (OSError, KeyError, TypeError, ValueError):
        raise SourceError('Private archive verification failed') from None


def restore_archived_snapshot(plan, files, root, key, evidence_secrets=()):
    """Validate every file and relationship in memory before an empty-destination restore."""
    plan = batch.validate_plan(plan)
    batch.validate_key(key)
    secrets = (key, *evidence_secrets)
    root = Path(root)
    require(not root.is_symlink() and (not root.exists() or (root.is_dir() and not any(root.iterdir()))), 'Archive restore requires an empty destination')
    try:
        _validate_snapshot(plan, files, secrets)
        def order(name):
            priority = (0 if name.startswith(('objects/', 'raw/')) else 1 if name.startswith('bundles/')
                        else 2 if name.endswith('/progress.json') else 3 if name.startswith('batches/')
                        else 5 if name == 'archive/complete.json' else 4)
            return priority, name
        with batch.writer(root):
            for name in sorted(files, key=order):
                atomic_write(root / name, files[name])
    except (OSError, KeyError, TypeError, ValueError):
        raise SourceError('Private archive restore failed') from None


def main():
    parser = argparse.ArgumentParser(description='Acquire a private raw-response archive; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('pipeline/output/archive'))
    parser.add_argument('--refresh', action='store_true', help='Refetch every bounded plan slot')
    parser.add_argument('--resume-run', type=int, help='Restore a completed trusted main archived-acquisition run')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', 'Vasuki8/us-trade-explorer'))
    args = parser.parse_args()
    try:
        plan = batch.validate_plan(batch.read(args.plan))
        key, token = os.environ.get('CENSUS_API_KEY', ''), os.environ.get('GH_TOKEN', '')
        batch.validate_key(key)
        if args.resume_run is not None:
            from pipeline.restore import SnapshotError, fetch_archived_snapshot
            try:
                files = fetch_archived_snapshot(args.repository, args.resume_run, token)
            except SnapshotError:
                raise SourceError('Trusted private archive download failed') from None
            restore_archived_snapshot(plan, files, args.output, key, evidence_secrets=(token,))
        receipt = run_archived_batch(plan, args.output, key, refresh=args.refresh, evidence_secrets=(token,))
        print(f"Private archive validated: {len(plan['partitions'])} requested partitions, {len(receipt['rawObjects'])} retained responses; publication remains blocked.")
    except (SourceError, OSError):
        parser.exit(1, 'Private archive failed; inspect the sanitized journal. No public release was activated.\n')


if __name__ == '__main__':
    main()
