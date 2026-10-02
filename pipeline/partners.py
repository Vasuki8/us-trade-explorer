"""Bounded private DET discovery. Observations never approve an additive inventory."""
import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re

from pipeline.batch import BASIS, atomic_write, validate_key, writer
from pipeline.candidates import BLOCKERS as CANDIDATE_BLOCKERS
from pipeline.candidates import canonical, decode, digest, hash_text, keys, require, timestamp
from pipeline.census import DIAGNOSTIC_CATEGORIES, PATHS, SourceError, aggregate_dimensions, fetch_candidate, parse_rows

MAX_ROWS = 500
MAX_OBJECT_BYTES = 512 * 1024
MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024
MAX_SNAPSHOT_FILES = 20
MAX_ZIP_ENTRIES = 24
BLOCKERS = [
    'Observed DET partners only; additive leaf inventory not approved',
    'Official API vintage and revision evidence not attached',
    'Full control reconciliation not verified',
    'Classification comparability not verified',
]
RAW_PATH = re.compile(r'raw/([a-f0-9]{64})\.json')
SCAN_PATH = re.compile(r'scans/([a-f0-9]{64})\.json')
RECEIPT_PATH = re.compile(r'receipts/([a-f0-9]{64})\.json')
CANDIDATE_FIELDS = ['schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash', 'candidateId',
                    'state', 'source', 'scope', 'officialReleaseDate', 'officialRevisionDate',
                    'ingestedAt', 'rows', 'publicationBlockers']
SCAN_FIELDS = ['schemaVersion', 'planId', 'basis', 'flow', 'period', 'product', 'summaryLevel',
               'sourceQuery', 'sourceHash', 'candidateId', 'source', 'scope', 'officialReleaseDate',
               'officialRevisionDate', 'ingestedAt', 'rows', 'observedPartners', 'state', 'coverage',
               'leafInventoryApproved', 'apiVintageVerified', 'publicationReady', 'publicationBlockers', 'scanId']


def validate_plan(plan):
    keys(plan, ['schemaVersion', 'basis', 'period', 'product', 'summaryLevel', 'flows'])
    require(type(plan['schemaVersion']) is int and plan['schemaVersion'] == 1, 'Unsupported discovery plan')
    require(plan['basis'] == BASIS and plan['period'] == '2026-07' and plan['product'] == '09'
            and plan['summaryLevel'] == 'DET', 'Discovery plan scope mismatch')
    require(type(plan['flows']) is list and len(plan['flows']) == 2
            and all(type(flow) is str for flow in plan['flows'])
            and sorted(plan['flows']) == ['exports', 'imports'], 'Discovery plan flow mismatch')
    return {**plan, 'flows': ['exports', 'imports']}


def _scope(plan, flow):
    plan = validate_plan(plan)
    require(type(flow) is str and flow in plan['flows'], 'Unsupported discovery flow')
    return plan


def _query(flow, plan):
    prefix, variable = ('I', 'GEN_VAL_MO') if flow == 'imports' else ('E', 'ALL_VAL_MO')
    return {'get': f'{prefix}_COMMODITY_SDESC,CTY_NAME,{variable}', 'YEAR': plan['period'][:4],
            'MONTH': plan['period'][5:], 'COMM_LVL': 'HS2', f'{prefix}_COMMODITY': plan['product'],
            'CTY_CODE': '*', **aggregate_dimensions(flow), 'SUMMARY_LVL': 'DET'}


def _decode(raw, secrets):
    value = decode(raw, secrets, maximum=MAX_OBJECT_BYTES)
    secret_values = (secrets,) if type(secrets) is str else secrets or ()
    require(all(type(secret) is str for secret in secret_values), 'Invalid evidence safety inputs')
    # Examine decoded strings directly: JSON serialization reescapes quote and
    # backslash characters present in an otherwise valid credential.
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is str:
            require(all(not secret or secret not in item for secret in secret_values), 'Evidence safety check failed')
        elif type(item) is dict:
            pending.extend(item.keys())
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
    return value


def _object(value, secrets):
    raw = canonical(value)
    require(0 < len(raw) <= MAX_OBJECT_BYTES, 'Oversized discovery object')
    return _decode(raw, secrets)


def _raw_rows(raw, plan, flow, secrets):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_OBJECT_BYTES, 'Missing or oversized discovery response')
    table = _decode(raw, secrets)
    require(type(table) is list and 2 <= len(table) <= MAX_ROWS + 1, 'Empty or oversized discovery table')
    rows = parse_rows(table, flow, plan['period'], expected_summary='DET')
    require(all(row['product'] == plan['product'] for row in rows), 'Discovery response scope mismatch')
    for row in rows:
        for field in ('description', 'partnerName'):
            require(all(ord(character) >= 32 and ord(character) != 127 for character in row[field]),
                    'Invalid discovery description')
    return rows


def _validate_candidate(candidate, raw, plan, flow, secrets):
    candidate = _object(candidate, secrets)
    keys(candidate, CANDIDATE_FIELDS)
    require(type(candidate['schemaVersion']) is int and candidate['schemaVersion'] == 2)
    require(candidate['flow'] == flow and candidate['period'] == plan['period']
            and candidate['state'] == 'candidate', 'Discovery candidate scope mismatch')
    require(candidate['source'] == 'https://api.census.gov' + PATHS[flow], 'Unexpected discovery source')
    require(candidate['scope'] == {'commodityLevel': 'HS2', 'product': plan['product'],
                                   'partner': '*', 'coverage': 'unverified'}, 'Discovery scope mismatch')
    require(candidate['sourceQuery'] == _query(flow, plan), 'Discovery query mismatch')
    require(candidate['officialReleaseDate'] is None and candidate['officialRevisionDate'] is None,
            'Unsupported discovery official dates')
    require(candidate['publicationBlockers'] == CANDIDATE_BLOCKERS, 'Missing candidate publication blockers')
    timestamp(candidate['ingestedAt'])
    hash_text(candidate['sourceHash'])
    hash_text(candidate['candidateId'])
    identity = {field: candidate[field] for field in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')}
    require(candidate['candidateId'] == digest(identity), 'Discovery candidate identity mismatch')
    require(type(raw) is bytes and hashlib.sha256(raw).hexdigest() == candidate['sourceHash'],
            'Discovery source checksum mismatch')
    rows = _raw_rows(raw, plan, flow, secrets)
    require(type(candidate['rows']) is list and candidate['rows'] == rows,
            'Discovery raw observations differ from candidate')
    return candidate


def _flags():
    return {'state': 'private-partner-discovery', 'coverage': 'observed-partners-only',
            'leafInventoryApproved': False, 'apiVintageVerified': False, 'publicationReady': False,
            'publicationBlockers': list(BLOCKERS)}


def normalize_scan(candidate, raw, *, plan, flow, secrets=()):
    """Validate candidate and independently parse strict exact bytes before deriving observations."""
    plan = _scope(plan, flow)
    candidate = _validate_candidate(candidate, raw, plan, flow, secrets)
    rows = sorted(candidate['rows'], key=lambda row: row['partnerCode'])
    scan = {'schemaVersion': 1, 'planId': digest(plan), 'basis': BASIS, 'flow': flow,
            'period': plan['period'], 'product': plan['product'], 'summaryLevel': 'DET',
            **{field: candidate[field] for field in ('sourceQuery', 'sourceHash', 'candidateId', 'source',
                                                     'scope', 'officialReleaseDate', 'officialRevisionDate', 'ingestedAt')},
            'rows': rows,
            'observedPartners': [{'code': row['partnerCode'], 'name': row['partnerName'],
                                  'role': 'world-control' if row['partnerCode'] == '-' else 'unreviewed-detail'}
                                 for row in rows], **_flags()}
    scan['scanId'] = digest({field: value for field, value in scan.items() if field != 'ingestedAt'})
    _object(scan, secrets)
    return scan


def _validate_scan(scan, raw, plan, flow, secrets):
    keys(scan, SCAN_FIELDS)
    require(type(scan['schemaVersion']) is int and scan['schemaVersion'] == 1)
    require(all(type(scan[field]) is bool for field in ('leafInventoryApproved', 'apiVintageVerified', 'publicationReady')),
            'Invalid discovery approval flags')
    # The source table retains its original order; stored observations are sorted.
    rows = _raw_rows(raw, plan, flow, secrets)
    candidate = {'schemaVersion': 2,
                 **{field: scan[field] for field in ('flow', 'period', 'sourceQuery', 'sourceHash', 'candidateId',
                                                     'source', 'scope', 'officialReleaseDate', 'officialRevisionDate', 'ingestedAt')},
                 'state': 'candidate', 'rows': rows, 'publicationBlockers': CANDIDATE_BLOCKERS}
    expected = normalize_scan(candidate, raw, plan=plan, flow=flow, secrets=secrets)
    require(scan == expected, 'Stored discovery scan mismatch')
    return scan


def _receipt(plan, flow, scan, object_bytes, raw):
    receipt = {'schemaVersion': 1, 'planId': digest(plan), 'basis': BASIS, 'flow': flow,
               'scanId': scan['scanId'], 'objectHash': hashlib.sha256(object_bytes).hexdigest(),
               'sourceHash': scan['sourceHash'], 'rawHash': hashlib.sha256(raw).hexdigest(),
               'rowCount': len(scan['rows']), 'partnerCount': len(scan['observedPartners']), **_flags()}
    receipt['receiptId'] = digest(receipt)
    return receipt


def _journal(plan, flow, generation, *, state='pending', scan_id=None, receipt_id=None,
             category=None, http_status=None, attempted_at=None):
    return {'schemaVersion': 1, 'planId': digest(plan), 'flow': flow, 'generation': generation,
            'state': state, 'scanId': scan_id, 'receiptId': receipt_id, 'category': category,
            'httpStatus': http_status, 'attemptedAt': attempted_at}


def _validate_journal(value, plan, flow):
    keys(value, ['schemaVersion', 'planId', 'flow', 'generation', 'state', 'scanId', 'receiptId',
                 'category', 'httpStatus', 'attemptedAt'])
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['planId'] == digest(plan) and value['flow'] == flow, 'Discovery journal scope mismatch')
    require(type(value['generation']) is int and 1 <= value['generation'] <= 1_000_000,
            'Invalid discovery generation')
    require(value['state'] in ('pending', 'successful', 'failed'), 'Invalid discovery attempt state')
    timestamp(value['attemptedAt'])
    if value['state'] == 'successful':
        hash_text(value['scanId'])
        hash_text(value['receiptId'])
        require(value['category'] is None and value['httpStatus'] is None)
    else:
        require(value['scanId'] is None and value['receiptId'] is None, 'Unsuccessful discovery has observation references')
        if value['state'] == 'pending':
            require(value['category'] is None and value['httpStatus'] is None)
        else:
            require(type(value['category']) is str and value['category'] in DIAGNOSTIC_CATEGORIES,
                    'Invalid discovery failure category')
            require(value['httpStatus'] is None or (type(value['httpStatus']) is int and 100 <= value['httpStatus'] <= 599))
    return value


def _inventory(files):
    require(type(files) is dict and 1 <= len(files) <= MAX_SNAPSHOT_FILES, 'Invalid discovery inventory')
    require(all(type(name) is str and type(raw) is bytes and 0 < len(raw) <= MAX_OBJECT_BYTES
                for name, raw in files.items()), 'Invalid or oversized discovery object')
    require(sum(map(len, files.values())) <= MAX_SNAPSHOT_BYTES, 'Oversized discovery snapshot')


def validate_snapshot(plan, flow, files, secrets=(), require_complete=False):
    """Revalidate all historical evidence, orphans and current attempt without any writes."""
    plan = _scope(plan, flow)
    _inventory(files)
    raws, scans, scan_bytes, receipts, pointer, journal = {}, {}, {}, {}, None, None
    for name, raw in files.items():
        raw_match, scan_match, receipt_match = RAW_PATH.fullmatch(name), SCAN_PATH.fullmatch(name), RECEIPT_PATH.fullmatch(name)
        if raw_match:
            source_hash = raw_match.group(1)
            require(hashlib.sha256(raw).hexdigest() == source_hash, 'Discovery raw filename checksum mismatch')
            _raw_rows(raw, plan, flow, secrets)
            raws[source_hash] = raw
            continue
        value = _decode(raw, secrets)
        if scan_match:
            require(type(value) is dict and value.get('scanId') == scan_match.group(1), 'Discovery scan filename mismatch')
            scans[scan_match.group(1)] = value
            scan_bytes[scan_match.group(1)] = raw
        elif receipt_match:
            require(type(value) is dict and value.get('receiptId') == receipt_match.group(1), 'Discovery receipt filename mismatch')
            receipts[receipt_match.group(1)] = value
        elif name == 'progress.json':
            journal = _validate_journal(value, plan, flow)
        elif name == 'complete.json':
            keys(value, ['receiptId'])
            hash_text(value['receiptId'])
            pointer = value
        else:
            raise SourceError('Unexpected discovery snapshot path')
    for scan in scans.values():
        source_hash = scan.get('sourceHash')
        require(type(source_hash) is str and source_hash in raws, 'Missing historical discovery response')
        _validate_scan(scan, raws[source_hash], plan, flow, secrets)
    for receipt_id, receipt in receipts.items():
        scan_id = receipt.get('scanId')
        require(type(scan_id) is str and scan_id in scans, 'Missing discovery receipt scan')
        scan = scans[scan_id]
        expected = _receipt(plan, flow, scan, scan_bytes[scan_id], raws[scan['sourceHash']])
        keys(receipt, expected)
        require(type(receipt['schemaVersion']) is int and type(receipt['rowCount']) is int
                and type(receipt['partnerCount']) is int
                and all(type(receipt[field]) is bool for field in ('leafInventoryApproved', 'apiVintageVerified', 'publicationReady'))
                and receipt == expected, 'Discovery receipt mismatch')
    require(pointer is None or pointer['receiptId'] in receipts, 'Missing active discovery receipt')
    if journal is not None and journal['state'] == 'successful':
        require(journal['receiptId'] in receipts and receipts[journal['receiptId']]['scanId'] == journal['scanId'],
                'Missing successful discovery journal evidence')
    receipt = None if pointer is None else receipts[pointer['receiptId']]
    complete = receipt is not None and journal is not None and journal['state'] == 'successful' \
        and journal['receiptId'] == receipt['receiptId'] and journal['scanId'] == receipt['scanId']
    require(not require_complete or complete, 'Discovery receipt and current successful generation do not match')
    return {'raws': raws, 'scans': scans, 'receipts': receipts, 'journal': journal,
            'pointer': pointer, 'receipt': receipt, 'complete': complete}


def _unsafe(path):
    return path.is_symlink() or bool(getattr(path, 'is_junction', lambda: False)())


def _safe_root(root):
    require(not any(_unsafe(path) for path in (root, *root.parents)), 'Unsafe discovery destination')
    require(not root.exists() or root.is_dir(), 'Invalid discovery destination')


def _stored_files(root):
    _safe_root(root)
    if not root.exists():
        return {}
    files = {}
    for path in root.rglob('*'):
        require(not _unsafe(path), 'Unsafe discovery object')
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            require(name in ('raw', 'scans', 'receipts'), 'Unexpected discovery directory')
            continue
        require(path.is_file(), 'Unsafe discovery object')
        if path.name.startswith('.pending-') or name == 'batch.lock':
            continue
        require(path.stat().st_size <= MAX_OBJECT_BYTES, 'Oversized discovery object')
        files[name] = path.read_bytes()
        require(len(files) <= MAX_SNAPSHOT_FILES and sum(map(len, files.values())) <= MAX_SNAPSHOT_BYTES,
                'Oversized discovery store')
    return files


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def run_partner_scan(plan, flow, root, key, refresh=False, evidence_secrets=()):
    """Acquire one bounded flow after validating every cached object; preserve prior pointers."""
    plan = _scope(plan, flow)
    validate_key(key)
    require(type(refresh) is bool, 'Invalid discovery refresh')
    secrets, root = (key, *evidence_secrets), Path(root)
    try:
        _safe_root(root)
        with writer(root):
            files = _stored_files(root)
            state = validate_snapshot(plan, flow, files, secrets) if files else None
            if state is not None and state['complete'] and not refresh:
                return state['receipt']
            previous = state['journal'] if state else None
            generation = (previous['generation'] + 1 if refresh and previous and previous['state'] == 'successful'
                          else previous['generation'] if previous else 1)
            attempted_at = _now()
            journal = _journal(plan, flow, generation, attempted_at=attempted_at)
            prospective = files | {'progress.json': canonical(journal)}
            validate_snapshot(plan, flow, prospective, secrets)
            atomic_write(root / 'progress.json', prospective['progress.json'])
            try:
                captured = []
                candidate = fetch_candidate(flow, plan['period'], key, product=plan['product'], partner='*',
                                            summary='DET', response_limit=MAX_OBJECT_BYTES,
                                            row_limit=MAX_ROWS, capture=captured.append)
                require(len(captured) == 1, 'Discovery source capture did not complete')
                raw = captured[0]
                scan = normalize_scan(candidate, raw, plan=plan, flow=flow, secrets=secrets)
                scan_path, raw_path = 'scans/' + scan['scanId'] + '.json', 'raw/' + scan['sourceHash'] + '.json'
                if scan_path in files:
                    previous_scan = _decode(files[scan_path], secrets)
                    require({k: v for k, v in previous_scan.items() if k != 'ingestedAt'} ==
                            {k: v for k, v in scan.items() if k != 'ingestedAt'}, 'Discovery scan identity collision')
                    scan = previous_scan
                    scan_raw = files[scan_path]
                else:
                    scan_raw = canonical(scan)
                require(raw_path not in files or files[raw_path] == raw, 'Discovery raw identity collision')
                receipt = _receipt(plan, flow, scan, scan_raw, raw)
                receipt_path = 'receipts/' + receipt['receiptId'] + '.json'
                receipt_raw = files.get(receipt_path, canonical(receipt))
                successful = _journal(plan, flow, generation, state='successful', scan_id=scan['scanId'],
                                      receipt_id=receipt['receiptId'], attempted_at=attempted_at)
                # Preflight all prospective bytes before any new evidence, success state or activation.
                prospective = files | {raw_path: raw, scan_path: scan_raw, receipt_path: receipt_raw,
                                       'progress.json': canonical(successful),
                                       'complete.json': canonical({'receiptId': receipt['receiptId']})}
                validate_snapshot(plan, flow, prospective, secrets, require_complete=True)
                for name in (raw_path, scan_path, receipt_path):
                    if name not in files:
                        atomic_write(root / name, prospective[name])
                atomic_write(root / 'progress.json', prospective['progress.json'])
                atomic_write(root / 'complete.json', prospective['complete.json'])
                return receipt
            except Exception as error:
                # Exceptions can contain reflected credentials; copy allowlisted diagnostics only.
                category = error.category if isinstance(error, SourceError) else 'validation_failed'
                status = error.http_status if isinstance(error, SourceError) else None
                failed = _journal(plan, flow, generation, state='failed', category=category,
                                  http_status=status, attempted_at=attempted_at)
                atomic_write(root / 'progress.json', canonical(failed))
                raise SourceError('Private discovery failed; prior successful receipt retained',
                                  category=category, http_status=status) from None
    except (OSError, ValueError, TypeError, KeyError):
        raise SourceError('Private discovery storage or verification failed; prior receipt retained') from None


def verify_partner_scan(plan, flow, root, secrets=()):
    plan = _scope(plan, flow)
    try:
        return validate_snapshot(plan, flow, _stored_files(Path(root)), secrets, require_complete=True)['receipt']
    except (OSError, ValueError, TypeError, KeyError):
        raise SourceError('Private discovery verification failed') from None


def restore_partner_snapshot(plan, flow, files, root, key, evidence_secrets=()):
    """Validate all bounded evidence and paths before writing into an empty destination."""
    plan = _scope(plan, flow)
    validate_key(key)
    root = Path(root)
    try:
        _safe_root(root)
        require(not root.exists() or not any(root.iterdir()), 'Discovery restore requires an empty destination')
        validate_snapshot(plan, flow, files, (key, *evidence_secrets))
        def order(name):
            return (0 if name.startswith('raw/') else 1 if name.startswith('scans/') else
                    2 if name.startswith('receipts/') else 3 if name == 'progress.json' else 4, name)
        with writer(root):
            for name in sorted(files, key=order):
                atomic_write(root / name, files[name])
    except (OSError, ValueError, TypeError, KeyError):
        raise SourceError('Private discovery restore failed') from None


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Private partner discovery arguments are invalid.\n')


def main():
    parser = _SafeArgumentParser(prog='pipeline.partners', description='Acquire a bounded private DET partner scan; does not publish')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--flow', choices=('imports', 'exports'), required=True)
    parser.add_argument('--output', type=Path, required=True, help='One flow-specific private store root')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--resume-run', type=int)
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', 'Vasuki8/us-trade-explorer'))
    args = parser.parse_args()
    try:
        key, token = os.environ.get('CENSUS_API_KEY', ''), os.environ.get('GH_TOKEN', '')
        validate_key(key)
        require(args.plan.is_file() and not _unsafe(args.plan) and args.plan.stat().st_size <= MAX_OBJECT_BYTES,
                'Missing or oversized discovery plan')
        plan = validate_plan(_decode(args.plan.read_bytes(), (key, token)))
        if args.resume_run is not None:
            from pipeline.restore import SnapshotError, fetch_partner_snapshot
            try:
                files = fetch_partner_snapshot(args.repository, args.resume_run, token)
            except SnapshotError:
                raise SourceError('Trusted private discovery download failed') from None
            restore_partner_snapshot(plan, args.flow, files, args.output, key, evidence_secrets=(token,))
        receipt = run_partner_scan(plan, args.flow, args.output, key, refresh=args.refresh, evidence_secrets=(token,))
        print(f"Private partner discovery validated: {receipt['rowCount']} observed rows, "
              f"{receipt['partnerCount']} observed partners; publication remains blocked.")
    except Exception:
        parser.exit(1, 'Private partner discovery failed; inspect the sanitized journal. Publication remains blocked.\n')


if __name__ == '__main__':
    main()
