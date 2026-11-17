"""Deterministic source inventory for tagging-readiness, never PDF/UA proof."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts import tagging_inventory as ti

class InventoryTests(unittest.TestCase):
    def test_extracts_comma_packages_and_options_but_not_comments(self):
        source = (r'\RequirePackage[backend=biber,style=numeric]{biblatex}'+'\n'
                  '% \\usepackage{obsolete}'+'\n'
                  '\\usepackage{caption,subcaption,amsmath}'+'\n'
                  '\\RequirePackage{tikz}'+'\n')
        self.assertEqual(ti.extract_packages(source),{'biblatex','caption','subcaption','amsmath','tikz'})

    def test_unknown_package_is_explicitly_unqualified(self):
        result=ti.report({'unknown-pack'},set())
        self.assertIn('unknown-pack',result['unreviewed'])
        self.assertFalse(result['pdf_ua_qualified'])

    def test_known_incompatibilities_are_preserved_as_blockers(self):
        result=ti.report({'caption','biblatex','glossaries'},{'algorithm2e','pgfplots','pdfpages'})
        self.assertEqual(set(result['incompatible']),{'caption','algorithm2e','pgfplots','pdfpages'})
        self.assertIn('biblatex',result['conditional'])
        self.assertIn('glossaries',result['unreviewed'])
        self.assertFalse(result['pdf_ua_qualified'])

    def test_missing_and_symlinked_source_are_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaises(ti.InventoryError):ti.inventory(root/'missing.tex',root/'missing.sty')
            a=root/'base.tex';a.write_text('\\usepackage{caption}')
            b=root/'extra.sty';b.symlink_to(a)
            with self.assertRaises(ti.InventoryError):ti.inventory(a,b)

    def test_ambiguous_unclosed_package_import_is_rejected(self):
        with self.assertRaisesRegex(ti.InventoryError,'Unparseable'):
            ti.extract_packages(r'\usepackage{caption')

    def test_no_active_package_commands_fails_closed(self):
        with self.assertRaises(ti.InventoryError):ti.report(set(),set())

    def test_result_is_json_and_never_conformance_certificate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=root/'main.cls';b=root/'science.sty'
            a.write_text('\\usepackage{caption,biblatex}')
            b.write_text('\\RequirePackage[ruled]{algorithm2e}')
            result=ti.inventory(a,b)
            loaded=json.loads(json.dumps(result))
            self.assertEqual(loaded['status'],'tagging-unqualified')
            self.assertFalse(loaded['pdf_ua_qualified'])
            self.assertEqual(loaded['source_type'],'mutable-upstream-status-list')
            self.assertEqual(loaded['direct_package_count'],3)

if __name__=='__main__':unittest.main()
