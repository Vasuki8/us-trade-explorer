"""World controls use fabricated source values and explicit Census dimensions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from pipeline.batch import run_batch, validate_plan, verify_bundle
from pipeline.candidates import digest, validate_candidate
from pipeline.census import SourceError, fetch_candidate

KEY = 'world-control-canary'
PLAN_PATH = Path(__file__).resolve().parents[2] / 'sources/batches/coffee-world-2026-07.json'


def reply(url, summary='DET', include_summary=True):
    query = parse_qs(urlsplit(url).query)
    prefix = 'I' if '/imports/' in url else 'E'
    variable = 'GEN_VAL_MO' if prefix == 'I' else 'ALL_VAL_MO'
    header = query['get'][0].split(',') + [name for name in query if name not in ('get', 'key')]
    values = {name: entries[0] for name, entries in query.items() if name not in ('get', 'key')}
    values.update({f'{prefix}_COMMODITY_SDESC': 'Coffee, tea', 'CTY_NAME': 'TOTAL FOR ALL COUNTRIES', variable: '123456', 'SUMMARY_LVL': summary})
    if not include_summary:
        header = [name for name in header if name != 'SUMMARY_LVL']
    return json.dumps([header, [values[name] for name in header]]).encode()


class WorldControlTests(unittest.TestCase):
    def test_world_queries_require_detail_summary_and_aggregate_dimensions(self):
        for flow in ('imports', 'exports'):
            with self.subTest(flow=flow), patch('pipeline.census.fetch_bytes', side_effect=reply) as fetch:
                candidate = fetch_candidate(flow, '2026-07', KEY, partner='-')
            query = parse_qs(urlsplit(fetch.call_args.args[0]).query)
            self.assertEqual(query['CTY_CODE'], ['-'])
            self.assertEqual(query['SUMMARY_LVL'], ['DET'])
            self.assertEqual(query['DISTRICT'], ['-'])
            self.assertTrue(set(query['get'][0].split(',')).isdisjoint(set(query) - {'get', 'key'}))
            self.assertEqual(candidate['rows'][0]['partnerCode'], '-')
            slot = {'flow': flow, 'period': '2026-07', 'product': '09', 'partner': '-'}
            validate_candidate(candidate, slot)
            altered = copy.deepcopy(candidate)
            altered['sourceQuery'].pop('SUMMARY_LVL')
            altered['candidateId'] = digest({k: altered[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
            with self.assertRaises(SourceError):
                validate_candidate(altered, slot)

    def test_world_missing_or_group_summary_fails_without_candidate(self):
        for summary, include in [('CGP', True), ('DET', False)]:
            with self.subTest(summary=summary, include=include), patch('pipeline.census.fetch_bytes', side_effect=lambda url: reply(url, summary, include)), self.assertRaises(SourceError):
                fetch_candidate('imports', '2026-07', KEY, partner='-')

    def test_reviewed_two_slot_world_plan_is_repeatable(self):
        plan = validate_plan(json.loads(PLAN_PATH.read_bytes()))
        self.assertEqual(len(plan['partitions']), 2)
        self.assertTrue(all(slot['partner'] == '-' for slot in plan['partitions']))
        with tempfile.TemporaryDirectory() as directory:
            with patch('pipeline.census.fetch_bytes', side_effect=reply):
                first = run_batch(plan, directory, KEY)
            with patch('pipeline.census.fetch_bytes', side_effect=AssertionError('Validated world evidence should resume offline')):
                second = run_batch(plan, directory, KEY)
            self.assertEqual(first, second)
            self.assertEqual(first, verify_bundle(plan, directory))
            self.assertEqual(first['coverage'], 'requested-partitions-only')
            self.assertIsNone(first['officialReleaseDate'])


if __name__ == '__main__':
    unittest.main()
