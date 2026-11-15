#!/usr/bin/env python3
"""Build and verify the example using fresh outputs and bounded external commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

if __package__:
    from .document_semantics import validate_document_semantics
else:
    from document_semantics import validate_document_semantics


BUILD_TIMEOUT = 300
PDF_TIMEOUT = 30
CLEANUP_TIMEOUT = 5
DIAGNOSTIC_LIMIT = 4096
DEFAULT_SOURCE_DATE_EPOCH = "1735689600"
ARTIFACT_NAMES = (
    "Thesis.pdf", "Thesis.log", "Thesis.bbl", "Thesis.blg", "Thesis.gls",
)
REQUIRED_SECTIONS = (
    "A Modernised Thesis Template",
    "Abstract",
    "Declaration of Authorship",
    "Preface",
    "Contents",
    "Introduction",
    "Glossary",
    "Bibliography",
    "An Appendix",
)
# Headings can appear in the contents or chapter prose without the section body.
REQUIRED_CONTENT = (
    "The TeXbook",
    "A document preparation system",
    "Vivamus at pulvinar nisi.",
)
# Expected plain text for this synthetic example, not the shared UMTHESIS schema.
EXAMPLE_METADATA = {
    "title": "A Modernised Thesis Template",
    "author": "Example Author",
    "degree": "Doctor of Philosophy",
    "submission_date": "January 2025",
    "department": "Department of Modernisation",
    "school": "School of Advanced Templates",
    "bibliography_content": "The TeXbook",
    "appendix_content": "Vivamus at pulvinar nisi.",
}
HARD_LOG_ERRORS = (
    ("TeX error", r"^!|(?:LaTeX|Package [^\n]+) Error:|Emergency stop|Fatal error|Runaway argument"),
    ("undefined citation or reference", r"(?:Citation|Reference)\b[^\n]*(?:\n[^\n]*)?\bundefined\b|There were undefined (?:references|citations)"),
    ("unresolved labels", r"Label\(s\) may have changed|multiply[- ]defined labels|Label [^\n]+ multiply defined"),
    ("another typesetting pass required", r"Please\s+(?:\(re\))?run\s+(?:Biber|BibTeX|LaTeX|LuaLaTeX)|Rerun\s+(?:LaTeX|Biber|to get)"),
    ("missing bibliography or glossary", r"Empty bibliography|No file [^\n]*\.(?:bbl|gls)\b"),
)


class VerificationError(RuntimeError):
    """A build or validation gate failed."""


def command_diagnostic(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    """Keep bounded compiler/PDF diagnostics, including failures before a log exists."""
    parts = []
    for label, output in (("stdout", stdout), ("stderr", stderr)):
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if output:
            parts.append(f"{label}:\n{output}")
    combined = "\n".join(parts)
    if not combined:
        return ""
    return f"\nCommand output (last {DIAGNOSTIC_LIMIT} characters):\n{combined[-DIAGNOSTIC_LIMIT:]}"


def run_command(
    command: list[str], *, cwd: Path, env: dict[str, str], timeout: int,
    reject_stderr: bool = False,
) -> str:
    """Bound commands and their POSIX process group; non-POSIX fallback kills the parent."""
    try:
        process = subprocess.Popen(
            command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", shell=False,
            start_new_session=(os.name == "posix"),
        )
    except FileNotFoundError as error:
        raise VerificationError(f"Required command not found: {command[0]}") from error
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        try:
            if os.name == "posix":
                # latexmk spawns TeX/Biber/makeindex: stop the group, not only its parent.
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=CLEANUP_TIMEOUT)
        except subprocess.TimeoutExpired as drain_error:
            # A detached process may have inherited a pipe; do not wait indefinitely.
            stdout, stderr = drain_error.output or error.output, drain_error.stderr or error.stderr
            process.stdout.close()
            process.stderr.close()
            try:
                process.wait(timeout=CLEANUP_TIMEOUT)
            except subprocess.TimeoutExpired:
                pass
        raise VerificationError(
            f"{command[0]} timed out after {timeout} seconds" + command_diagnostic(stdout, stderr)
        ) from error
    if process.returncode:
        raise VerificationError(
            f"{command[0]} exited with status {process.returncode}" + command_diagnostic(stdout, stderr)
        )
    if reject_stderr and stderr.strip():
        raise VerificationError(
            f"{command[0]} produced diagnostic output on stderr" + command_diagnostic(stdout, stderr)
        )
    return stdout


def require_file(path: Path) -> Path:
    # Only inspect ordinary files produced in this fresh build directory.
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise VerificationError(f"Missing, empty, or non-regular build output: {path.name}")
    return path


def validate_log(text: str) -> None:
    if not text.strip():
        raise VerificationError("Empty final LaTeX log")
    for description, pattern in HARD_LOG_ERRORS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            raise VerificationError(f"Final LaTeX log contains {description}")


def normalize_text(text: str) -> str:
    """Ignore whitespace layout only; keep every extracted character and its order."""
    return " ".join(text.split())



def validate_font_inventory(report: str) -> int:
    """Accept only a nonempty Poppler inventory with every font embedded."""
    lines = [line for line in report.splitlines() if line.strip()]
    if (
        len(lines) < 2
        or not lines[0].lstrip().startswith("name ")
        or not set(lines[1].strip()) <= {"-", " "}
    ):
        raise VerificationError("Malformed PDF font inventory header")
    count = 0
    for line in lines[2:]:
        # Font names/types contain spaces; inspect the stable right-hand columns:
        # embedded, subset, unicode, object number, generation number.
        parts = line.split()
        if len(parts) < 7 or any(value not in ("yes", "no") for value in parts[-5:-2]):
            raise VerificationError("Malformed PDF font inventory row")
        if parts[-5] != "yes":
            raise VerificationError("PDF font not embedded: " + parts[0])
        count += 1
    if not count:
        raise VerificationError("PDF font inventory contains no fonts")
    return count


def validate_outputs(output_dir: Path, repo_root: Path, env: dict[str, str]) -> dict:
    pdf = require_file(output_dir / "Thesis.pdf")
    log = require_file(output_dir / "Thesis.log")
    validate_log(log.read_text(encoding="utf-8", errors="replace"))
    for filename, entry in (("Thesis.bbl", r"\entry{"), ("Thesis.gls", r"\glossentry{")):
        contents = require_file(output_dir / filename).read_text(encoding="utf-8", errors="replace")
        if entry not in contents:
            raise VerificationError(f"No generated entries in {filename}")

    run_command(["qpdf", "--check", str(pdf)], cwd=repo_root, env=env, timeout=PDF_TIMEOUT)
    info = run_command(
        ["pdfinfo", str(pdf)], cwd=repo_root, env=env, timeout=PDF_TIMEOUT,
        reject_stderr=True,
    )
    pages = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if not pages or int(pages.group(1)) < 1:
        raise VerificationError("PDF must report a positive page count")
    fonts = run_command(
        ["pdffonts", str(pdf)], cwd=repo_root, env=env, timeout=PDF_TIMEOUT,
        reject_stderr=True,
    )
    embedded_font_count = validate_font_inventory(fonts)
    text = run_command(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        cwd=repo_root, env=env, timeout=PDF_TIMEOUT, reject_stderr=True,
    )
    normalized = normalize_text(text)
    if not normalized:
        raise VerificationError("PDF has no extractable text")
    missing = [section for section in REQUIRED_SECTIONS if section not in normalized]
    if missing:
        raise VerificationError("PDF is missing expected sections: " + ", ".join(missing))
    missing_content = [content for content in REQUIRED_CONTENT if content not in normalized]
    if missing_content:
        raise VerificationError("PDF is missing expected content: " + ", ".join(missing_content))
    try:
        semantics = validate_document_semantics(info, text, EXAMPLE_METADATA)
    except ValueError as error:
        raise VerificationError(str(error)) from error
    digest = hashlib.sha256()
    with pdf.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "pdf_sha256": digest.hexdigest(),
        "pdf_bytes": pdf.stat().st_size,
        "document_semantics": semantics,
        "page_count": int(pages.group(1)),
        "embedded_font_count": embedded_font_count,
        "normalized_text_characters": len(normalized),
        "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "required_sections": list(REQUIRED_SECTIONS),
        "required_content": list(REQUIRED_CONTENT),
    }


def check_evidence_directory(repo_root: Path, evidence_dir: Path) -> None:
    """Allow only the two owned directories, with no symlink redirection before cleanup."""
    root = repo_root.absolute()
    requested = evidence_dir.absolute()
    try:
        relative = requested.relative_to(root)
    except ValueError as error:
        raise VerificationError("Evidence directory must be inside the repository") from error
    if relative.parts not in (("build", "verification"), ("build", "replay")):
        raise VerificationError("Unexpected evidence directory")
    for path in (root, root / "build", requested):
        if path.is_symlink():
            raise VerificationError("Refusing symlinked evidence directory or ancestor")
        if path.exists() and not path.is_dir():
            raise VerificationError("Evidence directory or ancestor is not a directory")


def prepare_evidence(repo_root: Path, evidence_dir: Path) -> None:
    check_evidence_directory(repo_root, evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    # Clear only files owned by this verifier, before attempting a new build.
    for filename in (*ARTIFACT_NAMES, "report.json"):
        path = evidence_dir / filename
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            raise VerificationError(f"Evidence path is not a regular file: {filename}")


def write_report(evidence_dir: Path, report: dict) -> None:
    (evidence_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )


def retain_outputs(output_dir: Path, evidence_dir: Path) -> list[str]:
    retained = []
    for filename in ARTIFACT_NAMES:
        source = output_dir / filename
        if source.is_file() and not source.is_symlink():
            shutil.copyfile(source, evidence_dir / filename)
            retained.append(filename)
    return retained


def build_once(repo_root: Path, evidence_dir: Path, env: dict[str, str]) -> dict:
    prepare_evidence(repo_root, evidence_dir)
    report = {
        "schema_version": 1,
        "status": "running",
        "source_date_epoch": env["SOURCE_DATE_EPOCH"],
        "build_timeout_seconds": BUILD_TIMEOUT,
        "pdf_command_timeout_seconds": PDF_TIMEOUT,
        "cleanup_timeout_seconds": CLEANUP_TIMEOUT,
        "retained_artifacts": [],
    }
    write_report(evidence_dir, report)
    with tempfile.TemporaryDirectory(prefix="thesis-verify-") as temporary:
        output_dir = Path(temporary)
        try:
            run_command(
                [
                    "latexmk", "-lualatex", "-interaction=nonstopmode",
                    "-halt-on-error", "-file-line-error", "-no-shell-escape",
                    f"-outdir={output_dir}", "example/Thesis.tex",
                ],
                cwd=repo_root, env=env, timeout=BUILD_TIMEOUT,
            )
            report.update(validate_outputs(output_dir, repo_root, env))
            report["status"] = "passed"
        except (VerificationError, OSError) as error:
            report["status"] = "failed"
            report["error"] = str(error)
            raise VerificationError(str(error)) from error
        finally:
            report["retained_artifacts"] = retain_outputs(output_dir, evidence_dir)
            write_report(evidence_dir, report)
    return report


def compare_replays(first: dict, second: dict) -> None:
    if first["normalized_text_sha256"] != second["normalized_text_sha256"]:
        raise VerificationError("Replay changed normalized extracted PDF text")
    if first["page_count"] != second["page_count"]:
        raise VerificationError("Replay changed the PDF page count")


def verify(repo_root: Path, replay: bool = False) -> dict:
    evidence_dir = repo_root / "build" / "verification"
    replay_dir = repo_root / "build" / "replay"
    # Check both destinations before clearing either one; never follow a link into source.
    check_evidence_directory(repo_root, evidence_dir)
    check_evidence_directory(repo_root, replay_dir)
    prepare_evidence(repo_root, evidence_dir)
    prepare_evidence(repo_root, replay_dir)
    env = os.environ.copy()
    epoch = env.get("SOURCE_DATE_EPOCH", DEFAULT_SOURCE_DATE_EPOCH)
    if not epoch.isascii() or not epoch.isdigit():
        message = "SOURCE_DATE_EPOCH must be a non-negative integer"
        write_report(evidence_dir, {
            "schema_version": 1, "status": "failed", "error": message, "retained_artifacts": [],
        })
        raise VerificationError(message)
    env.update(SOURCE_DATE_EPOCH=epoch, FORCE_SOURCE_DATE="1", TZ="UTC", LC_ALL="C")
    first = build_once(repo_root, evidence_dir, env)
    if replay:
        try:
            second = build_once(repo_root, replay_dir, env)
            compare_replays(first, second)
            first["replay"] = {
                "status": "passed", "comparison": "normalized text and page count",
                "pdf_bytes_equal": first["pdf_sha256"] == second["pdf_sha256"],
            }
        except VerificationError as error:
            first["status"] = "failed"
            first["error"] = str(error)
            first["replay"] = {"status": "failed"}
            raise
        finally:
            write_report(evidence_dir, first)
    return first


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true", help="compare two clean builds in the same fixed environment")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    try:
        report = verify(repo_root, replay=args.replay)
    except (VerificationError, OSError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        return 1
    print(f"Verification passed: {report['page_count']} pages; evidence in build/verification/")
    if args.replay:
        equality = "match" if report["replay"]["pdf_bytes_equal"] else "differ"
        print(f"Replay passed: normalized text and page count match; PDF bytes {equality} (same toolchain only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
