"""Network-boundary tests use fabricated responses, never an API credential."""
import contextlib
import http.client
import io
import json
import socket
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from pipeline.census import SourceError, fetch_candidate, parse_rows, main

KEY = 'canary-private-secret'
IMPORT_HEADER = ['I_COMMODITY', 'I_COMMODITY_SDESC', 'CTY_CODE', 'CTY_NAME',
                 'GEN_VAL_MO', 'YEAR', 'MONTH', 'COMM_LVL', 'CTY_SUBCODE', 'DISTRICT', 'RP']
IMPORT_ROW = ['09', 'Coffee, tea', '1220', 'Canada', '123456', '2026', '07', 'HS2', '-', '-', '-']


class AcquisitionTests(unittest.TestCase):
    def test_schema_diagnostics_identify_known_missing_fields_without_echoing_source_names(self):
        for header, row, expected in [
            (IMPORT_HEADER[:-1], IMPORT_ROW[:-1], 'missing known columns=RP'),
            (IMPORT_HEADER + ['CTY_CODE'], IMPORT_ROW + ['1220'], 'duplicate columns=1'),
            (IMPORT_HEADER + [KEY], IMPORT_ROW + [KEY], 'unknown columns=1'),
        ]:
            with self.subTest(expected=expected), self.assertRaises(SourceError) as raised:
                parse_rows([header, row], 'imports', '2026-07')
            self.assertIn(expected, str(raised.exception))
            self.assertNotIn(KEY, str(raised.exception))

    def response(self, status=200):
        response = MagicMock()
        response.status = status
        response.getheader.side_effect = lambda key, default=None: {'Content-Type': 'application/json'}.get(key, default)
        connection = MagicMock()
        connection.getresponse.return_value = response
        return connection, response

    def test_network_failures_report_safe_categories_after_bounded_attempts(self):
        cases = [
            ('connect', socket.timeout(KEY), 'connect_timeout'),
            ('connect', socket.gaierror(KEY), 'dns_error'),
            ('connect', ssl.SSLError(KEY), 'tls_error'),
            ('headers', socket.timeout(KEY), 'headers_timeout'),
            ('body', socket.timeout(KEY), 'body_timeout'),
            ('headers', http.client.RemoteDisconnected(KEY), 'protocol_error'),
        ]
        for phase, failure, expected in cases:
            with self.subTest(phase=phase, category=expected):
                connection, response = self.response()
                target = {'connect': connection.connect, 'headers': connection.getresponse, 'body': response.read1}[phase]
                target.side_effect = failure
                logs = io.StringIO()
                with patch('pipeline.census.http.client.HTTPSConnection', return_value=connection), patch('pipeline.census.time.sleep'), contextlib.redirect_stderr(logs):
                    with self.assertRaises(SourceError) as raised:
                        fetch_candidate('imports', '2026-07', KEY)
                self.assertEqual(getattr(raised.exception, 'category', None), expected)
                events = [json.loads(line) for line in logs.getvalue().splitlines()]
                self.assertEqual([e['attempt'] for e in events], [1, 2, 3])
                self.assertTrue(all(e['category'] == expected for e in events))
                self.assertNotIn(KEY, logs.getvalue() + str(raised.exception))
                self.assertNotIn('https://', logs.getvalue())

    def test_http_status_and_no_results_have_distinct_safe_diagnostics(self):
        for status, category, attempts in [(429, 'rate_limited', 3), (503, 'upstream_unavailable', 3),
                                           (403, 'http_rejected', 1), (204, 'no_results', 1)]:
            with self.subTest(status=status):
                connection, response = self.response(status)
                logs = io.StringIO()
                with patch('pipeline.census.http.client.HTTPSConnection', return_value=connection), patch('pipeline.census.time.sleep'), contextlib.redirect_stderr(logs):
                    with self.assertRaises(SourceError) as raised:
                        fetch_candidate('imports', '2026-07', KEY)
                self.assertEqual(getattr(raised.exception, 'category', None), category)
                self.assertEqual(getattr(raised.exception, 'http_status', None), status)
                self.assertEqual(connection.request.call_count, attempts)
                response.read1.assert_not_called()

    def test_small_probe_uses_documented_period_and_aggregate_filters(self):
        raw = json.dumps([IMPORT_HEADER, IMPORT_ROW]).encode()
        with patch('pipeline.census.fetch_bytes', return_value=raw) as source:
            candidate = fetch_candidate('imports', '2026-07', KEY)
        query = parse_qs(urlsplit(source.call_args.args[0]).query)
        self.assertNotIn('time', query)
        for field, value in {'YEAR': '2026', 'MONTH': '07', 'I_COMMODITY': '09', 'CTY_CODE': '1220',
                             'DISTRICT': '-', 'CTY_SUBCODE': '-', 'RP': '-'}.items():
            self.assertEqual(query[field], [value])
        self.assertEqual(candidate['schemaVersion'], 2)
        self.assertEqual(candidate['scope'], {'commodityLevel': 'HS2', 'product': '09', 'partner': '1220', 'coverage': 'unverified'})
        self.assertNotIn('key', candidate['sourceQuery'])
        self.assertNotIn(KEY, json.dumps(candidate))
        self.assertEqual(candidate['rows'][0]['value'], '123456')
        self.assertIsNone(candidate['officialReleaseDate'])
        self.assertEqual(candidate['state'], 'candidate')

    def test_exports_require_total_domestic_foreign_and_district_dimensions(self):
        header = ['E_COMMODITY', 'E_COMMODITY_SDESC', 'CTY_CODE', 'CTY_NAME', 'ALL_VAL_MO', 'YEAR', 'MONTH', 'COMM_LVL', 'DISTRICT', 'DF']
        row = ['09', 'Coffee, tea', '1220', 'Canada', '12', '2026', '07', 'HS2', '-', '-']
        self.assertEqual(parse_rows([header, row], 'exports', '2026-07')[0]['value'], '12')
        for invalid in ['1', '2', '00']:
            with self.subTest(df=invalid), self.assertRaises(SourceError):
                parse_rows([header, row[:-1] + [invalid]], 'exports', '2026-07')

    def test_missing_or_conflicting_period_and_aggregation_dimensions_fail_closed(self):
        for index, replacement in [(5, '2025'), (6, '08'), (8, '0'), (9, '00'), (10, '00')]:
            row = IMPORT_ROW.copy()
            row[index] = replacement
            with self.subTest(index=index), self.assertRaises(SourceError):
                parse_rows([IMPORT_HEADER, row], 'imports', '2026-07')
        for missing in ['CTY_SUBCODE', 'DISTRICT', 'RP', 'MONTH']:
            index = IMPORT_HEADER.index(missing)
            with self.subTest(missing=missing), self.assertRaises(SourceError):
                parse_rows([IMPORT_HEADER[:index] + IMPORT_HEADER[index+1:], IMPORT_ROW[:index] + IMPORT_ROW[index+1:]], 'imports', '2026-07')
        with self.assertRaises(SourceError):
            parse_rows([IMPORT_HEADER + ['time'], IMPORT_ROW + ['2026-06']], 'imports', '2026-07')

    def test_scope_inputs_and_returned_rows_cannot_silently_expand_a_probe(self):
        for product, partner in [('09&key=bad', '1220'), ('0901', '1220'), ('09', '1220,2010'), ('09', '-1')]:
            with self.subTest(product=product, partner=partner), patch('pipeline.census.fetch_bytes') as source:
                with self.assertRaises(SourceError):
                    fetch_candidate('imports', '2026-07', KEY, product=product, partner=partner)
                source.assert_not_called()
        for index, changed in [(0, '84'), (2, '2010'), (2, '-')]:
            row = IMPORT_ROW.copy()
            row[index] = changed
            with self.subTest(index=index), patch('pipeline.census.fetch_bytes', return_value=json.dumps([IMPORT_HEADER, row]).encode()):
                with self.assertRaises(SourceError):
                    fetch_candidate('imports', '2026-07', KEY)

    def test_candidate_identity_includes_requested_scope_but_not_retrieval_time(self):
        raw = json.dumps([IMPORT_HEADER, IMPORT_ROW]).encode()
        with patch('pipeline.census.fetch_bytes', return_value=raw), patch('pipeline.census.datetime') as clock:
            clock.now.return_value.strftime.side_effect = ['2026-10-02T01:00:00Z', '2026-10-02T02:00:00Z', '2026-10-02T03:00:00Z']
            one = fetch_candidate('imports', '2026-07', KEY)
            repeat = fetch_candidate('imports', '2026-07', KEY)
            broad = fetch_candidate('imports', '2026-07', KEY, product='*', partner='*')
        self.assertNotEqual(one['ingestedAt'], repeat['ingestedAt'])
        self.assertEqual(one['candidateId'], repeat['candidateId'])
        self.assertNotEqual(one['candidateId'], broad['candidateId'])
        self.assertEqual(one['sourceHash'], broad['sourceHash'])

    def test_cli_repeated_candidates_are_idempotent_and_failed_attempt_preserves_evidence(self):
        scratch = Path('.local/tests').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            raw = json.dumps([IMPORT_HEADER, IMPORT_ROW]).encode()
            args = ['census', '--flow', 'imports', '--period', '2026-07', '--output', directory]
            logs = io.StringIO()
            with patch('sys.argv', args), patch.dict('os.environ', {'CENSUS_API_KEY': KEY}), contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
                with patch('pipeline.census.fetch_bytes', return_value=raw):
                    main()
                    first = {p.name: p.read_bytes() for p in Path(directory).iterdir()}
                    main()
                    self.assertEqual(first, {p.name: p.read_bytes() for p in Path(directory).iterdir()})
                with patch('pipeline.census.fetch_bytes', side_effect=SourceError('No records', category='no_results', http_status=204)):
                    with self.assertRaises(SystemExit) as stopped:
                        main()
                    self.assertEqual(stopped.exception.code, 1)
                self.assertEqual(first, {p.name: p.read_bytes() for p in Path(directory).iterdir()})
                with patch('sys.argv', args + ['--product', '*', '--partner', '*']), patch('pipeline.census.fetch_bytes', return_value=raw):
                    main()
            self.assertEqual(len(list(Path(directory).glob('*.json'))), 2)
            self.assertNotIn(KEY, logs.getvalue())
            self.assertIn('no_results', logs.getvalue())


if __name__ == '__main__':
    unittest.main()
