"""Bounded, resumable private Census bundles. This module never activates releases."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import tempfile

from pipeline.candidates import MAX_FILE_BYTES, canonical, decode, digest, hash_text, keys, require, timestamp, validate_candidate
from pipeline.census import DIAGNOSTIC_CATEGORIES, SourceError, fetch_candidate, validate_period

BASIS = 'census-monthly-goods-nsa-usd-v1'
MAX_PARTITIONS = 8
MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024
MAX_SNAPSHOT_FILES = 48
BUNDLE_BLOCKERS = ['Requested partitions only; global inventory unverified', 'Official publication and revision evidence not attached', 'Control reconciliation not verified', 'Classification comparability not verified']


def validate_slot(slot):
    keys(slot, ['flow', 'period', 'product', 'partner'])
    require(slot['flow'] in ('imports', 'exports'), 'Unsupported batch flow')
    validate_period(slot['period'])
    require(type(slot['product']) is str and re.fullmatch('[0-9]{2}', slot['product']), 'Batch requires an explicit HS2 product')
    require(type(slot['partner']) is str and re.fullmatch('(?:[0-9]{4}|-)', slot['partner']), 'Batch requires an explicit partner or world control')


def validate_plan(plan):
    keys(plan, ['schemaVersion', 'basis', 'partitions'])
    require(type(plan['schemaVersion']) is int and plan['schemaVersion'] == 1 and plan['basis'] == BASIS, 'Unsupported batch plan')
    require(type(plan['partitions']) is list and 1 <= len(plan['partitions']) <= MAX_PARTITIONS, 'Invalid batch partition count')
    slots = []
    for slot in plan['partitions']:
        validate_slot(slot)
        slots.append(dict(slot))
    slots.sort(key=lambda s: (s['flow'], s['period'], s['product'], s['partner']))
    require(len({digest(s) for s in slots}) == len(slots), 'Duplicate batch partitions')
    return {'schemaVersion': 1, 'basis': BASIS, 'partitions': slots}


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read(path, secret=None):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_FILE_BYTES, 'Missing or oversized evidence object')
    return decode(path.read_bytes(), secret)


@contextmanager
def writer(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / 'batch.lock'
    try:
        with lock.open('x') as output:
            output.write(str(os.getpid()))
    except FileExistsError:
        raise SourceError('Another batch writer holds the lock') from None
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def pending(slot):
    return {'slot': slot, 'state': 'pending', 'candidateId': None, 'objectHash': None, 'category': None, 'httpStatus': None, 'attemptedAt': None}


def validate_journal(journal, plan):
    keys(journal, ['schemaVersion', 'planId', 'entries'])
    require(type(journal['schemaVersion']) is int and journal['schemaVersion'] == 1 and journal['planId'] == digest(plan), 'Journal plan mismatch')
    require(type(journal['entries']) is list and len(journal['entries']) == len(plan['partitions']), 'Incomplete journal inventory')
    for entry, slot in zip(journal['entries'], plan['partitions']):
        keys(entry, ['slot', 'state', 'candidateId', 'objectHash', 'category', 'httpStatus', 'attemptedAt'])
        require(entry['slot'] == slot and entry['state'] in ('pending', 'successful', 'failed'), 'Invalid journal slot')
        if entry['state'] == 'successful':
            hash_text(entry['candidateId'])
            hash_text(entry['objectHash'])
            require(entry['category'] is None and entry['httpStatus'] is None)
            timestamp(entry['attemptedAt'])
        else:
            require(entry['candidateId'] is None and entry['objectHash'] is None)
            if entry['state'] == 'pending':
                require(entry['category'] is None and entry['httpStatus'] is None and entry['attemptedAt'] is None)
            else:
                require(type(entry['category']) is str and entry['category'] in DIAGNOSTIC_CATEGORIES)
                require(entry['httpStatus'] is None or (type(entry['httpStatus']) is int and 100 <= entry['httpStatus'] <= 599))
                timestamp(entry['attemptedAt'])
    return journal


def referenced_candidate(entry, objects, secret=None):
    candidate_id = entry['candidateId']
    hash_text(candidate_id)
    hash_text(entry['objectHash'])
    raw = objects(candidate_id)
    require(hashlib.sha256(raw).hexdigest() == entry['objectHash'], 'Stored candidate checksum mismatch')
    candidate = validate_candidate(decode(raw, secret), entry['slot'])
    require(candidate['candidateId'] == candidate_id, 'Stored candidate identity mismatch')
    return candidate


def object_bytes(root, identity):
    path = root / 'objects' / (identity + '.json')
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_FILE_BYTES, 'Missing candidate object')
    return path.read_bytes()


def validate_bundle(bundle, plan, objects, secret=None):
    keys(bundle, ['schemaVersion', 'bundleId', 'planId', 'basis', 'state', 'coverage', 'officialReleaseDate', 'officialRevisionDate', 'publicationBlockers', 'partitions'])
    require(type(bundle['schemaVersion']) is int and bundle['schemaVersion'] == 1 and bundle['planId'] == digest(plan) and bundle['basis'] == BASIS)
    require(bundle['state'] == 'candidate' and bundle['coverage'] == 'requested-partitions-only')
    require(bundle['officialReleaseDate'] is None and bundle['officialRevisionDate'] is None and bundle['publicationBlockers'] == BUNDLE_BLOCKERS)
    hash_text(bundle['bundleId'])
    require(digest({k: v for k, v in bundle.items() if k != 'bundleId'}) == bundle['bundleId'], 'Bundle identity mismatch')
    require(type(bundle['partitions']) is list and len(bundle['partitions']) == len(plan['partitions']), 'Incomplete bundle inventory')
    for entry, slot in zip(bundle['partitions'], plan['partitions']):
        keys(entry, ['slot', 'candidateId', 'objectHash', 'rowCount'])
        require(entry['slot'] == slot and type(entry['rowCount']) is int and entry['rowCount'] == 1, 'Bundle slot mismatch')
        referenced_candidate(entry, objects, secret)
    return bundle


def verify_bundle(plan, root):
    plan = validate_plan(plan)
    root = Path(root)
    try:
        pointer = read(root / 'batches' / digest(plan) / 'complete.json')
        keys(pointer, ['bundleId'])
        hash_text(pointer['bundleId'])
        bundle = read(root / 'bundles' / (pointer['bundleId'] + '.json'))
        require(bundle['bundleId'] == pointer['bundleId'], 'Bundle pointer mismatch')
        return validate_bundle(bundle, plan, lambda identity: object_bytes(root, identity))
    except (OSError, KeyError, TypeError):
        raise SourceError('Private bundle verification failed') from None


def save_candidate(root, candidate, slot, secret):
    raw = canonical(candidate)
    validate_candidate(decode(raw, secret), slot)
    path = root / 'objects' / (candidate['candidateId'] + '.json')
    if path.exists():
        previous = read(path, secret)
        validate_candidate(previous, slot)
        require(previous['candidateId'] == candidate['candidateId'])
        require({k: v for k, v in previous.items() if k != 'ingestedAt'} == {k: v for k, v in candidate.items() if k != 'ingestedAt'}, 'Candidate identity collision')
        raw = path.read_bytes()
    else:
        atomic_write(path, raw)
    return {'slot': slot, 'candidateId': candidate['candidateId'], 'objectHash': hashlib.sha256(raw).hexdigest(), 'rowCount': 1}


def validate_key(key):
    require(type(key) is str and 0 < len(key) <= 256 and not any(c.isspace() for c in key), 'CENSUS_API_KEY is missing or invalid')


def run_batch(plan, root, key, refresh=False, evidence_secrets=()):
    plan = validate_plan(plan)
    validate_key(key)
    secrets = (key, *evidence_secrets)
    root = Path(root)
    plan_id = digest(plan)
    progress_path = root / 'batches' / plan_id / 'progress.json'
    try:
        with writer(root):
            (root / 'objects').mkdir(exist_ok=True)
            (root / 'bundles').mkdir(exist_ok=True)
            journal = {'schemaVersion': 1, 'planId': plan_id, 'entries': [pending(slot) for slot in plan['partitions']]}
            if progress_path.exists():
                previous = validate_journal(read(progress_path, secrets), plan)
                # Verify all cached successes before issuing any network request.
                for entry in previous['entries']:
                    if entry['state'] == 'successful':
                        referenced_candidate(entry, lambda identity: object_bytes(root, identity), secrets)
                if not refresh:
                    journal = previous
            atomic_write(progress_path, canonical(journal))
            for entry in journal['entries']:
                if entry['state'] == 'successful':
                    continue
                slot = entry['slot']
                attempted = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                try:
                    candidate = fetch_candidate(slot['flow'], slot['period'], key, product=slot['product'], partner=slot['partner'])
                    reference = save_candidate(root, candidate, slot, secrets)
                except SourceError as error:
                    entry.update(state='failed', candidateId=None, objectHash=None, category=error.category, httpStatus=error.http_status, attemptedAt=attempted)
                    atomic_write(progress_path, canonical(journal))
                    raise SourceError('Batch partition failed; valid evidence retained', category=error.category, http_status=error.http_status) from None
                entry.update(state='successful', candidateId=reference['candidateId'], objectHash=reference['objectHash'], category=None, httpStatus=None, attemptedAt=attempted)
                atomic_write(progress_path, canonical(journal))
            bundle = {'schemaVersion': 1, 'planId': plan_id, 'basis': BASIS, 'state': 'candidate', 'coverage': 'requested-partitions-only', 'officialReleaseDate': None, 'officialRevisionDate': None, 'publicationBlockers': BUNDLE_BLOCKERS, 'partitions': [{key: entry[key] for key in ('slot', 'candidateId', 'objectHash')} | {'rowCount': 1} for entry in journal['entries']]}
            bundle['bundleId'] = digest(bundle)
            validate_bundle(bundle, plan, lambda identity: object_bytes(root, identity), secrets)
            bundle_path = root / 'bundles' / (bundle['bundleId'] + '.json')
            if bundle_path.exists():
                require(read(bundle_path, secrets) == bundle, 'Bundle identity collision')
            else:
                atomic_write(bundle_path, canonical(bundle))
            atomic_write(root / 'batches' / plan_id / 'complete.json', canonical({'bundleId': bundle['bundleId']}))
            return bundle
    except (OSError, KeyError, TypeError):
        raise SourceError('Batch storage or state verification failed; prior complete evidence retained') from None


def restore_snapshot(plan, files, root, key, evidence_secrets=()):
    plan = validate_plan(plan)
    validate_key(key)
    secrets = (key, *evidence_secrets)
    require(type(files) is dict and 1 <= len(files) <= MAX_SNAPSHOT_FILES and all(type(v) is bytes for v in files.values()), 'Invalid snapshot inventory')
    require(sum(map(len, files.values())) <= MAX_SNAPSHOT_BYTES, 'Oversized snapshot')
    root = Path(root)
    require(not root.exists() or not any(root.iterdir()), 'Restore requires an empty destination')
    plan_id = digest(plan)
    objects, bundles, journal, pointer = {}, {}, None, None
    # Validate ALL files and references in memory before making a filesystem write.
    for name, raw in files.items():
        require(type(name) is str, 'Invalid snapshot filename')
        value = decode(raw, secrets)
        if re.fullmatch(r'objects/[a-f0-9]{64}\.json', name):
            require(type(value) is dict and type(value.get('scope')) is dict)
            slot = {field: value.get(field) for field in ('flow', 'period')}
            slot.update(product=value['scope'].get('product'), partner=value['scope'].get('partner'))
            require(slot in plan['partitions'], 'Snapshot plan mismatch')
            validate_candidate(value, slot)
            require(name == 'objects/' + value['candidateId'] + '.json', 'Snapshot identity mismatch')
            objects[value['candidateId']] = raw
        elif re.fullmatch(r'bundles/[a-f0-9]{64}\.json', name):
            require(type(value) is dict and name == 'bundles/' + str(value.get('bundleId')) + '.json', 'Snapshot identity mismatch')
            bundles[value['bundleId']] = value
        elif name == f'batches/{plan_id}/progress.json':
            journal = validate_journal(value, plan)
        elif name == f'batches/{plan_id}/complete.json':
            keys(value, ['bundleId'])
            hash_text(value['bundleId'])
            pointer = value
        else:
            raise SourceError('Unexpected snapshot path')
    require(journal is not None, 'Missing snapshot journal')
    def lookup(identity):
        require(identity in objects, 'Missing snapshot object')
        return objects[identity]
    for entry in journal['entries']:
        if entry['state'] == 'successful':
            referenced_candidate(entry, lookup, secrets)
    for bundle in bundles.values():
        validate_bundle(bundle, plan, lookup, secrets)
    require(pointer is None or pointer['bundleId'] in bundles, 'Missing snapshot bundle')
    try:
        with writer(root):
            for name in sorted(files, key=lambda p: (0 if p.startswith('objects/') else 1 if p.startswith('bundles/') else 2 if p.endswith('/progress.json') else 3, p)):
                atomic_write(root / name, files[name])
    except OSError:
        raise SourceError('Snapshot storage failed') from None


def main():
    parser = argparse.ArgumentParser(description='Acquire a private bounded batch; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('pipeline/output/batch'))
    parser.add_argument('--refresh', action='store_true', help='Re-fetch every slot to detect source revisions')
    parser.add_argument('--resume-run', type=int, help='Restore a completed trusted main batch run before continuing')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', 'Vasuki8/us-trade-explorer'))
    args = parser.parse_args()
    try:
        plan = validate_plan(read(args.plan))
        key = os.environ.get('CENSUS_API_KEY', '')
        validate_key(key)
        token = os.environ.get('GH_TOKEN', '')
        if args.resume_run is not None:
            from pipeline.restore import SnapshotError, fetch_snapshot
            try:
                snapshot = fetch_snapshot(args.repository, args.resume_run, token)
            except SnapshotError:
                raise SourceError('Trusted snapshot download failed') from None
            restore_snapshot(plan, snapshot, args.output, key, evidence_secrets=(token,))
        bundle = run_batch(plan, args.output, key, refresh=args.refresh, evidence_secrets=(token,))
        print(f"Private batch validated: {len(bundle['partitions'])} requested partitions; publication remains blocked.")
    except (SourceError, OSError):
        parser.exit(1, 'Private batch failed; inspect the sanitized journal. No new release was activated.\n')


if __name__ == '__main__':
    main()
