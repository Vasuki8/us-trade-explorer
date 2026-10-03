"""Offline HTS row inspection; no statistical, quantity or publication approval.

JSON editions omit chapter/section/general notes. A matching projection is a
bounded metadata observation, never proof of historical comparability.
"""
import hashlib
import json
import re

from pipeline.candidates import hash_text, keys, require
from pipeline.census import SourceError

MAX_BYTES = 30 * 1024 * 1024
MAX_ROWS = 100_000
ROW_FIELDS = ('htsno', 'indent', 'description', 'superior', 'units', 'footnotes',
              'general', 'special', 'other', 'quotaQuantity', 'additionalDuties', 'addiitionalDuties')
SEMANTIC_FIELDS = ('description', 'indent', 'superior', 'units', 'footnotes', 'ancestors')


def _decode(raw, expected_sha256):
    hash_text(expected_sha256)
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'Missing or oversized HTS source')
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'HTS source checksum mismatch')

    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'Duplicate HTS JSON field')
            result[key] = value
        return result

    def constant(_):
        raise SourceError('Invalid HTS JSON number')

    try:
        result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        raise SourceError('Invalid HTS JSON encoding') from None
    require(type(result) is list and 0 < len(result) <= MAX_ROWS, 'Invalid HTS source row count')
    return result


def _text(value, maximum, message):
    require(type(value) is str and 0 < len(value) <= maximum and value.strip()
            and all(ord(c) >= 32 and ord(c) != 127 for c in value), message)


def _row(value, source_row):
    keys(value, ROW_FIELDS)
    code = value['htsno']
    require(type(code) is str and (code == '' or re.fullmatch(r'[0-9]{4}(?:\.[0-9]{2}){0,3}', code)),
            'Unsupported HTS code format')
    indent = value['indent']
    require(type(indent) is str and re.fullmatch(r'(?:[0-9]|1[0-2])', indent), 'Invalid HTS indentation')
    _text(value['description'], 4000, 'Invalid HTS description')
    require(value['superior'] in (None, 'true') and type(value['superior']) in (str, type(None)),
            'Invalid HTS hierarchy marker')
    units = value['units']
    require(type(units) is list and len(units) <= 2, 'Invalid HTS units')
    for unit in units:
        _text(unit, 32, 'Invalid HTS unit')
    require(len(set(units)) == len(units), 'Duplicate HTS units')
    require(code != '' or (value['superior'] == 'true' and units == []), 'Invalid unnamed HTS parent')
    notes = value['footnotes']
    require(notes is None or type(notes) is list and len(notes) <= 32, 'Invalid HTS footnotes')
    if notes is not None:
        for note in notes:
            keys(note, ('columns', 'value', 'type'))
            columns = note['columns']
            require(type(columns) is list and 1 <= len(columns) <= 12
                    and all(type(c) is str and c in ROW_FIELDS for c in columns)
                    and len(set(columns)) == len(columns), 'Invalid HTS footnote columns')
            _text(note['value'], 4000, 'Invalid HTS footnote text')
            require(note['type'] in ('endnote', 'footnote'), 'Invalid HTS footnote type')
    # Tariff rates/duty fields remain in the source artifact. They are outside
    # this statistical-metadata projection and cannot feed a customs calculator.
    return {'sourceRow': source_row, 'code': code.replace('.', '') or None,
            'indent': int(indent), 'description': value['description'],
            'superior': value['superior'], 'units': units, 'footnotes': notes}


def extract_hts_chapter(raw, expected_sha256, chapter='09'):
    """Inspect one contiguous chapter of a caller-pinned official JSON edition.

    Pin review/source attribution is the caller's responsibility. No claim about
    completeness of notes, effective intervals or actual observations is made.
    """
    require(type(chapter) is str and re.fullmatch(r'(?:0[1-9]|[1-8][0-9]|9[0-7])', chapter),
            'Invalid HTS chapter scope')
    data = _decode(raw, expected_sha256)
    rows, stack, coded = [], [], []
    seen, started, ended = set(), False, False
    for position, value in enumerate(data):
        require(type(value) is dict and type(value.get('htsno')) is str, 'Invalid HTS source row')
        source_code = value['htsno']
        selected = source_code.startswith(chapter)
        if selected:
            require(not ended, 'Noncontiguous HTS chapter')
            started = True
        elif source_code:
            if started:
                ended = True
            continue
        elif not started or ended:
            continue
        current = _row(value, position)
        code, indent = current['code'], current['indent']
        while stack and stack[-1]['indent'] >= indent:
            stack.pop()
        if indent == 0:
            # A heading with no subdivisions can be printed as a 10-digit root
            # (e.g. 0903.00.00.00); do not fabricate a missing four-digit row.
            require(code is not None, 'Invalid HTS chapter root')
        else:
            require(stack and indent == stack[-1]['indent'] + 1, 'Incomplete HTS hierarchy')
        if code is not None:
            require(code not in seen, 'Duplicate HTS code')
            active_codes = {parent['code'] for parent in stack if parent['code'] is not None}
            require(all(code[:length] not in seen or code[:length] in active_codes
                        for length in (4, 6, 8) if length < len(code)), 'Detached HTS parent code')
            seen.add(code)
            require(all(code.startswith(parent['code']) and len(code) > len(parent['code'])
                        for parent in stack if parent['code'] is not None), 'Incompatible HTS parent code')
            coded.append({**current, 'ancestors': [
                {field: parent[field] for field in ('code', 'indent', 'description', 'superior')}
                for parent in stack]})
        rows.append(current)
        stack.append(current)
    require(rows and coded and any(len(r['code']) == 10 for r in coded), 'Missing HTS chapter detail')
    return {'schemaVersion': 1, 'state': 'classification-review-only', 'flow': 'imports',
            'classification': 'HTSUS', 'chapter': chapter, 'sourceHash': expected_sha256,
            'counts': {'rows': len(rows), 'coded': len(coded), 'unnumbered': len(rows) - len(coded),
                       'statistical': sum(len(r['code']) == 10 for r in coded)},
            'rows': rows, 'codedRows': coded, 'comparabilityApproved': False, 'publicationReady': False}


def compare_hts_chapters(before, after, before_sha256, after_sha256, chapter='09'):
    """Compare independently verified raw editions, including ancestor meaning.

    Absolute source offsets can change when other chapters change. Preserve them
    in extraction but omit them from semantic comparison. Footnotes are distinct
    from row structure, and matching either never approves comparability.
    """
    a = extract_hts_chapter(before, before_sha256, chapter)
    b = extract_hts_chapter(after, after_sha256, chapter)
    old = {row['code']: row for row in a['codedRows']}
    new = {row['code']: row for row in b['codedRows']}
    common = old.keys() & new.keys()
    changed = []
    for code in sorted(common):
        fields = [field for field in SEMANTIC_FIELDS if old[code][field] != new[code][field]]
        if fields:
            changed.append({'code': code, 'fields': fields,
                            'before': {field: old[code][field] for field in fields},
                            'after': {field: new[code][field] for field in fields}})

    def projection(snapshot, with_notes):
        fields = ['code', 'indent', 'description', 'superior', 'units']
        if with_notes:
            fields.append('footnotes')
        return [{field: row[field] for field in fields} for row in snapshot['rows']]

    return {'schemaVersion': 1, 'state': 'classification-comparison-only', 'flow': 'imports',
            'classification': 'HTSUS', 'chapter': chapter,
            'beforeHash': before_sha256, 'afterHash': after_sha256,
            'added': sorted(new.keys() - old.keys()), 'removed': sorted(old.keys() - new.keys()),
            'changed': changed,
            'orderEqual': [r['code'] for r in a['codedRows']] == [r['code'] for r in b['codedRows']],
            'structureEqual': projection(a, False) == projection(b, False),
            'metadataEqual': projection(a, True) == projection(b, True),
            'comparabilityApproved': False, 'publicationReady': False}
