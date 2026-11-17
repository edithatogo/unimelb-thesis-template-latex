"""Contract-consumer boundary and synthetic PDF-profile tests (no network)."""
import hashlib
import json
from types import SimpleNamespace
import tempfile
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import contract_consumer as consumer


class ProvenanceTests(unittest.TestCase):
    def test_contract_pin_is_immutable_sha_and_manifest_digests(self):
        self.assertEqual(len(consumer.UPSTREAM_REVISION), 40)
        self.assertEqual(len(consumer.MANIFEST_SHA256), 64)
        self.assertEqual(len(consumer.FIXTURES_SHA256), 64)
        self.assertEqual(len(consumer.LIBRARY_SHA256), 64)

    def test_missing_or_tampered_contract_fails_closed_before_import(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'contracts/thesis/v1').mkdir(parents=True)
            (root / 'scripts').mkdir()
            (root / 'contracts/thesis/v1/manifest.json').write_text('{"contract_version":"1.0.0"}')
            (root / 'contracts/thesis/v1/fixtures.json').write_text('{}')
            (root / 'scripts/thesis_contract.py').write_text('pass')
            with patch.object(consumer, 'git_revision', return_value=consumer.UPSTREAM_REVISION):
                with self.assertRaisesRegex(consumer.QualificationError, 'digest'):
                    consumer.pinned_inputs(root)

    def test_wrong_revision_fails_before_loading_canonical_code(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(consumer, 'git_revision', return_value='0' * 40):
                with self.assertRaisesRegex(consumer.QualificationError, 'revision'):
                    consumer.pinned_inputs(Path(td))


class PdfProjectionTests(unittest.TestCase):
    def setUp(self):
        self.configuration = {
            'contract_version': '1.0.0', 'purpose': 'examination',
            'identity': 'identified', 'output': 'pdf', 'language': 'en',
            'pdf_standards': [],
            'metadata': {
                'title': 'Synthetic & safe # title',
                'author': {'student_record_name': 'Synthetic Student'},
                'degree': {'kind': 'doctoral', 'course': 'Doctor of Philosophy'},
                'academic_units': ['Synthetic School'],
                'submission': {'month': '2026-11'},
                'abstract': 'A synthetic summary.'
            }
        }

    def test_supported_fixture_projects_escaped_source_no_shell_escape(self):
        source = consumer.render_source(self.configuration)
        self.assertIn(r'\title{Synthetic \& safe \# title}', source)
        self.assertIn(r'\authors{Synthetic Student}', source)
        self.assertIn(r'\submissiondate{November 2026}', source)
        self.assertIn(r'\begin{abstract}', source)
        self.assertNotIn(r'\write18', source)
        args = consumer.latexmk_args('fixture.tex', 'out')
        self.assertIn('-no-shell-escape', args)
        self.assertIn('-halt-on-error', args)

    def test_unqualified_standards_and_blind_mode_cannot_render(self):
        for field, value in (
            ('pdf_standards', ['pdf/ua-2']), ('identity', 'blind-review'),
            ('output', 'html'), ('language', 'fr'),
        ):
            with self.subTest(field=field):
                cfg = {**self.configuration, field: value}
                with self.assertRaisesRegex(consumer.QualificationError, 'unsupported'):
                    consumer.render_source(cfg)

    def test_optional_rights_or_publication_cannot_be_silently_dropped(self):
        for field in ("rights", "publications", "creative_outputs"):
            with self.subTest(field=field):
                cfg = {**self.configuration, "metadata": {**self.configuration['metadata'], field: [{"id": "x"}]}}
                with self.assertRaisesRegex(consumer.QualificationError, 'unsupported'):
                    consumer.render_source(cfg)

    def test_untrusted_latex_commands_are_escaped_not_executed(self):
        self.configuration['metadata']['title'] = r"abc\write18{touch evil}"
        source = consumer.render_source(self.configuration)
        self.assertNotIn(r"\write18{touch evil}", source)
        self.assertIn(r"\textbackslash{}write18", source)

    def test_source_rejects_missing_metadata_even_if_draft(self):
        self.configuration['metadata']['title'] = ''
        with self.assertRaisesRegex(consumer.QualificationError, 'missing'):
            consumer.render_source(self.configuration)

    def test_rendered_content_must_match_observed_pdf_not_toc_only(self):
        page = 'Synthetic & safe # title\nSynthetic Student\nDoctor of Philosophy\nNovember 2026\nSynthetic School'
        info = 'Title: Synthetic & safe # title\nAuthor: Synthetic Student\nPages: 2\n'
        abstract = 'Abstract\nSynthetic & safe # title\nSynthetic Student\nA synthetic summary.'
        result = consumer.validate_rendered(info, page + '\f' + abstract + '\f', self.configuration)
        self.assertEqual(result['physical_pages'], 2)
        self.assertEqual(result['abstract_page'], 2)
        self.assertIn('title_page', result)
        with self.assertRaisesRegex(consumer.QualificationError, 'title'):
            consumer.validate_rendered(info, 'Contents\nSynthetic & safe # title\fSynthetic chapter', self.configuration)
        with self.assertRaisesRegex(consumer.QualificationError, 'metadata'):
            consumer.validate_rendered(info.replace('Synthetic Student', 'Wrong'), page, self.configuration)

    def test_abstract_omission_or_toc_entry_never_qualifies_abstract(self):
        page = 'Synthetic & safe # title\nSynthetic Student\nDoctor of Philosophy\nNovember 2026\nSynthetic School'
        info = 'Title: Synthetic & safe # title\nAuthor: Synthetic Student\nPages: 2\n'
        for second in (
            'Synthetic chapter with no abstract',
            'Contents\nAbstract 2\nA synthetic summary.',
            'Abstract\nSynthetic & safe # title\nSynthetic Student\nWrong abstract text',
            'Abstract\nSynthetic & safe # title\nA synthetic summary.',
        ):
            with self.subTest(second=second), self.assertRaisesRegex(consumer.QualificationError, 'abstract'):
                consumer.validate_rendered(info, page + '\f' + second + '\f', self.configuration)


class OutputSafetyTests(unittest.TestCase):
    def test_failure_clears_previous_success_and_emits_failure_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / 'build/contract/native.json'
            output.parent.mkdir(parents=True)
            output.write_text('{"status":"passed"}')
            with patch.object(consumer, 'ROOT', root):
                status = consumer.main(['--upstream', str(root / 'missing'), '--output', str(output)])
            self.assertEqual(status, 1)
            self.assertNotEqual(json.loads(output.read_text())['status'], 'passed')

    def test_output_parent_traversal_never_overwrites_existing_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / 'README.md'
            original.write_text('PRESERVE_THIS_SOURCE', encoding='utf-8')
            (root / 'build' / 'contract').mkdir(parents=True)
            malicious = root / 'build' / 'contract' / '..' / '..' / 'README.md'
            with patch.object(consumer, 'ROOT', root):
                with self.assertRaisesRegex(consumer.QualificationError, 'traversal|Output'):
                    consumer.prepare_output(malicious)
            self.assertEqual(original.read_text(encoding='utf-8'), 'PRESERVE_THIS_SOURCE')

    def test_main_rejects_parent_traversal_before_receipt_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / 'README.md'
            original.write_text('PRESERVE_THIS_SOURCE', encoding='utf-8')
            (root / 'build' / 'contract').mkdir(parents=True)
            malicious = root / 'build' / 'contract' / '..' / '..' / 'README.md'
            with patch.object(consumer, 'ROOT', root), self.assertRaisesRegex(consumer.QualificationError, 'traversal|Output'):
                consumer.main(['--upstream', str(root/'missing'), '--output', str(malicious)])
            self.assertEqual(original.read_text(encoding='utf-8'), 'PRESERVE_THIS_SOURCE')

    def test_symlinked_parent_cannot_redirect_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected = root / 'external'
            protected.mkdir()
            (root / 'build').symlink_to(protected, target_is_directory=True)
            with patch.object(consumer, 'ROOT', root):
                with self.assertRaisesRegex(consumer.QualificationError, 'symlink'):
                    consumer.prepare_output(root / 'build/contract/report.json')


class CanonicalFixtureTests(unittest.TestCase):
    def test_canonical_fixture_negative_and_positive_oracles_are_enforced(self):
        class Error(ValueError):
            def __init__(self, code):
                self.code = code
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture_path = root / 'fixture.json'
            data = {"id": "synthetic", "metadata": {"purpose": "draft"}, "cli": [], "explicit": {},
                    "expected": {"result": "valid", "diagnostic_codes": [], "values": {}}}
            fixture_path.write_text(json.dumps(data))
            bundle = SimpleNamespace(root=root, fixtures={"synthetic": {
                "path": "fixture.json", "sha256": consumer.digest(fixture_path)}})
            bundle.parse_cli = lambda _: {}
            bundle.normalize = lambda *args: {"configuration": {"purpose": "draft"}, "diagnostics": []}
            module = SimpleNamespace(read_json=lambda path: json.loads(path.read_text()), ContractError=Error)
            self.assertEqual(consumer.check_fixture(bundle, module, 'synthetic')['normalization'], 'executed-pass')
            data['expected']['values'] = {'purpose': 'examination'}
            fixture_path.write_text(json.dumps(data))
            bundle.fixtures['synthetic']['sha256'] = consumer.digest(fixture_path)
            with self.assertRaisesRegex(consumer.QualificationError, 'oracle'):
                consumer.check_fixture(bundle, module, 'synthetic')
            data['expected'] = {"result": "invalid", "diagnostic_codes": [], "values": {}, "error_code": "unknown-key"}
            fixture_path.write_text(json.dumps(data))
            bundle.fixtures['synthetic']['sha256'] = consumer.digest(fixture_path)
            def reject(*args): raise Error('unknown-key')
            bundle.normalize = reject
            self.assertEqual(consumer.check_fixture(bundle, module, 'synthetic')['normalization'], 'expected-invalid')
            data['expected']['error_code'] = 'invalid-date'
            fixture_path.write_text(json.dumps(data))
            bundle.fixtures['synthetic']['sha256'] = consumer.digest(fixture_path)
            with self.assertRaisesRegex(consumer.QualificationError, 'Unexpected negative'):
                consumer.check_fixture(bundle, module, 'synthetic')
            bundle.fixtures['synthetic']['sha256'] = '0' * 64
            with self.assertRaisesRegex(consumer.QualificationError, 'tampered'):
                consumer.check_fixture(bundle, module, 'synthetic')


class ExecutedPathTests(unittest.TestCase):
    def test_git_revision_reads_verified_external_checkout(self):
        good = SimpleNamespace(stdout=consumer.UPSTREAM_REVISION + '\n')
        with patch.object(consumer.subprocess, 'run', return_value=good):
            self.assertEqual(consumer.git_revision(Path('/tmp/pinned-upstream')), consumer.UPSTREAM_REVISION)
        with patch.object(consumer.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'git')):
            with self.assertRaisesRegex(consumer.QualificationError, 'checkout'):
                consumer.git_revision(Path('/tmp/pinned-upstream'))

    def test_real_output_verifier_boundary_and_checksum(self):
        config = {
            'contract_version': '1.0.0', 'identity': 'identified', 'output': 'pdf', 'language': 'en',
            'pdf_standards': [], 'metadata': {'title': 'Synthetic Thesis',
                'author': {'student_record_name': 'Example Scholar'},
                'degree': {'course': 'Doctor of Philosophy'},
                'academic_units': ['Synthetic School'],
                'submission': {'month': '2026-11'}, 'abstract': 'Synthetic summary.'},
        }
        observed = []
        def run(command, **kwargs):
            observed.append(command[0])
            if command[0] == 'latexmk':
                out = Path(next(x.split('=', 1)[1] for x in command if x.startswith('-outdir=')))
                (out / 'synthetic-contract.pdf').write_bytes(b'%PDF-1.7 synthetic fixture')
                (out / 'synthetic-contract.log').write_text('Output written on synthetic-contract.pdf')
                self.assertIn('-no-shell-escape', command)
            if command[0] == 'pdfinfo':
                return 'Title: Synthetic Thesis\nAuthor: Example Scholar\nPages: 3\n'
            if command[0] == 'pdftotext':
                return 'Synthetic Thesis\nExample Scholar\nDoctor of Philosophy\nNovember 2026\nSynthetic School\fAbstract\nSynthetic Thesis\nExample Scholar\nSynthetic summary.\fSynthetic text'
            return ''
        fake_verify = SimpleNamespace(run_command=run, validate_log=lambda text: None)
        with tempfile.TemporaryDirectory() as td, patch.dict(sys.modules, {'scripts.verify': fake_verify}):
            root = Path(td)
            (root / 'template').mkdir()
            result = consumer.run_render(root, config)
        self.assertEqual(observed, ['latexmk', 'qpdf', 'pdfinfo', 'pdftotext'])
        self.assertEqual(result['rendering'], 'executed-pass')
        self.assertEqual(len(result['pdf_sha256']), 64)
        self.assertEqual(result['physical_pages'], 3)

    def test_missing_pdf_cannot_be_replaced_by_old_receipt(self):
        config = {
            'contract_version': '1.0.0', 'metadata': {'title': 'Synthetic Thesis',
                'author': {'student_record_name': 'Example Scholar'},
                'degree': {'course': 'Doctor of Philosophy'},
                'academic_units': ['School'], 'submission': {'month': '2026-11'},
                'abstract': 'Summary'},
        }
        with tempfile.TemporaryDirectory() as td:
            def no_pdf(command, **_):
                if command[0] == 'latexmk':
                    out = Path(next(x.split('=',1)[1] for x in command if x.startswith('-outdir=')))
                    (out / 'synthetic-contract.log').write_text('Synthetic log')
                return ''
            with patch.dict(sys.modules, {'scripts.verify': SimpleNamespace(run_command=no_pdf, validate_log=lambda _: None)}):
                with self.assertRaisesRegex(consumer.QualificationError, 'Missing rendered'):
                    consumer.run_render(Path(td), config)

    def test_main_success_executes_all_fixture_cases_and_qualified_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'build').mkdir()
            bundle = SimpleNamespace(
                fixtures={'valid-case': {}, 'bad-case': {}},
                verify_fixtures=lambda: [{}, {}],
                manifest={'status':'candidate-schema-api'},
                digest=consumer.MANIFEST_SHA256,
            )
            def select(bundle, module, identifier):
                if identifier == 'bad-case':
                    return {'id':identifier, 'normalization':'expected-invalid','rendering':'not-applicable'}
                return {'id':identifier, 'normalization':'executed-pass', 'sha256':'a'*64,
                        'configuration': {'metadata': {'title':'Synthetic'}}}
            report_path=root / 'build/contract/report.json'
            with patch.object(consumer, 'ROOT', root), patch.object(consumer, 'load_canonical', return_value=(object(), bundle)), \
                 patch.object(consumer, 'check_fixture', side_effect=select), patch.object(consumer, 'run_render',return_value={'rendering':'executed-pass','pdf_sha256':'b'*64}), \
                 patch.object(consumer, 'git_revision', return_value=consumer.UPSTREAM_REVISION):
                status=consumer.main(['--upstream', str(root), '--render-fixture','valid-case', '--output',str(report_path)])
            self.assertEqual(status, 0)
            result=json.loads(report_path.read_text())
            self.assertEqual(result['status'],'passed')
            self.assertEqual(result['contract_status'], 'candidate-schema-api')
            self.assertEqual(len(result['input_cases']),2)
            self.assertEqual(result['full_contract_acceptance'], 'unexecuted')

    def test_main_rejects_incomplete_canonical_case_set(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            bundle=SimpleNamespace(fixtures={'one':{}}, verify_fixtures=lambda: [], manifest={}, digest=consumer.MANIFEST_SHA256)
            report=root / 'build/contract/report.json'
            with patch.object(consumer, 'ROOT',root), patch.object(consumer, 'load_canonical', return_value=(object(), bundle)), \
                 patch.object(consumer,'check_fixture', return_value={'id':'one','normalization':'executed-pass'}):
                self.assertEqual(consumer.main(['--upstream',str(root),'--output',str(report)]),1)
            self.assertEqual(json.loads(report.read_text())['status'],'failed')

    def test_invalid_month_and_unsupported_contract_versions_fail(self):
        with self.assertRaisesRegex(consumer.QualificationError, 'month'):
            consumer.month_label('2026-13')
        with self.assertRaisesRegex(consumer.QualificationError, 'contract'):
            consumer.render_source({'contract_version': '9.0.0'})



if __name__ == '__main__':
    unittest.main()
