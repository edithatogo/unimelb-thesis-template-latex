"""Independent, synthetic contracts for opt-in scientific authoring."""

import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import verify_science


class ScientificFixtureContract(unittest.TestCase):
    def test_complete_rendered_document_is_accepted(self):
        text = "\n".join(verify_science.REQUIRED_TEXT)
        self.assertEqual(verify_science.validate_science_text(text), len(text.split()))

    def test_each_required_feature_must_be_visible(self):
        for required in verify_science.REQUIRED_TEXT:
            with self.subTest(feature=required):
                text = "\n".join(s for s in verify_science.REQUIRED_TEXT if s != required)
                with self.assertRaisesRegex(verify_science.VerificationError, "missing"):
                    verify_science.validate_science_text(text)

    def test_empty_extracted_text_is_rejected(self):
        with self.assertRaisesRegex(verify_science.VerificationError, "empty"):
            verify_science.validate_science_text("\t \n")

    def test_pdf_build_uses_no_shell_escape(self):
        command = verify_science.build_command("/tmp/a", "examples/science-demo.tex")
        self.assertIn("-no-shell-escape", command)
        self.assertNotIn("-shell-escape", command)
        self.assertIn("-halt-on-error", command)



class ScientificBuildContract(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.text = "\n".join(verify_science.REQUIRED_TEXT)
        self.info = "Title: Science\nPages: 1\n"
        self.log = "This is LuaHBTeX.\nOutput written on science-demo.pdf.\n"
        self.emit_pdf = True

    def fake_command(self, command, **kwargs):
        self.calls.append(command[0])
        if command[0] == "lualatex":
            output_flag = next(arg for arg in command if arg.startswith("-output-directory="))
            output = Path(output_flag.split("=", 1)[1])
            if self.emit_pdf:
                (output / "science-demo.pdf").write_bytes(b"%PDF-1.7 synthetic fixture")
            (output / "science-demo.log").write_text(self.log, encoding="utf-8")
            return ""
        if command[0] == "pdfinfo":
            return self.info
        if command[0] == "pdftotext":
            return self.text
        if command[0] == "qpdf":
            return ""
        raise AssertionError(f"Unexpected command: {command}")

    def check(self):
        with patch.object(verify_science, "run_command", side_effect=self.fake_command):
            return verify_science.verify_science(Path.cwd())

    def test_fresh_build_validates_actual_pdf_and_rendered_text(self):
        result = self.check()
        self.assertEqual(result["pages"], 1)
        self.assertGreater(result["words"], 10)
        self.assertEqual(self.calls, ["lualatex", "qpdf", "pdfinfo", "pdftotext"])

    def test_compiler_cannot_succeed_without_pdf(self):
        self.emit_pdf = False
        with self.assertRaisesRegex(verify_science.VerificationError, "science-demo.pdf"):
            self.check()

    def test_invalid_pdf_page_count_is_rejected(self):
        self.info = "Pages: 0\n"
        with self.assertRaisesRegex(verify_science.VerificationError, "invalid PDF page count"):
            self.check()

    def test_invalid_rendered_content_is_rejected(self):
        self.text = "Scientific authoring fixture"
        with self.assertRaisesRegex(verify_science.VerificationError, "missing rendered features"):
            self.check()

    def test_unresolved_final_log_is_rejected(self):
        self.log = "LaTeX Warning: Citation 'missing' on page 1 undefined on input line 9.\n"
        with self.assertRaises(verify_science.VerificationError):
            self.check()

if __name__ == "__main__":
    unittest.main()
