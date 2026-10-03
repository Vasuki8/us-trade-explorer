"""Illustrative HTS-shaped fixtures; not official classification or trade data."""
import copy
import hashlib
import json
import unittest

from pipeline.classification import compare_hts_chapters, extract_hts_chapter, MAX_BYTES
from pipeline.census import SourceError


def row(code, indent, description, units=None, footnotes=None):
    return {'htsno': code, 'indent': str(indent), 'description': description,
            'superior': 'true' if not code else None, 'units': units or [],
            'footnotes': footnotes, 'general': '', 'special': '', 'other': '',
            'quotaQuantity': None, 'additionalDuties': None, 'addiitionalDuties': None}


def fixture():
    return [row('0801', 0, 'Previous chapter'), row('0901', 0, 'Coffee:'),
            row('', 1, 'Coffee, not roasted:'), row('0901.11.00', 2, 'Not decaffeinated'),
            row('', 3, 'Arabica:'), row('0901.11.00.15', 4, 'Certified organic', ['kg']),
            row('0901.11.00.25', 4, 'Other', ['kg']), row('1001', 0, 'Next chapter')]


def encoded(data):
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    return raw, hashlib.sha256(raw).hexdigest()


def extract(data):
    return extract_hts_chapter(*encoded(data))


def compare(before, after):
    a, ah = encoded(before)
    b, bh = encoded(after)
    return compare_hts_chapters(a, b, ah, bh)


class ClassificationTests(unittest.TestCase):
    def test_preserves_unnumbered_context_source_order_and_units(self):
        result = extract(fixture())
        self.assertEqual(result['counts'], {'rows': 6, 'coded': 4, 'unnumbered': 2, 'statistical': 2})
        self.assertEqual([r['code'] for r in result['rows']], ['0901', None, '09011100', None, '0901110015', '0901110025'])
        detail = next(r for r in result['codedRows'] if r['code'] == '0901110015')
        self.assertEqual([r['description'] for r in detail['ancestors']],
                         ['Coffee:', 'Coffee, not roasted:', 'Not decaffeinated', 'Arabica:'])
        self.assertEqual(detail['units'], ['kg'])
        self.assertEqual(detail['sourceRow'], 5)
        self.assertEqual(result['flow'], 'imports')
        self.assertEqual(result['classification'], 'HTSUS')
        self.assertEqual(result['state'], 'classification-review-only')
        self.assertFalse(result['comparabilityApproved'])
        self.assertFalse(result['publicationReady'])

    def test_unchanged_leaf_with_changed_blank_parent_is_reported(self):
        before, after = fixture(), fixture()
        after[4]['description'] = 'Robusta:'
        result = compare(before, after)
        self.assertEqual([r['code'] for r in result['changed']], ['0901110015', '0901110025'])
        self.assertEqual(result['changed'][0]['fields'], ['ancestors'])
        self.assertFalse(result['structureEqual'])

    def test_accepts_six_digit_numbered_hierarchy_seen_in_official_edition(self):
        data = fixture()
        data[2] = row('0901.11', 1, 'Six-digit parent:')
        result = extract(data)
        self.assertEqual(result['codedRows'][1]['code'], '090111')
        self.assertEqual(result['codedRows'][-1]['ancestors'][1]['code'], '090111')

    def test_accepts_standalone_ten_digit_root_seen_in_official_edition(self):
        data = fixture()
        data.insert(-1, row('0903.00.00.00', 0, 'Standalone product', ['kg']))
        result = extract(data)
        self.assertEqual(result['codedRows'][-1]['code'], '0903000000')
        self.assertEqual(result['codedRows'][-1]['ancestors'], [])

    def test_detects_addition_deletion_description_unit_and_footnote_changes(self):
        before, after = fixture(), fixture()
        after[5]['description'] = 'Updated description'
        after[5]['units'] = ['kg', 'No.']
        after[5]['footnotes'] = [{'columns': ['general'], 'value': 'See example note.', 'type': 'endnote'}]
        after[6]['htsno'] = '0901.11.00.35'
        result = compare(before, after)
        self.assertEqual(result['added'], ['0901110035'])
        self.assertEqual(result['removed'], ['0901110025'])
        self.assertEqual(result['changed'][0]['fields'], ['description', 'units', 'footnotes'])
        self.assertFalse(result['comparabilityApproved'])
        self.assertFalse(result['publicationReady'])

    def test_footnote_only_change_does_not_claim_full_metadata_equality(self):
        before, after = fixture(), fixture()
        before[3]['footnotes'] = [{'columns': ['general'], 'value': 'See example.', 'type': 'endnote'}]
        after[3]['footnotes'] = []
        result = compare(before, after)
        self.assertTrue(result['structureEqual'])
        self.assertFalse(result['metadataEqual'])
        self.assertEqual(result['changed'][0]['code'], '09011100')
        self.assertEqual(result['changed'][0]['fields'], ['footnotes'])

    def test_unnumbered_parent_footnote_has_actionable_before_after_report(self):
        before, after = fixture(), fixture()
        note = [{'columns': ['description'], 'value': 'Review this parent note.', 'type': 'footnote'}]
        after[4]['footnotes'] = note
        result = compare(before, after)
        self.assertTrue(result['structureEqual'])
        self.assertFalse(result['metadataEqual'])
        self.assertEqual(result['changed'], [])
        change = result['unnumberedChanges'][0]
        self.assertEqual(change['index'], 1)
        self.assertEqual(change['fields'], ['footnotes'])
        self.assertEqual(change['before'], {'footnotes': None})
        self.assertEqual(change['after'], {'footnotes': note})

    def test_rejects_json_numeric_overflow_and_unsupported_numeric_fields(self):
        data = fixture()
        data[5]['general'] = 1.5
        raw, _ = encoded(data)
        for number in (b'1e999', b'-1e999', b'1.5', b'7'):
            invalid = raw.replace(b'"general":1.5', b'"general":' + number)
            with self.subTest(number=number):
                with self.assertRaises(SourceError):
                    extract_hts_chapter(invalid, hashlib.sha256(invalid).hexdigest())

    def test_detects_order_changes_but_ignores_absolute_offsets_in_other_chapters(self):
        before, after = fixture(), fixture()
        after.insert(0, row('0701', 0, 'Unrelated preceding chapter'))
        self.assertTrue(compare(before, after)['metadataEqual'])
        after = fixture()
        after[5], after[6] = after[6], after[5]
        result = compare(before, after)
        self.assertFalse(result['orderEqual'])
        self.assertFalse(result['metadataEqual'])

    def test_keeps_exact_untrusted_text_and_does_not_mutate_inputs(self):
        data = fixture()
        data[5]['description'] = '<img src=x onerror=alert(1)> =SUM(A1)'
        saved = copy.deepcopy(data)
        self.assertEqual(extract(data)['codedRows'][-2]['description'], data[5]['description'])
        compare(data, data)
        self.assertEqual(saved, data)

    def test_rejects_hash_mismatch_malformed_hash_and_oversize(self):
        raw, identity = encoded(fixture())
        for data, expected in [(raw, '0' * 64), (raw, identity.upper()), (raw, True),
                               (b' ' * (MAX_BYTES + 1), identity), ('not bytes', identity)]:
            with self.subTest(expected=type(expected).__name__):
                with self.assertRaises(SourceError):
                    extract_hts_chapter(data, expected)

    def test_rejects_duplicate_json_fields_nonfinite_and_invalid_encoding(self):
        for raw in [b'[{"htsno":"0901","htsno":"0902"}]', b'[NaN]', b'[Infinity]', b'\xff']:
            with self.subTest(raw=raw):
                with self.assertRaises(SourceError):
                    extract_hts_chapter(raw, hashlib.sha256(raw).hexdigest())

    def test_rejects_duplicate_codes_bad_types_schema_and_hierarchy(self):
        changes = [(5, 'htsno', '0901.11.00'), (5, 'indent', True), (5, 'indent', '13'),
                   (5, 'indent', '0'), (5, 'units', 'kg'), (5, 'units', ['kg', 'kg']),
                   (5, 'description', ''), (5, 'description', 'bad\nlabel'),
                   (5, 'description', 'a' * 4001), (5, 'unknown', 'new field'),
                   (5, 'htsno', '0901.111'), (5, 'footnotes', ['bad']),
                   (5, 'footnotes', [{'columns': ['general'], 'value': 'x', 'type': 'bad'}]),
                   (5, 'superior', True), (5, 'general', True), (5, 'quotaQuantity', []),
                   (5, 'other', 'bad\nrate'), (3, 'htsno', '0902.11.00')]
        for index, field, value in changes:
            data = fixture()
            data[index][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(SourceError):
                    extract(data)

    def test_rejects_missing_noncontiguous_or_incomplete_chapter_and_invalid_scope(self):
        for data in [[], fixture()[:1], fixture()[2:], fixture() + [row('0902', 0, 'Late fragment')]]:
            with self.subTest(rows=len(data)):
                with self.assertRaises(SourceError):
                    extract(data)
        raw, identity = encoded(fixture())
        for chapter in ['*', '9', '00', '99', True, '09?key=secret']:
            with self.subTest(chapter=chapter):
                with self.assertRaises(SourceError):
                    extract_hts_chapter(raw, identity, chapter)

    def test_safe_error_does_not_echo_source_text(self):
        data = fixture()
        data[5]['units'] = ['reflected-sensitive-placeholder\n']
        with self.assertRaises(SourceError) as context:
            extract(data)
        self.assertNotIn('reflected-sensitive', str(context.exception))


if __name__ == '__main__':
    unittest.main()
