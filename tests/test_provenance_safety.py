"""Negative CLI, JSON and filesystem checks using disposable synthetic paths."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts import provenance_manifest as m

class ProvenanceSafetyTests(unittest.TestCase):
    def test_duplicate_keys_and_malformed_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'report.json'
            for data in ('{"status":"passed","status":"failed"}', '{broken', ' '* (4*1024*1024+1)):
                path.write_text(data)
                with self.subTest(size=len(data)),self.assertRaises(m.ProvenanceError):
                    m.read_receipt(path)

    def test_output_path_traversal_and_symlink_parent_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'build/verification').mkdir(parents=True)
            protected=root/'README.md';protected.write_text('keep unchanged')
            path=root/'build/verification/../../README.md'
            with patch.object(m,'ROOT',root),self.assertRaisesRegex(m.ProvenanceError,'traversal'):
                m.validate_output_path(path)
            self.assertEqual(protected.read_text(),'keep unchanged')
            (root/'build/verification').rename(root/'other')
            (root/'build/verification').symlink_to(root/'other',target_is_directory=True)
            with patch.object(m,'ROOT',root),self.assertRaisesRegex(m.ProvenanceError,'symlink'):
                m.validate_output_path(root/'build/verification/provenance.json')

    def test_output_cannot_overwrite_pdf_or_verifier_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'build/verification').mkdir(parents=True)
            with patch.object(m,'ROOT',root):
                for name in ('Thesis.pdf','report.json','Thesis.log'):
                    with self.subTest(name=name),self.assertRaisesRegex(m.ProvenanceError,'provenance'):
                        m.validate_output_path(root/'build/verification'/name)

    def test_no_old_success_report_survives_failed_cli(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'build/verification/provenance.json'
            path.parent.mkdir(parents=True);path.write_text('{"status":"passed"}')
            with patch.object(m,'ROOT',root),patch('sys.stderr',new_callable=io.StringIO):
                self.assertEqual(m.main([]),1)
            self.assertEqual(json.loads(path.read_text())['status'],'failed')

    def test_external_commands_are_literal_and_fail_on_nonzero(self):
        output=m.run_command([sys.executable,'-c','print("synthetic")'],cwd=Path.cwd(),timeout=5)
        self.assertIn('synthetic',output)
        with self.assertRaisesRegex(m.ProvenanceError,'failed'):
            m.run_command([sys.executable,'-c','raise SystemExit(4)'],cwd=Path.cwd(),timeout=5)

if __name__=='__main__':unittest.main()
