"""Single-month research binds classification evidence without inventing continuity."""
import copy
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import partner_review, selected_partners
from pipeline.candidates import canonical, digest
from pipeline.census import SourceError
from pipeline.tests.test_partner_review import snapshot
from pipeline.tests.test_partners import PLAN
from pipeline.tests.test_selected_partners import ANNEXES, ROWS

try:
    from pipeline import research
except ImportError:
    research = None


DOCUMENTS = {
    'imports': {f'hts-2026-rev{rev}-chapter09.pdf': f'%PDF-fabricated-import-{rev}'.encode()
                for rev in (11, 12, 13, 14)},
    'exports': {'schedule-b-2026-index.html': b'<html>Fabricated index</html>',
                'schedule-b-2026-chapter09.pdf': b'%PDF-fabricated-export-chapter'},
}


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(research, 'Single-period research assembly is missing')
        self.addCleanup(patch.stopall)
        patch.object(selected_partners, 'ANNEX_PINS', tuple(
            (edition, len(raw), sha256(raw).hexdigest()) for edition, raw in ANNEXES.items())).start()
        patch.object(research, 'CLASSIFICATION_PINS', {
            flow: tuple((name, len(raw), sha256(raw).hexdigest()) for name, raw in documents.items())
            for flow, documents in DOCUMENTS.items()}).start()
        patch('socket.socket', side_effect=AssertionError('Network prohibited')).start()
        patch('subprocess.run', side_effect=AssertionError('Subprocess prohibited')).start()
        original = type(os.environ).__getitem__
        def getitem(environment, name):
            if name.upper() in ('CENSUS_API_KEY', 'GITHUB_TOKEN', 'GH_TOKEN'):
                raise AssertionError('Credential lookup prohibited')
            return original(environment, name)
        patch.object(type(os.environ), '__getitem__', getitem).start()

    def build(self, flow='imports', files=None, documents=None, plan=None):
        return research.build_slice(PLAN if plan is None else plan, flow,
                                    snapshot(ROWS, flow) if files is None else files, ANNEXES,
                                    DOCUMENTS[flow] if documents is None else documents)

    def test_assembles_validated_values_without_reinterpreting_basis_or_coverage(self):
        files = snapshot(ROWS)
        result = self.build(files=files)
        self.assertEqual(result['state'], 'private-single-period-research')
        self.assertEqual(result['selectedTrade'], selected_partners.build_report(PLAN, 'imports', files, ANNEXES))
        self.assertEqual(result['classification']['chapter'], '09')
        self.assertEqual(result['classification']['label'], 'Coffee, tea, maté and spices')
        self.assertEqual(result['selectedTrade']['totals']['selectedShareOfWorldPercent'], '60.00')
        self.assertIs(result['publicationReady'], False)

    def test_import_and_export_classifications_and_source_documents_remain_separate(self):
        for flow, system, count in [('imports', 'HTSUS', 4), ('exports', 'Schedule B', 2)]:
            classification = self.build(flow)['classification']
            self.assertEqual(classification['system'], system)
            self.assertEqual(classification['flow'], flow)
            self.assertEqual(classification['level'], 'HS2')
            self.assertEqual(classification['reviewedReportingPeriod'], '2026-07')
            self.assertEqual(len(classification['documents']), count)
            self.assertEqual({document['file'] for document in classification['documents']}, set(DOCUMENTS[flow]))
            self.assertTrue(all(document['sourceURL'].startswith('https://') for document in classification['documents']))

    def test_known_document_dates_do_not_invent_api_vintage_or_effective_intervals(self):
        for flow in DOCUMENTS:
            result = self.build(flow)
            self.assertIsNone(result['classification']['provisionEffectiveFromVerified'])
            self.assertEqual(result['classification']['apiClassificationVintage'], 'not-identified')
            self.assertEqual(result['classification']['historicalComparability'], 'not-established')
            provenance = result['selectedTrade']['provenance']
            self.assertIsNone(provenance['officialMetadata']['officialRevisionDate'])
            self.assertIs(provenance['classificationComparabilityVerified'], False)
        self.assertEqual(self.build('exports')['classification']['editionDateEvidence'],
                         {'role': 'index-use-after-label', 'date': '2026-07-01'})
        self.assertIsNone(self.build()['classification']['editionDateEvidence'])

    def test_analysis_policy_limits_what_one_month_of_selected_country_values_supports(self):
        policy = self.build()['analysisPolicy']
        self.assertEqual(policy['countryValues'], 'selected-countries-same-flow-and-period-only')
        self.assertEqual(policy['countryWorldShares'], 'requires-observed-positive-world-control')
        for metric in ('historicalGrowth', 'fineCodeJoins', 'quantityMetrics', 'globalRankingsAndConcentration'):
            self.assertEqual(policy[metric], 'not-supported')

    def test_missing_rows_and_world_are_preserved_under_classification_context(self):
        result = self.build(files=snapshot([row for row in ROWS if row[0] not in ('-', '5330')]))
        report = result['selectedTrade']
        self.assertEqual(report['rows'][2]['status'], 'unobserved')
        self.assertIsNone(report['rows'][2]['value'])
        self.assertIsNone(report['totals']['selectedTotalUSD'])
        self.assertTrue(all(row['shareOfWorldPercent'] is None for row in report['rows']))
        self.assertIs(report['coverage']['globalCoverageComplete'], False)

    def test_classification_hash_size_types_and_exact_membership_are_required(self):
        for change in ('missing', 'extra', 'modified', 'wrong-type', 'oversized', 'other-flow'):
            documents = dict(DOCUMENTS['imports'])
            first = next(iter(documents))
            if change == 'missing': documents.pop(first)
            if change == 'extra': documents['unreviewed.pdf'] = b'%PDF-extra'
            if change == 'modified': documents[first] = b'X' + documents[first][1:]
            if change == 'wrong-type': documents[first] = documents[first].decode()
            if change == 'oversized': documents[first] += b'x'
            if change == 'other-flow': documents = DOCUMENTS['exports']
            with self.subTest(change=change), self.assertRaises(SourceError):
                self.build(documents=documents)

    def test_other_period_chapter_level_or_flow_cannot_inherit_review(self):
        for field, value in [('period', '2025-07'), ('product', '0901'), ('summaryLevel', 'CGP')]:
            plan = {**PLAN, field: value}
            with self.subTest(field=field), self.assertRaises(SourceError): self.build(plan=plan)
        with self.assertRaises(SourceError):
            research.build_slice(PLAN, 'reexports', snapshot(ROWS), ANNEXES, DOCUMENTS['exports'])

    def test_incomplete_archive_and_tampered_selected_values_fail_before_assembly(self):
        files = snapshot(ROWS)
        del files['complete.json']
        with self.assertRaises(SourceError): self.build(files=files)
        with self.assertRaises(SourceError):
            self.build(files=snapshot([(code, name, '1' if code == '-' else value) for code, name, value in ROWS]))

    def test_rehashed_invented_classification_and_capabilities_cannot_validate(self):
        original = self.build()
        mutations = [lambda r: r.update(publicationReady=True),
                     lambda r: r.update(schemaVersion=True),
                     lambda r: r['classification'].update(system='shared-import-export-codes'),
                     lambda r: r['classification'].update(provisionEffectiveFromVerified='2026-07-01'),
                     lambda r: r['classification']['documents'][0].update(sha256='0'*64),
                     lambda r: r['analysisPolicy'].update(historicalGrowth='supported'),
                     lambda r: r['selectedTrade']['rows'][0].update(value='99')]
        for mutate in mutations:
            result = copy.deepcopy(original)
            mutate(result)
            result['sliceId'] = digest({key: value for key, value in result.items() if key != 'sliceId'})
            with self.assertRaises(SourceError):
                research.validate_slice(PLAN, 'imports', snapshot(ROWS), ANNEXES, DOCUMENTS['imports'], result)

    def test_repeatable_offline_rebuild_preserves_inputs(self):
        files, documents = snapshot(ROWS), dict(DOCUMENTS['imports'])
        before = copy.deepcopy((files, ANNEXES, documents))
        result = self.build(files=files, documents=documents)
        self.assertEqual(result, self.build(files=files, documents=documents))
        self.assertEqual((files, ANNEXES, documents), before)
        self.assertEqual(result, research.validate_slice(PLAN, 'imports', files, ANNEXES, documents, result))

    def test_secret_reflection_and_oversized_report_are_rejected(self):
        files = snapshot([(code, 'secret-canary' if code == '1220' else name, value) for code, name, value in ROWS])
        with self.assertRaises(SourceError):
            research.build_slice(PLAN, 'imports', files, ANNEXES, DOCUMENTS['imports'], secrets=('secret-canary',))
        with self.assertRaises(SourceError):
            research.validate_slice(PLAN, 'imports', snapshot(ROWS), ANNEXES, DOCUMENTS['imports'],
                                    {'payload': 'x' * research.MAX_SLICE_BYTES})

    def test_cli_atomic_output_safe_paths_and_failure_preserves_prior_slice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, annex_dir, chapter_dir = [root / '.local' / name for name in ('archive', 'annexes', 'chapters')]
            for name, raw in snapshot(ROWS).items():
                path = archive / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            annex_dir.mkdir(); chapter_dir.mkdir()
            for edition, raw in ANNEXES.items(): (annex_dir / f'{edition}.pdf').write_bytes(raw)
            for name, raw in DOCUMENTS['imports'].items(): (chapter_dir / name).write_bytes(raw)
            plan = root / 'plan.json'; plan.write_bytes(canonical(PLAN))
            output = root / '.local' / 'research' / 'imports.json'
            arguments = ['research', '--plan', str(plan), '--flow', 'imports', '--snapshot', str(archive),
                         '--annex-dir', str(annex_dir), '--classification-dir', str(chapter_dir), '--output', str(output)]
            with patch.object(partner_review, '_REPOSITORY_ROOT', root), patch('sys.argv', arguments):
                with redirect_stdout(io.StringIO()) as stdout: research.main()
                self.assertNotIn('60', stdout.getvalue())
                before = output.read_bytes()
                for unsafe in (root / 'public' / 'data.json', archive / 'new.json', plan):
                    with patch('sys.argv', [*arguments[:-1], str(unsafe)]), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                        research.main()
                (chapter_dir / next(iter(DOCUMENTS['imports']))).write_bytes(b'%PDF-changed')
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error: research.main()
                self.assertEqual(error.exception.code, 1)
                self.assertEqual(output.read_bytes(), before)
                self.assertFalse((root / 'public').exists())


class ClassificationPinTests(unittest.TestCase):
    def test_production_pin_metadata_matches_reviewed_document_registry(self):
        self.assertIsNotNone(research, 'Single-period research assembly is missing')
        root = Path(__file__).resolve().parents[2]
        registry = json.loads((root / 'sources/chapter09-evidence-2026-07.json').read_bytes())
        documents = {row['file']: row for row in registry['documents']}
        self.assertEqual(set(documents), {name for pins in research.CLASSIFICATION_PINS.values() for name, _, _ in pins})
        for pins in research.CLASSIFICATION_PINS.values():
            for name, size, hash_value in pins:
                row = documents[name]
                self.assertEqual((size, hash_value), (row['bytes'], row['sha256']))
                self.assertEqual(row['sourceURL'], research._source_url(name))


if __name__ == '__main__':
    unittest.main()
