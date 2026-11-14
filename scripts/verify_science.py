#!/usr/bin/env python3
"""Compile the isolated scientific-authoring fixture and check its rendered PDF.

This is an opt-in capability probe. It does not certify PDF accessibility,
archival conformance or compliance with institutional submission rules.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from scripts.verify import VerificationError, normalize_text, require_file, run_command, validate_log

REQUIRED_TEXT = (
    "Scientific authoring fixture",
    "Take-home message",
    "The effect estimate is illustrative",
    "Plain-language summary",
    "Key terms",
    "Synthetic resource-use quantities",
    "Synthetic calculation",
    "Synthetic quadratic sequence",
)


def build_command(directory: str, source: str) -> list[str]:
    """Force LuaLaTeX without shell escape, writing only into a fresh directory."""
    return [
        "lualatex", "-no-shell-escape", "-halt-on-error", "-file-line-error",
        "-interaction=nonstopmode", f"-output-directory={directory}", source,
    ]


def validate_science_text(text: str) -> int:
    """Test actual rendered presence of every supported illustrative feature."""
    normalized = normalize_text(text)
    if not normalized:
        raise VerificationError("Scientific fixture has empty extracted text")
    missing = [expected for expected in REQUIRED_TEXT if expected not in normalized]
    if missing:
        raise VerificationError("Scientific fixture missing rendered features: " + ", ".join(missing))
    return len(normalized.split())


def verify_science(repo_root: Path) -> dict[str, int]:
    with tempfile.TemporaryDirectory(prefix="thesis-science-") as directory:
        output = Path(directory)
        env = os.environ.copy()
        env["TEXINPUTS"] = str(repo_root / "template") + "//" + os.pathsep + env.get("TEXINPUTS", "")
        run_command(
            build_command(directory, "examples/science-demo.tex"),
            cwd=repo_root, env=env, timeout=300,
        )
        pdf = require_file(output / "science-demo.pdf")
        log = require_file(output / "science-demo.log")
        validate_log(log.read_text(encoding="utf-8", errors="replace"))
        run_command(["qpdf", "--check", str(pdf)], cwd=repo_root, env=env, timeout=30)
        info = run_command(["pdfinfo", str(pdf)], cwd=repo_root, env=env, timeout=30, reject_stderr=True)
        pages = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
        if not pages or int(pages.group(1)) < 1:
            raise VerificationError("Scientific fixture has invalid PDF page count")
        text = run_command(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], cwd=repo_root, env=env, timeout=30, reject_stderr=True)
        return {"pages": int(pages.group(1)), "words": validate_science_text(text)}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = verify_science(root)
    print(f"Scientific-authoring fixture verified: {result['pages']} page(s), {result['words']} extracted words")
