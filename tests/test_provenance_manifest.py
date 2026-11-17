"""Behavioral checks for the verified build provenance boundary (synthetic)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import provenance_manifest as m

FONTS=("name  type  encoding  emb sub uni object ID\n"
       "----  ----  --------  --- --- --- ---------\n"
       "FOO+Regular Type1 Standard yes yes yes 1 0\n"
       "BAR+Bold Type1 Standard yes yes yes 2 0\n")

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.root=Path(d.name)
        for path in m.SOURCE_FILES:
            f=self.root/path; f.parent.mkdir(parents=True,exist_ok=True); f.write_text('synthetic source')
        self.folder=self.root/'build/verification'; self.folder.mkdir(parents=True)
        self.pdf=self.folder/'Thesis.pdf'; self.pdf.write_bytes(b'%PDF-1.7 synthetic data')
        self.receipt={'schema_version':1,'status':'passed','pdf_sha256':hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
          'pdf_bytes':self.pdf.stat().st_size,'page_count':2,'embedded_font_count':2,
          'normalized_text_sha256':'a'*64,'source_date_epoch':'1735689600'}
        self.save()

    def save(self): (self.folder/'report.json').write_text(json.dumps(self.receipt))

    def fake_command(self,args,*,cwd,timeout):
        if args[0]=='pdffonts': return FONTS
        if args[0]=='git':return 'f'*40 if 'rev-parse' in args else ''
        return args[0]+' version 1.0'

    def create(self):
        with patch.object(m,'run_command',side_effect=self.fake_command):return m.create_manifest(self.root)

    def test_provenance_is_evidence_not_reproducibility(self):
        result=self.create()
        self.assertEqual(result['pdf']['sha256'],self.receipt['pdf_sha256'])
        self.assertEqual(result['font_inventory']['count'],2)
        self.assertEqual(set(result['sources']),set(m.SOURCE_FILES))
        self.assertEqual(set(result['tool_versions']),set(m.VERSION_TOOLS))
        self.assertFalse(result['cross_environment_reproducible'])
        self.assertFalse(result['institutional_acceptance'])

    def test_stale_or_tampered_pdf_cannot_pass(self):
        self.pdf.write_bytes(b'%PDF-1.7 changed')
        with self.assertRaisesRegex(m.ProvenanceError,'PDF'):self.create()

    def test_failed_receipt_is_rejected(self):
        self.receipt['status']='failed';self.save()
        with self.assertRaises(m.ProvenanceError):self.create()

    def test_absent_source_and_symlink_are_rejected(self):
        path=self.root/m.SOURCE_FILES[0];path.unlink()
        with self.assertRaises(m.ProvenanceError):self.create()
        path.symlink_to(self.pdf)
        with self.assertRaises(m.ProvenanceError):self.create()

    def test_font_inventory_must_agree_with_verifier(self):
        self.receipt['embedded_font_count']=5;self.save()
        with self.assertRaisesRegex(m.ProvenanceError,'font'):self.create()

    def test_missing_epoch_blocks_provenance(self):
        self.receipt['source_date_epoch']='not-a-date';self.save()
        with self.assertRaisesRegex(m.ProvenanceError,'SOURCE_DATE_EPOCH'):self.create()

if __name__=='__main__':unittest.main()
