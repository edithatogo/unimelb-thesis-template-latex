"""Independent, synthetic contracts for opt-in scientific authoring."""

import unittest
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


if __name__ == "__main__":
    unittest.main()
