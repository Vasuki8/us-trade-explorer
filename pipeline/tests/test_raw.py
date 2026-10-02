"""Exact source-byte provenance and known-secret boundaries; values are fabricated."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import raw
from pipeline.batch import MAX_FILE_BYTES, validate_plan, validate_snapshot, run_batch
from pipeline.candidates import digest
from pipeline.census import SourceError, fetch_candidate
from pipeline.tests.test_batches import PLAN, SLOT, KEY, source_response


class RawSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def captured(self, flow='imports', partner='1220', value='123456'):
        captured = []
        def response(url):
            return b' \n' + source_response(url, value=value) + b'\n'
        with patch('pipeline.census.fetch_bytes', side_effect=response):
            candidate = fetch_candidate(flow, '2026-07', KEY, partner=partner, capture=captured.append)
        self.assertEqual(len(captured), 1)
        return candidate, captured[0], {'flow': flow, 'period': '2026-07', 'product': '09', 'partner': partner}

    def test_validated_capture_preserves_exact_source_bytes_and_candidate_identity(self):
        for flow, partner in [('imports', '1220'), ('exports', '1220'), ('imports', '-'), ('exports', '-')]:
            with self.subTest(flow=flow, partner=partner):
                candidate, body, slot = self.captured(flow, partner)
                self.assertTrue(body.startswith(b' \n'))
                self.assertEqual(candidate['sourceHash'], hashlib.sha256(body).hexdigest())
                self.assertEqual(raw.validate_raw_response(body, candidate, slot, secrets=(KEY,)), body)
                with patch('pipeline.census.fetch_bytes', return_value=body):
                    legacy = fetch_candidate(flow, '2026-07', KEY, partner=partner)
                self.assertEqual(candidate['candidateId'], legacy['candidateId'])
                self.assertNotIn('key', candidate['sourceQuery'])

    def test_failed_source_validation_never_invokes_capture(self):
        captured = []
        for body in [b'not JSON', json.dumps([['CTY_CODE'], [KEY]]).encode()]:
            with self.subTest(body=body), patch('pipeline.census.fetch_bytes', return_value=body), self.assertRaises(SourceError):
                fetch_candidate('imports', '2026-07', KEY, capture=captured.append)
        self.assertEqual(captured, [])

    def test_independent_raw_reparse_rejects_valid_normalized_but_different_values(self):
        candidate, body, slot = self.captured()
        changed = copy.deepcopy(candidate)
        changed['rows'][0]['value'] = '17'
        with self.assertRaises(SourceError):
            raw.validate_raw_response(body, changed, slot)
        with self.assertRaises(SourceError):
            raw.validate_raw_response(body + b' ', candidate, slot)

    def test_raw_dimensions_must_match_even_after_identity_is_recomputed(self):
        candidate, body, slot = self.captured()
        table = json.loads(body)
        table[1][table[0].index('DISTRICT')] = '01'
        changed_body = json.dumps(table).encode()
        changed = copy.deepcopy(candidate)
        changed['sourceHash'] = hashlib.sha256(changed_body).hexdigest()
        changed['candidateId'] = digest({k: changed[k] for k in ('schemaVersion', 'flow', 'period', 'sourceQuery', 'sourceHash')})
        with self.assertRaises(SourceError):
            raw.validate_raw_response(changed_body, changed, slot)

    def test_zero_is_reported_and_multiple_or_unexpected_slots_are_rejected(self):
        candidate, body, slot = self.captured(value='0')
        self.assertEqual(candidate['rows'][0]['status'], 'reported_zero')
        raw.validate_raw_response(body, candidate, slot)
        with self.assertRaises(SourceError):
            raw.validate_raw_response(body, candidate, {**slot, 'partner': '2010'})

    def test_escaped_github_secret_and_oversized_body_never_enter_raw_store(self):
        secret = 'github-raw-canary'
        for failure in ('secret', 'oversized'):
            output = self.root / failure
            def response(url):
                body = source_response(url)
                if failure == 'secret':
                    return body.replace(b'Canada', ''.join('\\u%04x' % ord(c) for c in secret).encode())
                return b' ' * MAX_FILE_BYTES + body
            with self.subTest(failure=failure), patch('pipeline.census.fetch_bytes', side_effect=response), self.assertRaises(SourceError) as raised:
                raw.acquire_with_raw('imports', '2026-07', KEY, product='09', partner='1220', root=output, evidence_secrets=(secret,))
            self.assertNotIn(secret, str(raised.exception))
            self.assertFalse(output.exists())

    def test_content_addressed_raw_reuse_checks_corruption_before_overwriting(self):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            first = raw.acquire_with_raw('imports', '2026-07', KEY, product='09', partner='1220', root=self.root)
            second = raw.acquire_with_raw('imports', '2026-07', KEY, product='09', partner='1220', root=self.root)
        self.assertEqual(first['candidateId'], second['candidateId'])
        files = list((self.root / 'raw').glob('*.json'))
        self.assertEqual(len(files), 1)
        self.assertEqual(hashlib.sha256(files[0].read_bytes()).hexdigest(), first['sourceHash'])
        files[0].write_bytes(b'corrupt')
        with patch('pipeline.census.fetch_bytes', side_effect=source_response), self.assertRaises(SourceError):
            raw.acquire_with_raw('imports', '2026-07', KEY, product='09', partner='1220', root=self.root)
        self.assertEqual(files[0].read_bytes(), b'corrupt')

    def test_acquisition_injection_persists_raw_before_marking_slot_successful(self):
        def acquire(flow, period, key, *, product, partner):
            return raw.acquire_with_raw(flow, period, key, product=product, partner=partner, root=self.root)
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            bundle = run_batch(PLAN, self.root, KEY, acquire=acquire)
        self.assertEqual(len(bundle['partitions']), 2)
        self.assertEqual(len(list((self.root / 'raw').glob('*.json'))), 2)

    def test_normalized_snapshot_validation_is_pure_and_still_rejects_raw_paths(self):
        with patch('pipeline.census.fetch_bytes', side_effect=source_response):
            run_batch(PLAN, self.root, KEY)
        files = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob('*.json')}
        before = dict(files)
        verified = validate_snapshot(validate_plan(PLAN), files, secrets=(KEY,))
        self.assertEqual(len(verified['objects']), 2)
        self.assertTrue(all(entry['state'] == 'successful' for entry in verified['journal']['entries']))
        self.assertEqual(files, before)
        with self.assertRaises(SourceError):
            validate_snapshot(PLAN, {**files, 'raw/' + 'a' * 64 + '.json': b'[]'})


if __name__ == '__main__':
    unittest.main()
