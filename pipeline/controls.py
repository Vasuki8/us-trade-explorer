"""Private selected-market checks. A subset check cannot activate a public release."""
import argparse
import os
from pathlib import Path
import re

from pipeline.batch import BASIS, atomic_write, object_bytes, read, referenced_candidate, restore_snapshot, validate_key, validate_plan, verify_bundle, writer
from pipeline.candidates import canonical, decode, digest, keys, require, timestamp
from pipeline.census import SourceError, validate_period
from pipeline.publication import archive_publication, verify_publication
from pipeline.restore import SnapshotError, fetch_snapshot

SOURCE_ROOT = Path(__file__).resolve().parents[1] / 'sources'
INVENTORY_SOURCE = 'https://www.census.gov/foreign-trade/schedules/c/countrycodes.html'
# Reviewed selected countries only. Numeric syntax never approves a leaf inventory.
REVIEWED_PARTNERS = {'1220': 'Canada', '2010': 'Mexico', '5330': 'India', '5700': 'China'}
BLOCKERS = [
    'Complete per-flow leaf inventory not approved',
    'Full world reconciliation not verified',
    'Current API observation vintage and revision date not verified',
    'Raw statistical responses not archived or independently revalidated',
    'Classification vintage and comparability not verified',
]


def validate_check(check):
    keys(check, ['schemaVersion', 'basis', 'period', 'product', 'partners', 'inventorySourceURL', 'reviewedOn'])
    require(type(check['schemaVersion']) is int and check['schemaVersion'] == 1 and check['basis'] == BASIS)
    validate_period(check['period'])
    require(type(check['product']) is str and re.fullmatch('[0-9]{2}', check['product']))
    require(check['inventorySourceURL'] == INVENTORY_SOURCE)
    require(type(check['reviewedOn']) is str)
    timestamp(check['reviewedOn'] + 'T00:00:00Z')
    require(type(check['partners']) is list and len(check['partners']) == len(REVIEWED_PARTNERS), 'Unsupported selected-country inventory')
    partners = {}
    for partner in check['partners']:
        keys(partner, ['code', 'name'])
        require(type(partner['code']) is str and partner['code'] in REVIEWED_PARTNERS and partner['code'] not in partners)
        require(partner['name'] == REVIEWED_PARTNERS[partner['code']], 'Selected country name mismatch')
        partners[partner['code']] = partner['name']
    return check


def expected_plan(check, partners):
    return validate_plan({'schemaVersion': 1, 'basis': check['basis'], 'partitions': [
        {'flow': flow, 'period': check['period'], 'product': check['product'], 'partner': partner}
        for flow in ('imports', 'exports') for partner in partners
    ]})


def observation(entry, root, secrets):
    candidate = referenced_candidate(entry, lambda identity: object_bytes(Path(root), identity), secrets)
    row = candidate['rows'][0]
    return {
        'partnerCode': row['partnerCode'], 'partnerName': row['partnerName'],
        'valueUSD': row['value'], 'status': row['status'], 'candidateId': candidate['candidateId'],
        'objectHash': entry['objectHash'], 'sourceHash': candidate['sourceHash'], 'ingestedAt': candidate['ingestedAt'],
    }


def build_report(check, market_plan, market_root, world_plan, world_root, statement, document, *, secrets=()):
    """Re-verify every input. Announcement evidence does not establish API vintage."""
    check = validate_check(decode(canonical(check), secrets))
    market_plan, world_plan = validate_plan(market_plan), validate_plan(world_plan)
    require(market_plan == expected_plan(check, REVIEWED_PARTNERS), 'Market plan differs from reviewed scope')
    require(world_plan == expected_plan(check, ['-']), 'World plan differs from reviewed scope')
    publication = verify_publication(statement, document, secrets=secrets)
    require(publication['period'] == check['period'] and publication['basis'] == check['basis'], 'Publication scope mismatch')
    markets = verify_bundle(market_plan, market_root)
    world = verify_bundle(world_plan, world_root)
    checks = []
    for flow in ('imports', 'exports'):
        selected = [observation(entry, market_root, secrets) for entry in markets['partitions'] if entry['slot']['flow'] == flow]
        control_entries = [entry for entry in world['partitions'] if entry['slot']['flow'] == flow]
        require(len(selected) == len(REVIEWED_PARTNERS) and len(control_entries) == 1, 'Incomplete control inputs')
        control = observation(control_entries[0], world_root, secrets)
        require(control['partnerCode'] == '-', 'World control code mismatch')
        for row in selected:
            require(row['partnerName'].casefold() == REVIEWED_PARTNERS[row['partnerCode']].casefold(), 'Source country name mismatch')
        total = sum(int(row['valueUSD']) for row in selected)
        world_total = int(control['valueUSD'])
        require(total <= world_total, 'Selected-market amount exceeds world control; inspect basis, source vintage and revisions')
        checks.append({
            'flow': flow, 'selectedTotalUSD': str(total), 'worldControlUSD': str(world_total),
            'outsideSelectionUSD': str(world_total - total), 'subsetCheck': 'passed',
            'fullWorldReconciliation': 'not-verified', 'observations': selected, 'control': control,
        })
    report = {
        'schemaVersion': 1, 'state': 'private-validation', 'publicationReady': False,
        'coverage': 'selected-markets-only',
        'scope': {'period': check['period'], 'product': check['product'], 'basis': check['basis'],
                  'selectedInventoryId': digest(check), 'inventorySourceURL': check['inventorySourceURL'], 'reviewedOn': check['reviewedOn']},
        'inputs': {'marketPlanId': digest(market_plan), 'marketBundleId': markets['bundleId'],
                   'worldPlanId': digest(world_plan), 'worldBundleId': world['bundleId']},
        'publication': publication, 'checks': checks, 'publicationBlockers': BLOCKERS,
    }
    report['reportId'] = digest(report)
    return decode(canonical(report), secrets)


def save_report(report, root, *, secrets=()):
    """Persist only a completed private report; never writes a public active pointer."""
    report = decode(canonical(report), secrets)
    keys(report, ['schemaVersion', 'state', 'publicationReady', 'coverage', 'scope', 'inputs', 'publication', 'checks', 'publicationBlockers', 'reportId'])
    require(report['state'] == 'private-validation' and report['publicationReady'] is False and report['publicationBlockers'] == BLOCKERS)
    require(digest({k: v for k, v in report.items() if k != 'reportId'}) == report['reportId'], 'Control report identity mismatch')
    root = Path(root)
    with writer(root):
        path = root / (report['reportId'] + '.json')
        if path.exists():
            require(read(path, secrets) == report, 'Control report identity collision')
        else:
            atomic_write(path, canonical(report))
        atomic_write(root / 'complete.json', canonical({'reportId': report['reportId']}))
    return report


def run_control_report(market_run, world_run, root, key, token, repository):
    validate_key(key)
    root = Path(root)
    require(not root.exists() or not any(root.iterdir()), 'Control acquisition requires an empty destination')
    secrets = (key, token)
    check = read(SOURCE_ROOT / 'control-checks/coffee-2026-07.json', secrets)
    market_plan = validate_plan(read(SOURCE_ROOT / 'batches/coffee-markets-2026-07.json', secrets))
    world_plan = validate_plan(read(SOURCE_ROOT / 'batches/coffee-world-2026-07.json', secrets))
    statement = read(SOURCE_ROOT / 'publications/ft900-2026-07.json', secrets)
    try:
        for run_id, plan, destination in [(market_run, market_plan, root / 'markets'), (world_run, world_plan, root / 'world')]:
            files = fetch_snapshot(repository, run_id, token)
            restore_snapshot(plan, files, destination, key, evidence_secrets=(token,))
    except SnapshotError:
        raise SourceError('Trusted control input download failed') from None
    proof = archive_publication(statement, root / 'publication', secrets=secrets)
    document_path = root / 'publication/documents' / (proof['documentHash'] + '.pdf')
    # Re-read and independently verify the archived bytes, rather than trusting proof.json.
    report = build_report(check, market_plan, root / 'markets', world_plan, root / 'world', statement, document_path.read_bytes(), secrets=secrets)
    return save_report(report, root / 'reports', secrets=secrets)


def main():
    parser = argparse.ArgumentParser(description='Verify private selected markets against world controls; does not publish')
    parser.add_argument('--market-run', required=True, type=int)
    parser.add_argument('--world-run', required=True, type=int)
    parser.add_argument('--output', type=Path, default=Path('pipeline/output/controls'))
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', 'Vasuki8/us-trade-explorer'))
    args = parser.parse_args()
    try:
        report = run_control_report(args.market_run, args.world_run, args.output, os.environ.get('CENSUS_API_KEY', ''), os.environ.get('GH_TOKEN', ''), args.repository)
        print(f"Private control report validated: {len(report['checks'])} subset checks. Full reconciliation and publication remain blocked.")
    except (SourceError, OSError, KeyError, TypeError):
        parser.exit(1, 'Private control report failed. No public release was activated.\n')


if __name__ == '__main__':
    main()
