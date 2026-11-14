"""Behavioral tests for the standalone CodeQL completion and findings gate."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import check_codeql


COMPLETE = {
    "version": "2.1.0",
    "runs": [{"tool": {"driver": {"name": "CodeQL"}}, "results": []}],
}


class ReportChecks(unittest.TestCase):
    def setUp(self):
        self.report = copy.deepcopy(COMPLETE)
        self.run = self.report["runs"][0]

    def test_zero_results_without_optional_metadata_or_invocations_pass(self):
        self.assertEqual(check_codeql.validate_report(self.report), 1)

    def test_optional_successful_invocations_and_metadata_pass(self):
        self.run["tool"]["driver"]["name"] = "CodeQL command-line toolchain"
        self.run["invocations"] = [{"executionSuccessful": True}]
        self.run["automationDetails"] = {"id": "/language:python"}
        self.assertEqual(check_codeql.validate_report(self.report), 1)
        self.run["invocations"] = []
        self.assertEqual(check_codeql.validate_report(self.report), 1)

    def test_any_finding_fails_even_if_low_severity_suppressed_or_unchanged(self):
        for finding in (
            {"message": {"text": "Synthetic finding"}},
            {"level": "note", "message": {"text": "Synthetic note"}},
            {"suppressions": [{"kind": "inSource"}], "message": {"text": "Suppressed"}},
            {"baselineState": "unchanged", "message": {"text": "Existing"}},
        ):
            with self.subTest(finding=finding):
                self.run["results"] = [finding]
                with self.assertRaisesRegex(check_codeql.SarifError, "1 finding"):
                    check_codeql.validate_report(self.report)

    def test_a_later_run_cannot_hide_findings(self):
        second = copy.deepcopy(self.run)
        second["results"] = [{"message": {"text": "Later finding"}}]
        self.report["runs"].append(second)
        with self.assertRaisesRegex(check_codeql.SarifError, "finding"):
            check_codeql.validate_report(self.report)

    def test_missing_malformed_or_empty_run_collection_fails(self):
        for document in (None, [], {}, {"version": "2.0.0", "runs": [self.run]},
                         {"version": "2.1.0", "runs": None},
                         {"version": "2.1.0", "runs": []},
                         {"version": "2.1.0", "runs": [None]}):
            with self.subTest(document=document), self.assertRaises(check_codeql.SarifError):
                check_codeql.validate_report(document)

    def test_missing_tool_driver_or_name_fails(self):
        for tool in (None, {}, {"driver": None}, {"driver": {}},
                     {"driver": {"name": ""}}, {"driver": {"name": 42}}):
            with self.subTest(tool=tool), self.assertRaises(check_codeql.SarifError):
                self.run["tool"] = tool
                check_codeql.validate_report(self.report)

    def test_missing_null_or_malformed_results_are_incomplete(self):
        del self.run["results"]
        with self.assertRaisesRegex(check_codeql.SarifError, "results"):
            check_codeql.validate_report(self.report)
        for results in (None, {}, "", False):
            with self.subTest(results=results), self.assertRaisesRegex(check_codeql.SarifError, "results"):
                self.run["results"] = results
                check_codeql.validate_report(self.report)

    def test_unsuccessful_incomplete_or_malformed_invocations_fail(self):
        for invocations in (None, {}, [None], [{}], [{"executionSuccessful": False}],
                            [{"executionSuccessful": "true"}], [{"executionSuccessful": 1}]):
            with self.subTest(invocations=invocations), self.assertRaises(check_codeql.SarifError):
                self.run["invocations"] = invocations
                check_codeql.validate_report(self.report)

    def test_error_notifications_fail_despite_success_flag_and_empty_results(self):
        for field in ("toolExecutionNotifications", "toolConfigurationNotifications"):
            with self.subTest(field=field), self.assertRaisesRegex(check_codeql.SarifError, "analysis error"):
                self.run["invocations"] = [{"executionSuccessful": True, field: [
                    {"level": "error", "message": {"text": "Synthetic extraction failure"}},
                ]}]
                check_codeql.validate_report(self.report)

    def test_non_error_diagnostics_are_not_findings(self):
        for level in ("none", "note", "warning"):
            with self.subTest(level=level):
                self.run["invocations"] = [{"executionSuccessful": True, "toolExecutionNotifications": [
                    {"level": level, "message": {"text": "Synthetic diagnostic"}},
                ]}]
                self.assertEqual(check_codeql.validate_report(self.report), 1)

    def test_malformed_notifications_fail(self):
        for notifications in (None, {}, [None], [{"level": "unknown"}]):
            with self.subTest(notifications=notifications), self.assertRaises(check_codeql.SarifError):
                self.run["invocations"] = [{"executionSuccessful": True,
                                            "toolExecutionNotifications": notifications}]
                check_codeql.validate_report(self.report)

    def test_external_results_or_invocations_cannot_be_accepted_as_empty(self):
        for field in ("results", "invocations"):
            with self.subTest(field=field), self.assertRaisesRegex(check_codeql.SarifError, "External"):
                self.run["externalPropertyFileReferences"] = {
                    field: [{"location": {"uri": "unread-external.sarif-external-properties"}}],
                }
                check_codeql.validate_report(self.report)


class FileChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "analysis.sarif"

    def test_missing_file_fails(self):
        with self.assertRaisesRegex(check_codeql.SarifError, "Missing"):
            check_codeql.check_sarif(self.path)

    def test_malformed_empty_or_non_json_file_fails(self):
        for content in (b"", b"{", b"null", b"[]", b"\xff", b'{"runs": NaN}'):
            with self.subTest(content=content), self.assertRaises(check_codeql.SarifError):
                self.path.write_bytes(content)
                check_codeql.check_sarif(self.path)

    def test_duplicate_keys_cannot_replace_findings_with_empty_results(self):
        self.path.write_text(
            '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"CodeQL"}},'
            '"results":[{"message":{"text":"finding"}}],"results":[]}]}', encoding="utf-8",
        )
        with self.assertRaisesRegex(check_codeql.SarifError, "duplicate"):
            check_codeql.check_sarif(self.path)

    def test_input_size_is_bounded(self):
        self.path.write_text(json.dumps(COMPLETE), encoding="utf-8")
        with patch.object(check_codeql, "MAX_SARIF_BYTES", 16):
            with self.assertRaisesRegex(check_codeql.SarifError, "exceeds"):
                check_codeql.check_sarif(self.path)

    def test_cli_returns_success_only_for_complete_zero_findings(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "check_codeql.py"
        for findings, expected in (([], 0), ([{"message": {"text": "Synthetic finding"}}], 1)):
            with self.subTest(expected=expected):
                report = copy.deepcopy(COMPLETE)
                report["runs"][0]["results"] = findings
                self.path.write_text(json.dumps(report), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(script), str(self.path)], capture_output=True,
                    text=True, timeout=10, check=False,
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
