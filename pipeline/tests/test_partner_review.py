"""Offline, fabricated coverage scenarios never approve public data."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import partners
from pipeline.candidates import canonical, digest
from pipeline.census import SourceError
from pipeline.tests.test_partners import PLAN, evidence, files_at

try:
    from pipeline import partner_review
except ImportError:
    partner_review = None


def snapshot(observations=None, flow='imports', generation=1):
    candidate, raw = evidence(flow, observations)
    scan = partners.normalize_scan(candidate, raw, plan=PLAN, flow=flow)
    encoded = canonical(scan)
    receipt = partners._receipt(PLAN, flow, scan, encoded, raw)
    journal = partners._journal(PLAN, flow, generation, state='successful',
                                scan_id=scan['scanId'], receipt_id=receipt['receiptId'],
                                attempted_at='2026-10-02T01:02:03Z')
    return {'raw/' + scan['sourceHash'] + '.json': raw,
            'scans/' + scan['scanId'] + '.json': encoded,
            'receipts/' + receipt['receiptId'] + '.json': canonical(receipt),
            'progress.json': canonical(journal),
            'complete.json': canonical({'receiptId': receipt['receiptId']})}


class PartnerReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name) / 'repository'
        self.repository.mkdir()
        self.store = self.repository / '.local' / 'evidence' / 'imports'
        self.plan_path = self.repository / 'plan.json'
        self.plan_path.write_bytes(canonical(PLAN))
        self.output = self.repository / '.local' / 'partner-review' / 'imports.json'
        self.addCleanup(patch.stopall)
        patch('socket.socket', side_effect=AssertionError('Sockets are forbidden')).start()
        def environment_get(name, default=None):
            # argparse/gettext may ask about locale and terminal colors. Never
            # retrieve any real environment value; reject credential requests.
            if name.upper() in ('CENSUS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'):
                raise AssertionError('Credential environment lookups are forbidden')
            return default
        environment_type = type(os.environ)
        original_getitem = environment_type.__getitem__
        def environment_getitem(environment, name):
            if name.upper() in ('CENSUS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'):
                raise AssertionError('Credential environment lookups are forbidden')
            return original_getitem(environment, name)
        patch.object(os.environ, 'get', side_effect=environment_get).start()
        patch('os.getenv', side_effect=environment_get).start()
        patch.object(environment_type, '__getitem__', environment_getitem).start()

    def module(self):
        self.assertIsNotNone(partner_review, 'Bounded partner coverage diagnostics are missing')
        return partner_review

    def store_files(self, files):
        for name, raw in files.items():
            path = self.store / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def reviewed(self, files, assignments):
        review = self.module().make_review(PLAN, 'imports', files)
        for decision in review['decisions']:
            disposition = assignments.get(decision['code'], 'unresolved')
            decision.update(disposition=disposition,
                            rationale='Operator scenario evidence' if disposition != 'unresolved' else None,
                            references=['fabricated-source.v1'] if disposition != 'unresolved' else [])
        return review

    def cli(self, extra=(), failure=False):
        module = self.module()
        args = ['partner_review', '--plan', str(self.plan_path), '--flow', 'imports',
                '--snapshot', str(self.store), '--output', str(self.output), *extra]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(module, '_REPOSITORY_ROOT', self.repository), patch('sys.argv', args), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            if failure:
                with self.assertRaises(SystemExit) as result:
                    module.main()
                self.assertNotEqual(result.exception.code, 0)
            else:
                module.main()
        return stdout.getvalue(), stderr.getvalue()

    def assert_blocked(self, report):
        self.assertFalse(report['leafInventoryApproved'])
        self.assertFalse(report['apiVintageVerified'])
        self.assertFalse(report['publicationReady'])
        self.assertEqual(report['fullWorldReconciliation'], 'not-verified')
        self.assertEqual(report['coverage'], 'observed-partners-only')
        self.assertEqual(report['publicationBlockers'][:4], partners.BLOCKERS)

    def test_default_worksheet_binds_complete_source_and_has_only_observed_codes(self):
        files = snapshot()
        review = self.module().make_review(PLAN, 'imports', files)
        self.assertEqual(set(review), {'schemaVersion', 'state', 'decisionAuthority', 'scope', 'inputs', 'decisions'})
        self.assertEqual((review['schemaVersion'], review['state'], review['decisionAuthority']),
                         (1, 'draft-partner-review', 'operator-scenario-only'))
        self.assertEqual(review['scope'], {'planId': digest(PLAN), 'basis': PLAN['basis'],
                                          'flow': 'imports', 'period': '2026-07', 'product': '09', 'summaryLevel': 'DET'})
        state = partners.validate_snapshot(PLAN, 'imports', files, require_complete=True)
        self.assertEqual(review['inputs'], {field: state['receipt'][field]
                                          for field in ('scanId', 'receiptId', 'sourceHash', 'objectHash')})
        self.assertEqual(review['decisions'], [
            {'code': '1220', 'disposition': 'unresolved', 'rationale': None, 'references': []},
            {'code': '9999', 'disposition': 'unresolved', 'rationale': None, 'references': []}])

    def test_default_report_exact_shape_totals_zero_status_provenance_and_identity(self):
        report = self.module().build_diagnostics(PLAN, 'imports', snapshot())
        self.assertEqual(set(report), {'schemaVersion', 'state', 'decisionAuthority', 'scope', 'inputs',
                                      'reviewId', 'review', 'rows', 'world', 'totals', 'counts', 'residuals',
                                      'provenance', 'coverage', 'leafInventoryApproved', 'apiVintageVerified',
                                      'fullWorldReconciliation', 'publicationReady', 'publicationBlockers', 'reportId'})
        self.assertEqual(report['state'], 'private-coverage-diagnostic')
        self.assertEqual(report['decisionAuthority'], 'operator-scenario-only')
        self.assertEqual(report['totals'], {'observedUSD': '7', 'includedUSD': '0', 'excludedUSD': '0', 'unresolvedUSD': '7'})
        self.assertEqual(report['counts'], {'observed': 2, 'included': 0, 'excluded': 0, 'unresolved': 2})
        self.assertEqual(report['residuals'], {'observedMinusWorldUSD': '-93', 'includedMinusWorldUSD': '-100'})
        self.assertEqual(report['world'], {'status': 'reported', 'value': '100'})
        self.assertEqual(report['rows'][0], {'code': '1220', 'name': 'Canada', 'status': 'reported_zero',
                                          'value': '0', 'disposition': 'unresolved'})
        self.assertEqual(report['provenance'], {'officialReleaseDate': None, 'officialRevisionDate': None,
                                              'ingestedAt': '2026-10-02T01:02:03Z', 'revisionDetectedAt': None})
        self.assertEqual(report['reviewId'], digest(report['review']))
        self.assertEqual(report['reportId'], digest({k: v for k, v in report.items() if k != 'reportId'}))
        self.assert_blocked(report)

    def test_exact_integer_scenarios_above_javascript_precision_and_signed_residuals(self):
        files = snapshot([('1220', 'First', '9007199254740993'), ('9999', 'Second', '7'),
                          ('2010', 'Third', '0'), ('-', 'World', '9007199254740998')])
        review = self.reviewed(files, {'1220': 'include', '9999': 'exclude'})
        report = self.module().build_diagnostics(PLAN, 'imports', files, review)
        self.assertEqual(report['totals'], {'observedUSD': '9007199254741000', 'includedUSD': '9007199254740993',
                                          'excludedUSD': '7', 'unresolvedUSD': '0'})
        self.assertEqual(report['counts'], {'observed': 3, 'included': 1, 'excluded': 1, 'unresolved': 1})
        self.assertEqual(report['residuals'], {'observedMinusWorldUSD': '2', 'includedMinusWorldUSD': '-5'})
        self.assert_blocked(report)

    def test_all_classified_and_zero_residual_never_approve_inventory_or_vintage(self):
        files = snapshot([('1220', 'First', '5'), ('9999', 'Second', '2'), ('-', 'World', '7')])
        review = self.reviewed(files, {'1220': 'include', '9999': 'include'})
        report = self.module().build_diagnostics(PLAN, 'imports', files, review)
        self.assertEqual(report['counts'], {'observed': 2, 'included': 2, 'excluded': 0, 'unresolved': 0})
        self.assertEqual(report['residuals'], {'observedMinusWorldUSD': '0', 'includedMinusWorldUSD': '0'})
        self.assert_blocked(report)

    def test_unobserved_world_is_distinct_from_reported_zero_and_empty_categories(self):
        for observations, world, residuals, blockers in [
            ([('9999', 'Only', '0')], {'status': 'unobserved', 'value': None},
             {'observedMinusWorldUSD': None, 'includedMinusWorldUSD': None}, 5),
            ([('-', 'World', '0')], {'status': 'reported_zero', 'value': '0'},
             {'observedMinusWorldUSD': '0', 'includedMinusWorldUSD': '0'}, 4)]:
            with self.subTest(world=world):
                report = self.module().build_diagnostics(PLAN, 'imports', snapshot(observations))
                self.assertEqual(report['world'], world)
                self.assertEqual(report['residuals'], residuals)
                self.assertEqual(report['totals'], dict.fromkeys(
                    ('observedUSD', 'includedUSD', 'excludedUSD', 'unresolvedUSD'), '0'))
                self.assertEqual(len(report['publicationBlockers']), blockers)
                self.assert_blocked(report)
        missing = self.module().build_diagnostics(PLAN, 'imports', snapshot([('9999', 'Only', '0')]))
        self.assertIn('world', missing['publicationBlockers'][-1].lower())

    def test_output_is_deterministic_and_sorts_operator_decisions_without_mutation(self):
        files = snapshot()
        review = self.reviewed(files, {'1220': 'include', '9999': 'exclude'})
        review['decisions'].reverse()
        before = copy.deepcopy(review)
        report = self.module().build_diagnostics(PLAN, 'imports', files, review)
        reordered = self.module().build_diagnostics(PLAN, 'imports', dict(reversed(list(files.items()))), review)
        self.assertEqual(canonical(report), canonical(reordered))
        self.assertEqual(review, before)
        self.assertEqual([d['code'] for d in report['review']['decisions']], ['1220', '9999'])

    def test_worksheet_rejects_copied_names_values_approval_flags_and_report(self):
        files = snapshot()
        module = self.module()
        review = module.make_review(PLAN, 'imports', files)
        mutations = []
        for field in ('publicationReady', 'leafInventoryApproved', 'reviewId', 'extra'):
            bad = copy.deepcopy(review)
            bad[field] = True
            mutations.append(bad)
        for field in ('name', 'value', 'status', 'approved'):
            bad = copy.deepcopy(review)
            bad['decisions'][0][field] = 'Copied evidence'
            mutations.append(bad)
        mutations.append(module.build_diagnostics(PLAN, 'imports', files))
        for bad in mutations:
            with self.subTest(fields=list(bad)):
                with self.assertRaises(SourceError):
                    module.build_diagnostics(PLAN, 'imports', files, bad)

    def test_worksheet_rejects_missing_extra_duplicate_world_and_nonstring_codes(self):
        files = snapshot()
        review = self.module().make_review(PLAN, 'imports', files)
        variants = [[], review['decisions'][:1], review['decisions'] + [review['decisions'][0]],
                    review['decisions'] + [{'code': '-', 'disposition': 'unresolved', 'rationale': None, 'references': []}]]
        for code in ('2010', 1220, '01220'):
            bad = copy.deepcopy(review['decisions'])
            bad[0]['code'] = code
            variants.append(bad)
        for decisions in variants:
            with self.subTest(decisions=decisions):
                with self.assertRaises(SourceError):
                    self.module().build_diagnostics(PLAN, 'imports', files, {**review, 'decisions': decisions})

    def test_scope_source_receipt_and_generation_bindings_cannot_be_changed(self):
        files = snapshot()
        module = self.module()
        review = module.make_review(PLAN, 'imports', files)
        for container in ('scope', 'inputs'):
            for field in review[container]:
                bad = copy.deepcopy(review)
                bad[container][field] = 'changed'
                with self.subTest(container=container, field=field), self.assertRaises(SourceError):
                    module.build_diagnostics(PLAN, 'imports', files, bad)
        for field, value in [('schemaVersion', True), ('state', 'approved'), ('decisionAuthority', 'official')]:
            with self.subTest(field=field), self.assertRaises(SourceError):
                module.build_diagnostics(PLAN, 'imports', files, {**review, field: value})
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'exports', snapshot(flow='exports'), review)
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', snapshot([('1220', 'Changed', '0')]), review)
        bad = copy.deepcopy(files)
        journal = partners._journal(PLAN, 'imports', 2, attempted_at='2026-10-02T01:02:03Z')
        bad['progress.json'] = canonical(journal)
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', bad, review)

    def test_dispositions_require_bounded_text_and_reference_labels(self):
        files = snapshot()
        review = self.reviewed(files, {'1220': 'include'})
        base = review['decisions'][0]
        cases = [('disposition', 'approved'), ('disposition', []), ('rationale', None),
                 ('rationale', ''), ('rationale', ' \t'), ('rationale', 'x' * 251),
                 ('rationale', 'bad\x00note'), ('rationale', 'bad\x7fnote'),
                 ('references', []), ('references', ['dup', 'dup']),
                 ('references', ['a'] * 11), ('references', ['https://example.invalid']),
                 ('references', ['../path']), ('references', ['CAPS']),
                 ('references', ['a' * 81]), ('references', [1]), ('references', None)]
        for field, value in cases:
            bad = copy.deepcopy(review)
            bad['decisions'][0] = {**base, field: value}
            with self.subTest(field=field, value=value), self.assertRaises(SourceError):
                self.module().build_diagnostics(PLAN, 'imports', files, bad)
        good = copy.deepcopy(review)
        good['decisions'][0].update(rationale='x' * 250, references=['a' * 80] + ['r' + str(i) for i in range(9)])
        self.module().build_diagnostics(PLAN, 'imports', files, good)

    def test_unresolved_notes_require_the_same_pair_or_the_empty_default(self):
        files = snapshot()
        review = self.module().make_review(PLAN, 'imports', files)
        for rationale, references, accepted in [
            ('Still investigating', ['review-pending'], True), (None, [], True),
            (None, ['source'], False), ('Note', [], False), ('', [], False)]:
            bad = copy.deepcopy(review)
            bad['decisions'][0].update(rationale=rationale, references=references)
            if accepted:
                self.module().build_diagnostics(PLAN, 'imports', files, bad)
            else:
                with self.assertRaises(SourceError):
                    self.module().build_diagnostics(PLAN, 'imports', files, bad)

    def test_corrupt_raw_scan_receipt_and_stale_pointer_are_rejected(self):
        files = snapshot()
        module = self.module()
        for name in files:
            bad = dict(files)
            bad[name] = b'{}'
            with self.subTest(name=name):
                for call in (module.make_review, module.build_diagnostics):
                    with self.assertRaises(SourceError):
                        call(PLAN, 'imports', bad)
        bad = dict(files)
        bad['complete.json'] = canonical({'receiptId': 'a' * 64})
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', bad)

    def test_snapshot_row_and_total_byte_bounds_are_kept(self):
        module = self.module()
        many = [(str(1000 + i), 'Partner', '1') for i in range(501)]
        candidate, raw = evidence(observations=many)
        with self.assertRaises(SourceError):
            partners.normalize_scan(candidate, raw, plan=PLAN, flow='imports')
        files = snapshot()
        files['raw/' + 'a' * 64 + '.json'] = b' ' * (2 * 1024 * 1024 + 1)
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', files)

    def test_known_escaped_secret_in_notes_or_source_is_rejected(self):
        module = self.module()
        for secret in ('fabricated"quoted-key', 'fabricated\\backslash-key', 'fabricated-é-key'):
            with self.subTest(secret=secret):
                files = snapshot()
                review = self.reviewed(files, {'1220': 'include'})
                review['decisions'][0]['rationale'] = secret
                with self.assertRaises(SourceError):
                    module.build_diagnostics(PLAN, 'imports', files, review, secrets=(secret,))
                reflected = snapshot([('1220', secret, '1')])
                with self.assertRaises(SourceError):
                    module.make_review(PLAN, 'imports', reflected, secrets=(secret,))

    def test_worksheet_and_report_encoded_bounds_reject_without_truncation(self):
        module = self.module()
        observations = [(str(1000 + i), 'Partner', '1') for i in range(400)]
        files = snapshot(observations)
        review = self.reviewed(files, {code: 'include' for code, _, _ in observations})
        for decision in review['decisions']:
            decision.update(rationale='x' * 250, references=['r' + str(i) + '-' + 'x' * 70 for i in range(10)])
        self.assertGreater(len(canonical(review)), 256 * 1024)
        with self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', files, review)
        with patch.object(module, 'MAX_REPORT_BYTES', 200), self.assertRaises(SourceError):
            module.build_diagnostics(PLAN, 'imports', snapshot())

    def test_reader_returns_validated_current_state_and_verify_receipt_is_compatible(self):
        self.assertTrue(callable(getattr(partners, 'read_partner_snapshot', None)),
                        'A single-load validated partner snapshot reader is missing')
        files = snapshot()
        self.store_files(files)
        state = partners.read_partner_snapshot(PLAN, 'imports', self.store)
        self.assertTrue(state['complete'])
        self.assertEqual(state['receipt'], partners.verify_partner_scan(PLAN, 'imports', self.store))
        with patch('pipeline.partners._stored_files', wraps=partners._stored_files) as read:
            state = partners.read_partner_snapshot(PLAN, 'imports', self.store)
        self.assertEqual(read.call_count, 1)
        self.assertEqual(state['scans'][state['receipt']['scanId']]['rows'][1]['value'], '0')

    def test_reader_rejects_stale_corrupt_and_symlinked_input(self):
        self.assertTrue(callable(getattr(partners, 'read_partner_snapshot', None)),
                        'A single-load validated partner snapshot reader is missing')
        files = snapshot()
        self.store_files(files)
        for name in ('progress.json', 'complete.json', next(name for name in files if name.startswith('raw/'))):
            path = self.store / name
            original = path.read_bytes()
            path.write_bytes(b'{}')
            with self.subTest(name=name), self.assertRaises(SourceError):
                partners.read_partner_snapshot(PLAN, 'imports', self.store)
            path.write_bytes(original)
        with patch.object(Path, 'is_junction', lambda path: path == self.store.parent):
            with self.assertRaises(SourceError):
                partners.read_partner_snapshot(PLAN, 'imports', self.store)

    def test_cli_offline_single_read_default_private_report_and_counts_only_stdout(self):
        module = self.module()
        self.store_files(snapshot())
        with patch('pipeline.partners._stored_files', wraps=partners._stored_files) as read:
            stdout, stderr = self.cli()
        self.assertEqual(read.call_count, 1)
        self.assertEqual(stderr, '')
        self.assertIn('2 observed', stdout)
        self.assertIn('0 included', stdout)
        self.assertIn('0 excluded', stdout)
        self.assertIn('2 unresolved', stdout)
        self.assertIn('publication remains blocked', stdout)
        self.assertNotIn('Canada', stdout)
        self.assertNotIn('100', stdout)
        report = module._read_json(self.output, module.MAX_REPORT_BYTES)
        self.assert_blocked(report)
        self.assertEqual(report['totals']['observedUSD'], '7')
        self.assertEqual(sorted(files_at(self.store)), sorted(snapshot()))

    def test_cli_accepts_extracted_review_and_preserves_input_bytes(self):
        files = snapshot()
        self.store_files(files)
        worksheet = self.repository / '.local' / 'worksheet.json'
        raw = canonical(self.reviewed(files, {'1220': 'include', '9999': 'exclude'}))
        worksheet.write_bytes(raw)
        self.cli(['--review', str(worksheet)])
        self.assertEqual(worksheet.read_bytes(), raw)
        self.assertEqual(files_at(self.store), files)
        report = self.module()._read_json(self.output, self.module().MAX_REPORT_BYTES)
        self.assertEqual(report['counts'], {'observed': 2, 'included': 1, 'excluded': 1, 'unresolved': 0})

    def test_cli_rejects_public_snapshot_and_input_overwrite_before_directory_creation(self):
        self.store_files(snapshot())
        worksheet = self.repository / '.local' / 'worksheet.json'
        worksheet.write_bytes(canonical(self.module().make_review(PLAN, 'imports', snapshot())))
        local_plan = self.repository / '.local' / 'plan.json'
        local_plan.write_bytes(canonical(PLAN))
        cases = [(self.repository / 'public' / 'data.json', []),
                 (self.repository / '.local' / '..' / 'public' / 'data.json', []),
                 (self.repository / '.local' / 'reports' / 'wrong.txt', []),
                 (self.store / 'new' / 'diagnostic.json', []),
                 (worksheet, ['--review', str(worksheet)]),
                 (local_plan, ['--plan', str(local_plan)])]
        for output, extra in cases:
            with self.subTest(output=output):
                before = output.read_bytes() if output.is_file() else None
                self.output = output
                stdout, stderr = self.cli(extra, failure=True)
                self.assertEqual(stdout, '')
                self.assertNotIn(str(output), stderr)
                self.assertEqual(output.read_bytes() if output.is_file() else None, before)
        self.assertFalse((self.repository / 'public').exists())
        self.assertFalse((self.store / 'new').exists())
        self.assertFalse((self.repository / '.local' / 'reports').exists())

    def test_cli_rejects_symlink_or_junction_files_and_ancestors(self):
        self.store_files(snapshot())
        module = self.module()
        for unsafe in (self.plan_path, self.plan_path.parent, self.store,
                       self.output, self.output.parent, self.repository / '.local'):
            with self.subTest(unsafe=unsafe), patch.object(Path, 'is_junction', lambda path: path == unsafe):
                self.cli(failure=True)
        worksheet = self.repository / '.local' / 'worksheet.json'
        worksheet.write_bytes(canonical(module.make_review(PLAN, 'imports', snapshot())))
        with patch.object(Path, 'is_symlink', lambda path: path == worksheet):
            self.cli(['--review', str(worksheet)], failure=True)
        self.assertFalse(self.output.exists())

    def test_cli_rejects_real_symlinked_output_and_preserves_target(self):
        self.module()
        self.store_files(snapshot())
        self.output.parent.mkdir(parents=True)
        target = self.repository / 'target.json'
        target.write_bytes(b'preserved')
        try:
            os.symlink(target, self.output)
        except OSError:
            self.skipTest('Creating symlinks is unavailable in this environment')
        self.cli(failure=True)
        self.assertEqual(target.read_bytes(), b'preserved')
        self.assertTrue(self.output.is_symlink())

    def test_cli_duplicate_nonfinite_and_oversized_json_preserve_previous_output(self):
        self.store_files(snapshot())
        self.cli()
        previous = self.output.read_bytes()
        worksheet = self.repository / '.local' / 'worksheet.json'
        for raw in (b'{"schemaVersion":1,"schemaVersion":1}', b'{"schemaVersion":NaN}',
                    b'{"schemaVersion":Infinity}', b' ' * (256 * 1024 + 1), b'[' * 2000):
            worksheet.write_bytes(raw)
            stdout, stderr = self.cli(['--review', str(worksheet)], failure=True)
            self.assertEqual(stdout, '')
            self.assertEqual(self.output.read_bytes(), previous)
            self.assertNotIn('schemaVersion', stderr)
        original_plan = self.plan_path.read_bytes()
        for raw in (b'{"basis":"x","basis":"y"}', b'{"schemaVersion":NaN}', b' ' * (512 * 1024 + 1)):
            self.plan_path.write_bytes(raw)
            self.cli(failure=True)
            self.assertEqual(self.output.read_bytes(), previous)
        self.plan_path.write_bytes(original_plan)

    def test_cli_corrupt_snapshot_or_invalid_worksheet_never_creates_output_parent(self):
        files = snapshot()
        self.store_files(files)
        (self.store / 'complete.json').write_bytes(b'{}')
        self.cli(failure=True)
        self.assertFalse(self.output.parent.exists())
        self.store_files(files)
        worksheet = self.repository / '.local' / 'worksheet.json'
        worksheet.write_bytes(canonical({**self.module().make_review(PLAN, 'imports', files), 'publicationReady': True}))
        self.cli(['--review', str(worksheet)], failure=True)
        self.assertFalse(self.output.parent.exists())

    def test_atomic_replace_failure_preserves_previous_valid_output_and_cleans_pending_file(self):
        self.store_files(snapshot())
        self.cli()
        previous = self.output.read_bytes()
        worksheet = self.repository / '.local' / 'worksheet.json'
        worksheet.write_bytes(canonical(self.reviewed(snapshot(), {'1220': 'include'})))
        with patch('pipeline.batch.os.replace', side_effect=OSError('https://unsafe.invalid/private-note')):
            stdout, stderr = self.cli(['--review', str(worksheet)], failure=True)
        self.assertEqual(stdout, '')
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertEqual(list(self.output.parent.glob('.pending-*')), [])
        self.assertNotIn('https://', stderr)
        self.assertNotIn('private-note', stderr)

    def test_cli_parser_and_runtime_errors_never_echo_bad_arguments_or_notes(self):
        self.store_files(snapshot())
        for extra in (['--flow', 'https://unsafe.invalid/?credential=fabricated'],
                      ['--unknown', 'private-note'], ['--plan', 'private-note-missing.json']):
            stdout, stderr = self.cli(extra, failure=True)
            self.assertEqual(stdout, '')
            self.assertNotIn('https://', stderr)
            self.assertNotIn('private-note', stderr)
            self.assertNotIn('fabricated', stderr)


if __name__ == '__main__':
    unittest.main()
