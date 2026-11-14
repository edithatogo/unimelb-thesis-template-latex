#!/usr/bin/env python3
"""Require complete standalone SARIF with zero findings after a successful analyzer.

This checks the SARIF 2.1.0 completion/result fields, not the entire SARIF schema.
Optional metadata and invocation records may be absent. The workflow must also
require the pinned analyzer step to succeed; a report alone cannot prove that.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


MAX_SARIF_BYTES = 20 * 1024 * 1024


class SarifError(ValueError):
    """The analysis report cannot establish a complete zero-findings result."""


def _object(value: object, location: str) -> dict:
    if not isinstance(value, dict):
        raise SarifError(f"{location} must be an object")
    return value


def _array(value: object, location: str) -> list:
    if not isinstance(value, list):
        raise SarifError(f"{location} must be an array")
    return value


def validate_report(document: object) -> int:
    """Check every run; return its count only when all runs have zero findings."""
    report = _object(document, "SARIF report")
    if report.get("version") != "2.1.0":
        raise SarifError("SARIF version must be 2.1.0")
    runs = _array(report.get("runs"), "runs")
    if not runs:
        raise SarifError("SARIF report contains no analysis runs")

    findings = 0
    for index, value in enumerate(runs):
        location = f"runs[{index}]"
        run = _object(value, location)
        tool = _object(run.get("tool"), f"{location}.tool")
        driver = _object(tool.get("driver"), f"{location}.tool.driver")
        if not isinstance(driver.get("name"), str) or not driver["name"]:
            raise SarifError(f"{location}.tool.driver.name must be a nonempty string")

        # SARIF distinguishes missing/null results (no analysis) from [] (none found).
        findings += len(_array(run.get("results"), f"{location}.results"))
        external = _object(
            run.get("externalPropertyFileReferences", {}),
            f"{location}.externalPropertyFileReferences",
        )
        for field in ("results", "invocations"):
            references = _array(external.get(field, []), f"{location}.external.{field}")
            if references:
                raise SarifError(f"External {field} are incomplete for this standalone gate")

        invocations = _array(run.get("invocations", []), f"{location}.invocations")
        for invocation in invocations:
            invocation = _object(invocation, f"{location}.invocation")
            if invocation.get("executionSuccessful") is not True:
                raise SarifError(f"{location} contains an unsuccessful or incomplete invocation")
            for field in ("toolExecutionNotifications", "toolConfigurationNotifications"):
                notifications = _array(invocation.get(field, []), f"{location}.{field}")
                for notification in notifications:
                    notification = _object(notification, f"{location}.{field} entry")
                    level = notification.get("level", "warning")
                    if level not in ("none", "note", "warning", "error"):
                        raise SarifError(f"{location}.{field} has an invalid notification level")
                    if level == "error":
                        raise SarifError(f"{location} reports an analysis error in {field}")

    if findings:
        raise SarifError(f"CodeQL reported {findings} finding(s); inspect the retained SARIF")
    return len(runs)


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SarifError("SARIF JSON contains a duplicate object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SarifError("SARIF JSON contains a non-standard numeric constant")


def check_sarif(path: Path) -> int:
    """Read one expected report with bounded input and unambiguous JSON parsing."""
    try:
        if not path.is_file():
            raise SarifError(f"Missing or non-regular SARIF report: {path}")
        with path.open("rb") as source:
            content = source.read(MAX_SARIF_BYTES + 1)
        if len(content) > MAX_SARIF_BYTES:
            raise SarifError(f"SARIF report exceeds {MAX_SARIF_BYTES} bytes")
        document = json.loads(
            content, object_pairs_hook=_unique_keys, parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SarifError(f"Cannot read valid SARIF JSON from {path}: {error}") from error
    return validate_report(document)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sarif", type=Path, help="Expected standalone CodeQL SARIF file")
    args = parser.parse_args()
    try:
        runs = check_sarif(args.sarif)
    except SarifError as error:
        print(f"CodeQL gate failed: {error}", file=sys.stderr)
        return 1
    print(f"CodeQL gate passed: {runs} analysis run(s), zero findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
