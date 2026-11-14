"""Behavioral checks for verification failures, using synthetic compiler/PDF output."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts import verify


GOOD_LOG = "This is LuaHBTeX.\nOutput written on Thesis.pdf (12 pages, 2048 bytes).\n"
GOOD_TEXT = "\n".join(verify.REQUIRED_SECTIONS) + """
A synthetic thesis example.
The TeXbook
A document preparation system
Vivamus at pulvinar nisi.
"""


GOOD_FONTS = (
    "name                                 type              encoding         emb sub uni object ID\n"
    "------------------------------------ ----------------- ---------------- --- --- --- ---------\n"
    "AAAAAA+Example-Regular               CID Type 0C       Identity-H       yes yes yes     13  0\n"
    "AAAAAB+Example-Bold                  Type 1            Custom           yes yes no      24  0\n"
)


def write_outputs(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "Thesis.pdf").write_bytes(b"%PDF-1.7\nsynthetic test input\n")
    (directory / "Thesis.log").write_text(GOOD_LOG, encoding="utf-8")
    (directory / "Thesis.bbl").write_text(r"\entry{fixture}{book}{}", encoding="utf-8")
    (directory / "Thesis.gls").write_text(r"\glossentry{fixture}{}", encoding="utf-8")
    (directory / "Thesis.blg").write_text("INFO - Output to Thesis.bbl", encoding="utf-8")


class OutputChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "outputs"
        write_outputs(self.output)
        self.env = {"SOURCE_DATE_EPOCH": verify.DEFAULT_SOURCE_DATE_EPOCH}
        self.pdfinfo = "Title: Synthetic thesis\nPages: 12\n"
        self.text = GOOD_TEXT
        self.fonts = GOOD_FONTS
        self.commands = []

    def fake_command(self, command, **kwargs):
        self.commands.append((command, kwargs))
        if command[0] == "pdfinfo":
            return self.pdfinfo
        if command[0] == "pdftotext":
            return self.text
        if command[0] == "pdffonts":
            return self.fonts
        return ""

    def check(self):
        with patch.object(verify, "run_command", side_effect=self.fake_command):
            return verify.validate_outputs(self.output, self.root, self.env)

    def test_complete_output_passes_pdf_tools_and_reports_evidence(self):
        report = self.check()
        self.assertEqual(report["page_count"], 12)
        self.assertEqual(report["embedded_font_count"], 2)
        self.assertEqual(len(report["normalized_text_sha256"]), 64)
        self.assertEqual([command[0] for command, _ in self.commands], ["qpdf", "pdfinfo", "pdffonts", "pdftotext"])
        self.assertTrue(all(options["timeout"] == 30 for _, options in self.commands))
        self.assertEqual(
            [options.get("reject_stderr", False) for _, options in self.commands],
            [False, True, True, True],
        )


    def test_font_inventory_requires_all_fonts_embedded(self):
        self.fonts = GOOD_FONTS.replace("yes yes no", "no  no  no ")
        with self.assertRaisesRegex(verify.VerificationError, "not embedded"):
            self.check()

    def test_font_inventory_must_not_be_empty_or_malformed(self):
        for report in (
            GOOD_FONTS.splitlines()[0] + "\n" + GOOD_FONTS.splitlines()[1],
            GOOD_FONTS + "malformed\n",
            "Unexpected output\n",
        ):
            with self.subTest(report=report):
                self.fonts = report
                with self.assertRaisesRegex(verify.VerificationError, "font"):
                    self.check()

    def test_missing_or_empty_required_outputs_fail(self):
        for filename in ("Thesis.pdf", "Thesis.log", "Thesis.bbl", "Thesis.gls"):
            for state in ("missing", "empty"):
                with self.subTest(filename=filename, state=state):
                    write_outputs(self.output)
                    path = self.output / filename
                    if state == "missing":
                        path.unlink()
                    else:
                        path.write_bytes(b"")
                    with self.assertRaisesRegex(verify.VerificationError, filename):
                        self.check()

    def test_bibliography_and_glossary_must_have_entries(self):
        for filename in ("Thesis.bbl", "Thesis.gls"):
            with self.subTest(filename=filename):
                write_outputs(self.output)
                (self.output / filename).write_text("A generated header without entries", encoding="utf-8")
                with self.assertRaisesRegex(verify.VerificationError, "No generated entries"):
                    self.check()

    def test_hard_log_errors_are_rejected(self):
        cases = (
            "LaTeX Warning: Citation 'missing' on page 1 undefined on input line 2.",
            "LaTeX Warning: Reference " + chr(96) + "missing' on page 1 undefined on input line 2.",
            "LaTeX Warning: Citation 'a-very-long-name' on page 1\n undefined on input line 2.",
            "LaTeX Warning: There were undefined references.",
            "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.",
            "LaTeX Warning: There were multiply-defined labels.",
            "Package biblatex Warning: Please (re)run Biber on the file:",
            "Package biblatex Warning: Please rerun LaTeX.",
            "Package rerunfilecheck Warning: Rerun to get outlines right.",
            "! Undefined control sequence.",
            "./example/Thesis.tex:31: LaTeX Error: Missing begin document.",
            "Package example Error: malformed input.",
            "! Emergency stop.",
            "Fatal error occurred, no output PDF file produced!",
            "Package biblatex Warning: Empty bibliography on input line 44.",
            "No file Thesis.gls.",
            "No file Thesis.bbl.",
        )
        for failure in cases:
            with self.subTest(failure=failure):
                (self.output / "Thesis.log").write_text(GOOD_LOG + failure, encoding="utf-8")
                with self.assertRaisesRegex(verify.VerificationError, "Final LaTeX log"):
                    self.check()

    def test_nonfatal_typography_warning_is_not_an_unresolved_reference(self):
        (self.output / "Thesis.log").write_text(GOOD_LOG + "Overfull \\hbox (2.0pt too wide)\n", encoding="utf-8")
        self.check()

    def test_invalid_pdf_or_pdf_tool_failure_is_not_accepted(self):
        with patch.object(verify, "run_command", side_effect=verify.VerificationError("qpdf exited with status 2")):
            with self.assertRaisesRegex(verify.VerificationError, "qpdf"):
                verify.validate_outputs(self.output, self.root, self.env)

    def test_page_count_must_be_present_and_positive(self):
        for info in ("Pages: 0\n", "Pages: -1\n", "Pages: unknown\n", "Title: No pages\n"):
            with self.subTest(info=info):
                self.pdfinfo = info
                with self.assertRaisesRegex(verify.VerificationError, "positive page count"):
                    self.check()

    def test_empty_extracted_text_fails(self):
        self.text = " \n\t\f "
        with self.assertRaisesRegex(verify.VerificationError, "no extractable text"):
            self.check()

    def test_each_expected_section_is_required(self):
        for section in verify.REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.text = GOOD_TEXT.replace(section, "")
                with self.assertRaisesRegex(verify.VerificationError, "missing expected sections"):
                    self.check()

    def test_generated_files_and_headings_cannot_replace_rendered_content(self):
        cases = (
            ("Bibliography", "The TeXbook"),
            ("Glossary", "A document preparation system"),
            ("An Appendix", "Vivamus at pulvinar nisi."),
        )
        for heading, content in cases:
            with self.subTest(content=content):
                self.text = GOOD_TEXT.replace(content, "")
                self.assertIn(heading, self.text)
                with self.assertRaisesRegex(verify.VerificationError, "missing expected content"):
                    self.check()

    def test_build_output_symlinks_are_rejected(self):
        (self.output / "Thesis.pdf").unlink()
        (self.output / "Thesis.pdf").symlink_to(self.output / "Thesis.log")
        with self.assertRaisesRegex(verify.VerificationError, "non-regular"):
            self.check()


class ExternalCommandChecks(unittest.TestCase):
    def call(self, program, *arguments, timeout=5, reject_stderr=False):
        return verify.run_command(
            [sys.executable, "-c", program, *arguments],
            cwd=Path("."), env=os.environ.copy(), timeout=timeout,
            reject_stderr=reject_stderr,
        )

    def test_success_status_with_pdf_warning_on_stderr_is_rejected(self):
        warning = "Syntax Warning: Annotation destination array is too short"
        with self.assertRaisesRegex(verify.VerificationError, "diagnostic output on stderr") as caught:
            self.call(
                "import sys; print('Pages: 12'); print(sys.argv[1], file=sys.stderr)",
                warning, reject_stderr=True,
            )
        self.assertIn(warning, str(caught.exception))
        self.assertIn("Pages: 12", str(caught.exception))

    def test_strict_command_accepts_success_and_blank_stderr(self):
        output = self.call(
            "import sys; print('Pages: 12'); print('  ', file=sys.stderr)",
            reject_stderr=True,
        )
        self.assertEqual(output, "Pages: 12\n")

    def test_ordinary_command_may_emit_nonfatal_stderr(self):
        output = self.call("import sys; print('compiled'); print('typography warning', file=sys.stderr)")
        self.assertEqual(output, "compiled\n")

    def test_nonzero_status_retains_actual_stdout_and_stderr(self):
        with self.assertRaises(verify.VerificationError) as caught:
            self.call("import sys; print('synthetic compiler context'); print('synthetic compile error', file=sys.stderr); sys.exit(3)")
        self.assertIn("status 3", str(caught.exception))
        self.assertIn("synthetic compiler context", str(caught.exception))
        self.assertIn("synthetic compile error", str(caught.exception))

    def test_diagnostic_output_is_bounded_and_preserves_tail(self):
        with self.assertRaises(verify.VerificationError) as caught:
            self.call("import sys; print('x' * 10000); print('final diagnostic', file=sys.stderr); sys.exit(1)")
        self.assertIn("final diagnostic", str(caught.exception))
        self.assertLess(len(str(caught.exception)), verify.DIAGNOSTIC_LIMIT + 300)

    def test_missing_tool_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(verify.VerificationError, "Required command not found"):
                verify.run_command([str(Path(directory) / "missing-tool")], cwd=Path(directory), env={}, timeout=5)

    def test_commands_keep_literal_arguments_without_shell_expansion(self):
        arguments = ["a file.pdf", "$(not-executed)", "semicolon;argument"]
        output = self.call("import json, sys; print(json.dumps(sys.argv[1:]))", *arguments)
        self.assertEqual(json.loads(output), arguments)

    @unittest.skipUnless(os.name == "posix", "POSIX process-group cleanup is only guaranteed on POSIX")
    def test_actual_timeout_stops_compiler_child_and_retains_diagnostic(self):
        program = """
import subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'])
Path(sys.argv[1]).write_text(str(child.pid))
print('synthetic compiler started', flush=True)
time.sleep(10)
"""
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "child.pid"
            started = time.monotonic()
            child_pid = None
            try:
                with self.assertRaisesRegex(verify.VerificationError, "timed out after 1 seconds") as caught:
                    self.call(program, str(pid_file), timeout=1)
                self.assertLess(time.monotonic() - started, 5)
                self.assertIn("synthetic compiler started", str(caught.exception))
                child_pid = int(pid_file.read_text())
                # A killed orphan can briefly remain a zombie until the runner's init reaps it.
                def child_is_running():
                    if sys.platform.startswith("linux"):
                        try:
                            state = Path(f"/proc/{child_pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
                        except FileNotFoundError:
                            return False
                        return state not in ("Z", "X")
                    status = subprocess.run(
                        ["ps", "-o", "stat=", "-p", str(child_pid)],
                        capture_output=True, text=True, timeout=2, check=False,
                    )
                    return status.returncode == 0 and bool(status.stdout.strip()) and not status.stdout.strip().startswith("Z")
                for _ in range(20):
                    if not child_is_running():
                        break
                    time.sleep(0.05)
                self.assertFalse(child_is_running(), "compiler child survived the verification timeout")
            finally:
                if child_pid is None and pid_file.exists():
                    child_pid = int(pid_file.read_text())
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


class BuildAndReplayChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.builds = []
        self.texts = [GOOD_TEXT, GOOD_TEXT]
        self.command_failure = None

    def fake_command(self, command, **kwargs):
        if command[0] == "latexmk":
            output = Path(next(argument.removeprefix("-outdir=") for argument in command if argument.startswith("-outdir=")))
            self.builds.append((output, command, kwargs))
            (output / "Thesis.log").write_text(GOOD_LOG, encoding="utf-8")
            if self.command_failure:
                raise self.command_failure
            write_outputs(output)
            (output / "unrelated-private.txt").write_text("must not be retained", encoding="utf-8")
        elif command[0] == "pdfinfo":
            return "Pages: 12\n"
        elif command[0] == "pdffonts":
            return GOOD_FONTS
        elif command[0] == "pdftotext":
            return self.texts[len(self.builds) - 1]
        return ""

    def run_verification(self, replay=False):
        with patch.object(verify, "run_command", side_effect=self.fake_command):
            return verify.verify(self.root, replay=replay)

    def test_clean_build_retains_only_allowlisted_outputs_and_success_report(self):
        result = self.run_verification()
        evidence = self.root / "build" / "verification"
        self.assertEqual(result["status"], "passed")
        self.assertEqual(set(path.name for path in evidence.iterdir()), set(verify.ARTIFACT_NAMES) | {"report.json"})
        self.assertEqual(json.loads((evidence / "report.json").read_text())["status"], "passed")
        output, command, options = self.builds[0]
        self.assertNotEqual(output, evidence)
        self.assertFalse(output.exists())
        self.assertIn("-no-shell-escape", command)
        self.assertEqual(options["timeout"], 300)

    def test_failed_build_cannot_use_old_pdf_and_retains_failure_log(self):
        evidence = self.root / "build" / "verification"
        write_outputs(evidence)
        self.command_failure = verify.VerificationError("latexmk exited with status 12")
        with self.assertRaisesRegex(verify.VerificationError, "latexmk"):
            self.run_verification()
        self.assertFalse((evidence / "Thesis.pdf").exists())
        self.assertTrue((evidence / "Thesis.log").exists())
        self.assertEqual(json.loads((evidence / "report.json").read_text())["status"], "failed")

    def test_replay_uses_different_clean_directories_and_identical_fixed_environment(self):
        self.texts[1] = GOOD_TEXT.replace("\n", "\n\n\t")
        report = self.run_verification(replay=True)
        self.assertEqual(report["replay"]["status"], "passed")
        self.assertNotEqual(self.builds[0][0], self.builds[1][0])
        self.assertEqual(self.builds[0][2]["env"], self.builds[1][2]["env"])
        self.assertEqual(self.builds[0][2]["env"]["TZ"], "UTC")

    def test_replay_text_drift_fails_and_records_failure(self):
        self.texts[1] += "Different content"
        with self.assertRaisesRegex(verify.VerificationError, "changed normalized"):
            self.run_verification(replay=True)
        report = json.loads((self.root / "build" / "verification" / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["replay"]["status"], "failed")

    def test_replay_page_count_drift_fails(self):
        first = {"page_count": 12, "normalized_text_sha256": "same"}
        second = {"page_count": 13, "normalized_text_sha256": "same"}
        with self.assertRaisesRegex(verify.VerificationError, "page count"):
            verify.compare_replays(first, second)

    def test_invalid_source_date_epoch_fails(self):
        for epoch in ("-1", "tomorrow", ""):
            with self.subTest(epoch=epoch), patch.dict(verify.os.environ, {"SOURCE_DATE_EPOCH": epoch}):
                with self.assertRaisesRegex(verify.VerificationError, "SOURCE_DATE_EPOCH"):
                    self.run_verification()

    def test_invalid_epoch_clears_old_success_evidence_and_records_failure(self):
        evidence = self.root / "build" / "verification"
        write_outputs(evidence)
        (evidence / "report.json").write_text('{"status": "passed"}', encoding="utf-8")
        with patch.dict(verify.os.environ, {"SOURCE_DATE_EPOCH": "invalid"}):
            with self.assertRaisesRegex(verify.VerificationError, "SOURCE_DATE_EPOCH"):
                self.run_verification()
        self.assertFalse((evidence / "Thesis.pdf").exists())
        report = json.loads((evidence / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertIn("SOURCE_DATE_EPOCH", report["error"])
        self.assertEqual(report["retained_artifacts"], [])

    @unittest.skipUnless(os.name == "posix", "requires symlink creation")
    def test_symlinked_evidence_directories_never_delete_source(self):
        for relative in ("build", "build/verification", "build/replay"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                protected_source = root / "example"
                write_outputs(protected_source)
                (protected_source / "report.json").write_text('{"protected": true}', encoding="utf-8")
                expected = {path.name: path.read_bytes() for path in protected_source.iterdir()}
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(protected_source, target_is_directory=True)
                with self.assertRaisesRegex(verify.VerificationError, "symlinked evidence"):
                    verify.verify(root)
                self.assertEqual(
                    {path.name: path.read_bytes() for path in protected_source.iterdir()}, expected,
                )


if __name__ == "__main__":
    unittest.main()
