"""Strict offline validation of private singleton acquisition evidence."""
import hashlib
import json
import re
from datetime import datetime

from pipeline.census import PATHS, SourceError, aggregate_dimensions

MAX_FILE_BYTES = 65536
BLOCKERS = ['Live dimensions and coverage not yet reconciled', 'Official publication evidence not yet attached']


def require(condition, message='Invalid private evidence'):
    if not condition:
        raise SourceError(message)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), 'Unexpected evidence fields')


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise SourceError('Invalid evidence encoding') from None


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def hash_text(value):
    require(type(value) is str and re.fullmatch('[a-f0-9]{64}', value), 'Invalid evidence identity')


def timestamp(value):
    require(type(value) is str and re.fullmatch(r'20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value), 'Invalid evidence timestamp')
    try:
        require(datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%dT%H:%M:%SZ') == value)
    except ValueError:
        raise SourceError('Invalid evidence timestamp') from None


def decode(raw, secret=None, *, maximum=MAX_FILE_BYTES):
    require(type(maximum) is int and 0 < maximum <= 2 * 1024 * 1024, 'Invalid private evidence bound')
    require(type(raw) is bytes and len(raw) <= maximum, 'Oversized private evidence')
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'Repeated evidence fields')
            result[key] = value
        return result
    def constant(_):
        raise SourceError('Invalid evidence number')
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
        # Check decoded values too: JSON escaping must not defeat reflection checks.
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
        secrets = (secret,) if type(secret) is str else secret or ()
        require(all(not item or item not in encoded for item in secrets), 'Evidence safety check failed')
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise SourceError('Invalid private JSON evidence') from None


def validate_candidate(value, slot):
    keys(value, ['schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash', 'candidateId', 'state', 'source', 'scope', 'officialReleaseDate', 'officialRevisionDate', 'ingestedAt', 'rows', 'publicationBlockers'])
    flow, period, product, partner = (slot[k] for k in ('flow', 'period', 'product', 'partner'))
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 2)
    require(value['flow'] == flow and value['period'] == period and value['state'] == 'candidate')
    require(value['source'] == 'https://api.census.gov' + PATHS[flow], 'Unexpected evidence source')
    require(value['scope'] == {'commodityLevel': 'HS2', 'product': product, 'partner': partner, 'coverage': 'unverified'}, 'Evidence scope mismatch')
    prefix, variable = ('I', 'GEN_VAL_MO') if flow == 'imports' else ('E', 'ALL_VAL_MO')
    expected_query = {'get': f'{prefix}_COMMODITY_SDESC,CTY_NAME,{variable}', 'YEAR': period[:4], 'MONTH': period[5:], 'COMM_LVL': 'HS2', f'{prefix}_COMMODITY': product, 'CTY_CODE': partner, **aggregate_dimensions(flow)}
    if partner == '-':
        expected_query['SUMMARY_LVL'] = 'DET'
    require(value['sourceQuery'] == expected_query, 'Evidence query mismatch')
    require(value['officialReleaseDate'] is None and value['officialRevisionDate'] is None)
    require(value['publicationBlockers'] == BLOCKERS, 'Missing publication blockers')
    timestamp(value['ingestedAt'])
    hash_text(value['sourceHash'])
    hash_text(value['candidateId'])
    identity = {key: value[key] for key in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')}
    require(digest(identity) == value['candidateId'], 'Candidate identity mismatch')
    require(type(value['rows']) is list and len(value['rows']) == 1, 'Singleton evidence requires one observation')
    row = value['rows'][0]
    keys(row, ['product', 'description', 'partnerCode', 'partnerName', 'flow', 'period', 'value', 'status'])
    require((row['product'], row['partnerCode'], row['flow'], row['period']) == (product, partner, flow, period), 'Observation scope mismatch')
    require(type(row['value']) is str and re.fullmatch(r'(0|[1-9]\d{0,23})', row['value']), 'Invalid observation value')
    require(row['status'] == ('reported_zero' if row['value'] == '0' else 'reported'), 'Observation status mismatch')
    for field in ('description', 'partnerName'):
        text = row[field]
        require(type(text) is str and 0 < len(text) <= 250 and all(ord(c) >= 32 and ord(c) != 127 for c in text), 'Invalid observation text')
    return value
