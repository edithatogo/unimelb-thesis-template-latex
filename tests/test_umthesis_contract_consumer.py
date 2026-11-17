"""Synthetic, separately scoped LaTeX UMTHESIS normalized-data consumer tests.

The canonical Typst-side schema remains authoritative; this boundary does not
perform policy approvals or validate final PDFs.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import umthesis_contract_consumer as adapter


def normalized():
    return {
        "contract_version": "1.0.0",
        "purpose": "examination",
        "layout": "default",
        "double_sided": False,
        "identity": "identified",
        "output": "pdf",
        "pdf_standards": [],
        "language": "en",
        "label_locale": "en",
        "bibliography": {"mode": "unified", "style": "apa"},
        "metadata": {
            "title": "Illustrative synthetic research",
            "author": {"student_record_name": "Synthetic Student", "orcid": "0000-0000-0000-0001"},
            "degree": {"kind": "doctoral", "course": "Doctor of Philosophy"},
            "academic_units": ["Synthetic School"],
            "submission": {"month": "2026-11"},
            "abstract": "Synthetic abstract for configuration validation only.",
            "declarations": {"original_work": True, "word_count": 1200},
        },
        "approval_refs": {},
    }


def envelope(configuration=None):
    configuration = normalized() if configuration is None else configuration
    return {
        "contract_version": "1.0.0",
        "contract_sha256": adapter.CANONICAL_MANIFEST_SHA256,
        "configuration": configuration,
        "configuration_sha256": adapter.canonical_digest(configuration),
        "diagnostics": [],
    }


class UmthesisLatexConsumerTests(unittest.TestCase):
    def test_valid_canonical_envelope_produces_bounded_tex_and_receipt(self):
        tex, report = adapter.prepare(envelope())
        self.assertEqual(report["status"], "source-only-not-rendered")
        self.assertEqual(report["contract_version"], "1.0.0")
        self.assertEqual(report["contract_sha256"], adapter.CANONICAL_MANIFEST_SHA256)
        self.assertFalse(report["university_approved"])
        self.assertEqual(report["supported_configuration"], True)
        self.assertIn(r"\title{Illustrative synthetic research}", tex)
        self.assertIn(r"\authors{Synthetic Student}", tex)
        self.assertIn(r"\degree{Doctor of Philosophy}", tex)
        self.assertIn(r"\submissiondate{November 2026}", tex)
        self.assertIn(r"\school{Synthetic School}", tex)
        self.assertIn(r"\orcid{0000-0000-0000-0001}", tex)
        self.assertNotIn("Synthetic abstract", tex)
        self.assertEqual(report["tex_sha256"], hashlib.sha256(tex.encode()).hexdigest())
        self.assertEqual(report["observed_rendered_order"], "unexecuted")

    def test_missing_draft_metadata_has_draft_placeholders_not_fabricated_identity(self):
        config = normalized()
        config["purpose"] = "draft"
        config["metadata"] = {}
        tex, report = adapter.prepare(envelope(config))
        self.assertIn(r"\title{[Draft title not supplied]}", tex)
        self.assertIn(r"\authors{[Draft author not supplied]}", tex)
        self.assertIn(r"\submissiondate{[Draft month not supplied]}", tex)
        self.assertTrue(report["requires_author_review"])

    def test_final_missing_metadata_fails_without_an_output(self):
        config = normalized()
        del config["metadata"]["author"]
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(envelope(config))

    def test_invalid_month_fails_even_with_self_consistent_checksum(self):
        config = normalized()
        config["metadata"]["submission"]["month"] = "2026-13"
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(envelope(config))

    def test_teX_specials_cannot_become_commands(self):
        config = normalized()
        config["metadata"]["title"] = 'A \\\\input{secrets.tex} % # $ & _ ~ ^ } {'
        tex, _ = adapter.prepare(envelope(config))
        self.assertNotIn(r"\input{secrets.tex}", tex)
        self.assertIn(r"\textbackslash{}", tex)
        self.assertIn(r"\%", tex)
        self.assertIn(r"\#", tex)
        self.assertIn(r"\{", tex)

    def test_config_digest_and_canonical_pin_must_match_exactly(self):
        raw = envelope()
        for mutation in (
            dict(raw, contract_sha256="0" * 64),
            dict(raw, configuration_sha256="f" * 64),
            dict(raw, contract_version="2.0.0"),
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(adapter.ConsumerError):
                    adapter.prepare(mutation)
        raw["configuration"]["double_sided"] = 0
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(raw)

    def test_unsupported_identifiers_profiles_and_matter_are_not_silent_success(self):
        for key, value in (("identity", "blind-review"), ("purpose", "deposit-public"),
                           ("output", "experimental-html"), ("language", "fr"),
                           ("layout", "print"), ("double_sided", True)):
            config = normalized()
            config[key] = value
            with self.subTest(field=key), self.assertRaises(adapter.UnsupportedConfiguration):
                adapter.prepare(envelope(config))
        config = normalized()
        config["metadata"]["publications"] = [{"id": "paper1"}]
        with self.assertRaises(adapter.UnsupportedConfiguration):
            adapter.prepare(envelope(config))

    def test_optional_false_does_not_coerce_to_string_or_true(self):
        config = normalized()
        config["metadata"]["declarations"]["original_work"] = False
        with self.assertRaises(adapter.UnsupportedConfiguration):
            adapter.prepare(envelope(config))
        config["metadata"]["declarations"]["original_work"] = "false"
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(envelope(config))

    def test_reject_unknown_keys_and_malformed_envelopes(self):
        raw = envelope()
        raw["unknown"] = True
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(raw)
        raw = envelope()
        raw["configuration"]["extra"] = 17
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare(raw)
        with self.assertRaises(adapter.ConsumerError):
            adapter.prepare({"configuration": {}})

    def test_cli_does_not_create_partial_output_for_invalid_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = envelope()
            bad["contract_sha256"] = "0" * 64
            path = root / "in.json"
            path.write_text(json.dumps(bad))
            out = root / "fragment.tex"
            receipt = root / "receipt.json"
            cmd = [sys.executable, "-m", "scripts.umthesis_contract_consumer",
                   "--input", str(path), "--output", str(out), "--report", str(receipt)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out.exists())
            self.assertFalse(receipt.exists())
            self.assertNotIn("Synthetic Student", result.stderr)

    def test_cli_creates_consumer_output_but_no_institutional_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "in.json"
            path.write_text(json.dumps(envelope()))
            out = root / "fragment.tex"
            receipt = root / "receipt.json"
            cmd = [sys.executable, "-m", "scripts.umthesis_contract_consumer",
                   "--input", str(path), "--output", str(out), "--report", str(receipt)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(receipt.read_text())["status"], "source-only-not-rendered")
            self.assertNotIn("Synthetic Student", result.stdout)
            self.assertIn(r"\authors{Synthetic Student}", out.read_text())


if __name__ == "__main__":
    unittest.main()
