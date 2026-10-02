import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from pipeline.candidates import decode
from pipeline.census import MAX_BYTES, MAX_ROWS, SourceError, aggregate_dimensions, fetch_bytes, fetch_candidate

KEY = 'fixture-census-key'


def response(flow='imports', codes=('-', '0003', '1220'), summary='DET'):
    prefix, variable = ('I', 'GEN_VAL_MO') if flow == 'imports' else ('E', 'ALL_VAL_MO')
    table = []
    for code in codes:
        row = {prefix + '_COMMODITY': '09', prefix + '_COMMODITY_SDESC': 'Coffee',
               'CTY_CODE': code, 'CTY_NAME': 'Source label', variable: '0' if code == '0003' else '123',
               'COMM_LVL': 'HS2', 'YEAR': '2026', 'MONTH': '07', **aggregate_dimensions(flow)}
        if summary is not None:
            row['SUMMARY_LVL'] = summary
        if not table:
            table.append(list(row))
        table.append(list(row.values()))
    return json.dumps(table).encode()


class PartnerSourceTests(unittest.TestCase):
    def test_explicit_detail_wildcard_both_flows_preserves_observed_zero_and_capture(self):
        for flow in ('imports', 'exports'):
            with self.subTest(flow=flow):
                raw = response(flow)
                captured = []
                with patch('pipeline.census.fetch_bytes', return_value=raw) as fetch:
                    candidate = fetch_candidate(flow, '2026-07', KEY, partner='*', summary='DET',
                                                response_limit=512 * 1024, row_limit=500, capture=captured.append)
                args, kwargs = fetch.call_args
                query = parse_qs(urlsplit(args[0]).query)
                self.assertEqual(kwargs, {'maximum': 512 * 1024})
                self.assertEqual(query['SUMMARY_LVL'], ['DET'])
                self.assertEqual(query['CTY_CODE'], ['*'])
                self.assertTrue(set(query['get'][0].split(',')).isdisjoint(set(query) - {'get', 'key'}))
                self.assertEqual(captured, [raw])
                self.assertEqual(candidate['sourceHash'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(candidate['rows'][1]['status'], 'reported_zero')

    def test_default_country_query_and_identity_remain_unchanged(self):
        raw = response(codes=('1220',), summary=None)
        with patch('pipeline.census.fetch_bytes', return_value=raw) as fetch:
            first = fetch_candidate('imports', '2026-07', KEY)
            second = fetch_candidate('imports', '2026-07', KEY, summary=None, response_limit=None, row_limit=None)
        self.assertEqual(first['candidateId'], second['candidateId'])
        for args, kwargs in fetch.call_args_list:
            self.assertEqual(kwargs, {})
            self.assertNotIn('SUMMARY_LVL', parse_qs(urlsplit(args[0]).query))

    def test_invalid_constraints_fail_before_source_calls(self):
        invalid = [{'summary': value} for value in ('CGP', 'det', True, '', 1)]
        invalid += [{'response_limit': value} for value in (0, True, -1, MAX_BYTES + 1, '512')]
        invalid += [{'row_limit': value} for value in (0, True, -1, MAX_ROWS + 1, '500')]
        with patch('pipeline.census.fetch_bytes') as fetch:
            for constraints in invalid:
                with self.subTest(constraints=constraints), self.assertRaises(SourceError):
                    fetch_candidate('imports', '2026-07', KEY, partner='*', **constraints)
        fetch.assert_not_called()

    def test_non_detail_rows_fail_before_capture(self):
        captured = []
        with patch('pipeline.census.fetch_bytes', return_value=response(summary='CGP')):
            with self.assertRaises(SourceError):
                fetch_candidate('imports', '2026-07', KEY, partner='*', summary='DET', capture=captured.append)
        self.assertEqual(captured, [])

    def test_row_and_mocked_response_bounds_fail_before_capture(self):
        for constraints in ({'row_limit': 2}, {'response_limit': 20}):
            captured = []
            with self.subTest(constraints=constraints), patch('pipeline.census.fetch_bytes', return_value=response()):
                with self.assertRaises(SourceError):
                    fetch_candidate('imports', '2026-07', KEY, partner='*', summary='DET',
                                    capture=captured.append, **constraints)
            self.assertEqual(captured, [])

    def test_transport_enforces_smaller_declared_and_streamed_body_bounds(self):
        for declared in ('5', None):
            sock = Mock()
            reply = SimpleNamespace(status=200, getheader=lambda name, default=None:
                                    {'Content-Type': 'application/json', 'Content-Length': declared}.get(name, default),
                                    read1=Mock(side_effect=[b'abcde', b'']), close=Mock())
            connection = Mock(sock=sock)
            connection.getresponse.return_value = reply
            with self.subTest(declared=declared), patch('pipeline.census.http.client.HTTPSConnection', return_value=connection):
                with self.assertRaises(SourceError):
                    fetch_bytes('https://api.census.gov/data/timeseries/intltrade/imports/hs?x=1', maximum=4)
            if declared is not None:
                reply.read1.assert_not_called()
            connection.close.assert_called_once()

    def test_invalid_transport_bound_fails_before_connection(self):
        with patch('pipeline.census.http.client.HTTPSConnection') as connection:
            for maximum in (0, True, MAX_BYTES + 1, '512'):
                with self.subTest(maximum=maximum), self.assertRaises(SourceError):
                    fetch_bytes('https://api.census.gov/data/timeseries/intltrade/imports/hs', maximum=maximum)
        connection.assert_not_called()

    def test_larger_decoding_retains_default_cap_and_strict_secret_json_checks(self):
        raw = json.dumps({'text': 'x' * 70000}).encode()
        with self.assertRaises(SourceError):
            decode(raw)
        self.assertEqual(len(decode(raw, maximum=512 * 1024)['text']), 70000)
        escaped = ''.join('\\u%04x' % ord(char) for char in KEY)
        for unsafe in (('{"secret":"' + escaped + '"}').encode(), b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.subTest(unsafe_type=len(unsafe)), self.assertRaises(SourceError):
                decode(unsafe, (KEY,), maximum=512 * 1024)
        for maximum in (0, True, 2 * 1024 * 1024 + 1, '512'):
            with self.subTest(maximum=maximum), self.assertRaises(SourceError):
                decode(b'{}', maximum=maximum)


if __name__ == '__main__':
    unittest.main()
