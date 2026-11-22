#!/usr/bin/env python3
"""Pinned UMTHESIS v1 input consumer and optional synthetic LaTeX metadata probe.

The canonical validator and its full fixture catalogue live upstream. This
consumer refuses drift; it does not publish a duplicate policy schema or claim
full institutional, PDF/UA or rights conformance.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

# SHA identities belong to the same reviewed upstream snapshot.
UPSTREAM_REVISION = "861a644f8d1e8ede866b213d32f70fdefde5bbe4"
MANIFEST_SHA256 = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
FIXTURES_SHA256 = "af82359a786b2be565e49de594e32a5d2edb3354221dfd5371d5d954b33c5757"
LIBRARY_SHA256 = "fdb89aa329357bc7a2325fbba791507d9e64784edce3e7fac0c8826fe5a77bb7"
ADAPTER_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]


class QualificationError(RuntimeError):
    """A missing input, unsatisfied pin, or unsupported output prevents acceptance."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
            text=True, check=True, timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise QualificationError("Required canonical checkout cannot be verified") from exc
    return completed.stdout.strip()


def pinned_inputs(checkout: Path) -> tuple[Path, Path]:
    """Validate exact Git/source/bundle identities before importing upstream code."""
    checkout = checkout.absolute()
    if checkout.is_symlink() or not checkout.is_dir():
        raise QualificationError("Missing or symlinked upstream checkout")
    if git_revision(checkout) != UPSTREAM_REVISION:
        raise QualificationError("Canonical checkout revision differs from the pin")
    root = checkout / "contracts" / "thesis" / "v1"
    library = checkout / "scripts" / "thesis_contract.py"
    checks = (
        (root / "manifest.json", MANIFEST_SHA256),
        (root / "fixtures.json", FIXTURES_SHA256),
        (library, LIBRARY_SHA256),
    )
    for path, expected in checks:
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise QualificationError("Canonical contract file missing or digest mismatch")
    return root, library


def load_canonical(checkout: Path):
    root, library = pinned_inputs(checkout)
    spec = importlib.util.spec_from_file_location("umthesis_pinned_contract", library)
    if spec is None or spec.loader is None:
        raise QualificationError("Cannot load reviewed canonical validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bundle = module.Bundle(root, expected_digest=MANIFEST_SHA256)
    if bundle.compatibility.get("adapter_api_version") != ADAPTER_VERSION:
        raise QualificationError("Canonical adapter API version is unsupported")
    return module, bundle


def latex_escape(value: str) -> str:
    """Emit literal text; never let normalized metadata create TeX commands."""
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "%": r"\%", "$": r"\$", "#": r"\#", "&": r"\&",
        "_": r"\_", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def month_label(month: str) -> str:
    try:
        year, number = month.split("-")
        calendar = date(int(year), int(number), 1)
    except (AttributeError, ValueError) as exc:
        raise QualificationError("Invalid normalized submission month") from exc
    return calendar.strftime("%B %Y")


def metadata_values(configuration: dict) -> dict[str, str]:
    if configuration.get("contract_version") != ADAPTER_VERSION:
        raise QualificationError("Unsupported normalized contract version")
    for key, valid in (
        ("identity", "identified"), ("output", "pdf"),
        ("language", "en"), ("label_locale", "en"),
    ):
        if configuration.get(key, valid) != valid:
            raise QualificationError(f"unsupported LaTeX metadata-rendering profile: {key}")
    if configuration.get("pdf_standards"):
        raise QualificationError("unsupported claimed PDF standard for metadata probe")
    metadata = configuration.get("metadata")
    if not isinstance(metadata, dict):
        raise QualificationError("Missing normalized metadata")
    supported = {"title", "author", "degree", "academic_units", "submission", "abstract", "declarations"}
    unsupported = set(metadata) - supported
    if unsupported:
        raise QualificationError("unsupported metadata-rendering fields: " + ", ".join(sorted(unsupported)))
    try:
        values = {
            "title": metadata["title"],
            "author": metadata["author"]["student_record_name"],
            "degree": metadata["degree"]["course"],
            "school": metadata["academic_units"][0],
            "submission_date": month_label(metadata["submission"]["month"]),
            "abstract": metadata["abstract"],
        }
    except (KeyError, IndexError, TypeError) as exc:
        raise QualificationError("Missing normalized document metadata") from exc
    if not all(isinstance(s, str) and s.strip() for s in values.values()):
        raise QualificationError("missing nonempty normalized document metadata")
    if not isinstance(metadata["academic_units"], list) or len(metadata["academic_units"]) != 1:
        raise QualificationError("unsupported multiple academic units in metadata-rendering probe")
    return values


def render_source(configuration: dict) -> str:
    """Render a synthetic *metadata-only* probe, not a final-submission thesis."""
    vals = {key: latex_escape(value) for key, value in metadata_values(configuration).items()}
    return (
        r"\documentclass[a4paper,11pt,oneside]{Thesis}" + "\n"
        + rf"\title{{{vals['title']}}}" + "\n"
        + rf"\authors{{{vals['author']}}}" + "\n"
        + rf"\degree{{{vals['degree']}}}" + "\n"
        + r"\thesistype{Synthetic doctoral specimen}" + "\n"
        + r"\subject{Synthetic metadata qualification}" + "\n"
        + r"\keywords{synthetic, contract, verification}" + "\n"
        + rf"\submissiondate{{{vals['submission_date']}}}" + "\n"
        + r"\university{The University of Melbourne}" + "\n"
        + r"\department{Synthetic Department}" + "\n"
        + rf"\school{{{vals['school']}}}" + "\n"
        + r"\begin{document}" + "\n"
        + r"\frontmatter" + "\n"
        + r"\maketitle" + "\n"
        + r"\begin{abstract}" + "\n"
        + vals["abstract"] + "\n"
        + r"\end{abstract}" + "\n"
        + r"\Declaration{Synthetic declaration fixture for \thesistitle.}" + "\n"
        + r"\mainmatter" + "\n"
        + r"\chapter{Synthetic text}" + "\n"
        + r"This document tests literal metadata rendering only." + "\n"
        + r"\end{document}" + "\n"
    )


def latexmk_args(source: str, out_dir: str) -> list[str]:
    return [
        "latexmk", "-lualatex", "-no-shell-escape", "-interaction=nonstopmode",
        "-halt-on-error", "-file-line-error", f"-outdir={out_dir}", source,
    ]


def validate_rendered(info: str, text: str, configuration: dict) -> dict:
    """Require title metadata on the first physical page in documented order."""
    vals = metadata_values(configuration)
    parsed = {}
    for line in info.splitlines():
        key, sep, value = line.partition(":")
        if sep and key in {"Title", "Author", "Pages"}:
            if key in parsed:
                raise QualificationError(f"Duplicate PDF metadata: {key}")
            parsed[key] = value.strip()
    if parsed.get("Title") != vals["title"] or parsed.get("Author") != vals["author"]:
        raise QualificationError("Rendered PDF metadata disagrees with normalized input")
    try:
        page_count = int(parsed["Pages"])
    except (ValueError, KeyError) as exc:
        raise QualificationError("Missing PDF page count") from exc
    if page_count <= 0:
        raise QualificationError("Invalid PDF page count")
    first = " ".join(text.split("\f")[0].split())
    positions = [first.find(" ".join(vals[k].split())) for k in
                 ("title", "author", "degree", "submission_date", "school")]
    if -1 in positions:
        raise QualificationError("Missing title metadata from first physical page")
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise QualificationError("Incorrect rendered title metadata order")
    pages = text.split("\f")
    if len(pages) > 1 and not pages[-1].strip():
        pages.pop()  # Poppler normally ends text extraction with a form feed.
    if len(pages) != page_count:
        raise QualificationError("Extracted physical page count differs from PDF metadata")
    abstract_pages = [
        index for index, page in enumerate(pages)
        if index > 0
        and any(line.strip() == "Abstract" for line in page.splitlines())
        and all(" ".join(vals[key].split()) in " ".join(page.split())
                for key in ("title", "author", "abstract"))
    ]
    if len(abstract_pages) != 1:
        raise QualificationError("Missing or ambiguous rendered abstract on a separate physical page")
    return {"title_page": 1, "abstract_page": abstract_pages[0] + 1,
            "physical_pages": page_count, "metadata_fields": 5}


def check_fixture(bundle, module, identifier: str) -> dict:
    record = bundle.fixtures.get(identifier)
    if record is None:
        raise QualificationError("Unknown canonical fixture ID")
    fixture = module.read_json(bundle.root / record["path"])
    if fixture["id"] != identifier or digest(bundle.root / record["path"]) != record["sha256"]:
        raise QualificationError("Stale or tampered canonical fixture")
    try:
        normalized = bundle.normalize(fixture["metadata"], bundle.parse_cli(fixture["cli"]), fixture["explicit"])
    except module.ContractError as exc:
        if fixture["expected"]["result"] != "invalid" or exc.code != fixture["expected"].get("error_code"):
            raise QualificationError("Unexpected negative canonical fixture result") from exc
        return {"id": identifier, "sha256": record["sha256"], "normalization": "expected-invalid", "error_code": exc.code,
                "rendering": "not-applicable"}
    if fixture["expected"]["result"] != "valid":
        raise QualificationError("Canonical negative fixture unexpectedly accepted")
    for dotted, expected_value in fixture["expected"]["values"].items():
        current = normalized["configuration"]
        for piece in dotted.split("."):
            if not isinstance(current, dict) or piece not in current:
                raise QualificationError("Missing expected canonical fixture oracle path")
            current = current[piece]
        if current != expected_value:
            raise QualificationError("Canonical fixture semantic oracle mismatch")
    actual_codes = {entry["code"] for entry in normalized["diagnostics"]}
    if actual_codes != set(fixture["expected"]["diagnostic_codes"]):
        raise QualificationError("Canonical fixture diagnostics differ from expected")
    return {
        "id": identifier, "sha256": record["sha256"], "normalization": "executed-pass",
        "diagnostic_codes": sorted(actual_codes), "rendering": "unexecuted",
        "configuration": normalized["configuration"],
    }


def run_render(root: Path, configuration: dict) -> dict:
    from scripts.verify import run_command, validate_log
    source = render_source(configuration)
    with tempfile.TemporaryDirectory(prefix="latex-umthesis-") as temporary:
        temp = Path(temporary)
        tex = temp / "synthetic-contract.tex"
        tex.write_text(source, encoding="utf-8")
        env = os.environ.copy()
        env["TEXINPUTS"] = f"{root / 'template'}//{os.pathsep}" + env.get("TEXINPUTS", "")
        env.update(SOURCE_DATE_EPOCH="1794700800", FORCE_SOURCE_DATE="1", TZ="UTC")
        run_command(latexmk_args(str(tex), temporary), cwd=root, env=env, timeout=300)
        pdf = temp / "synthetic-contract.pdf"
        log = temp / "synthetic-contract.log"
        if not pdf.is_file() or not log.is_file() or not pdf.stat().st_size:
            raise QualificationError("Missing rendered synthetic LaTeX artifact")
        validate_log(log.read_text(encoding="utf-8", errors="replace"))
        run_command(["qpdf", "--check", str(pdf)], cwd=root, env=env, timeout=30)
        info = run_command(["pdfinfo", str(pdf)], cwd=root, env=env, timeout=30, reject_stderr=True)
        text = run_command(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], cwd=root, env=env, timeout=30, reject_stderr=True)
        return {**validate_rendered(info, text, configuration), "pdf_sha256": digest(pdf),
                "pdf_bytes": pdf.stat().st_size, "rendering": "executed-pass"}


def prepare_output(path: Path) -> None:
    """Clear stale successful evidence without following symlinked parents."""
    root = ROOT.absolute()
    target = path.absolute()
    allowed = root / "build" / "contract"
    if ".." in target.parts:
        raise QualificationError("Refusing output path parent traversal")
    if target == allowed or not target.is_relative_to(allowed):
        raise QualificationError("Output must reside within build/contract")
    candidate = root
    for part in target.relative_to(root).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise QualificationError("Refusing symlinked contract output path")
    if target.exists() and not target.is_file():
        raise QualificationError("Contract output is not a regular file")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"schema_version": 1, "status": "running"}) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True, help="exact pinned checkout of the canonical Typst source")
    parser.add_argument("--output", type=Path, default=Path("build/contract/latex-native-report.json"))
    parser.add_argument("--render-fixture", default="doctoral-monograph")
    args = parser.parse_args(argv)
    output = (ROOT / args.output).absolute()
    allowed = (ROOT / "build" / "contract").absolute()
    if output.is_symlink() or not output.is_relative_to(allowed) or output == allowed:
        parser.error("Output must be an ordinary file under build/contract")
    prepare_output(output)
    try:
        module, bundle = load_canonical(args.upstream)
        canonical_cases = bundle.verify_fixtures()  # the authoritative oracle
        cases = [check_fixture(bundle, module, key) for key in sorted(bundle.fixtures)]
        if len(cases) != len(canonical_cases):
            raise QualificationError("Canonical and consumer fixture inventories differ")
        observations = [{key: value for key, value in case.items() if key != "configuration"}
                        for case in cases]
        chosen = check_fixture(bundle, module, args.render_fixture)
        if chosen["normalization"] != "executed-pass":
            raise QualificationError("Selected fixture does not produce a valid normalized configuration")
        rendered = run_render(ROOT, chosen["configuration"])
        report = {
            "schema_version": 1, "scope": "latex-metadata-only-qualification-slice",
            "status": "passed", "contract_version": "1.0.0", "contract_sha256": bundle.digest,
            "fixture_manifest_sha256": FIXTURES_SHA256,
            "upstream_revision": UPSTREAM_REVISION, "adapter_version": ADAPTER_VERSION,
            "latex_revision": git_revision(ROOT),
            "contract_status": bundle.manifest.get("status"),
            "input_cases": observations, "rendered_fixture": args.render_fixture,
            "rendered_fixture_sha256": chosen["sha256"], "rendered": rendered,
            "institutional_approval": "unverified", "pdf_accessibility": "unverified",
            "publication_rights": "unverified", "full_contract_acceptance": "unexecuted",
            "rendered_scope": ["metadata.title", "metadata.author.student_record_name",
                               "metadata.degree.course", "metadata.academic_units[0]",
                               "metadata.submission.month", "metadata.abstract"],
            "not_qualified": ["bibliography", "publication-rights", "PDF/UA", "PDF/A",
                              "declarations", "complete-institutional-policy", "cross-engine"],
        }
    except Exception as error:
        # Do not disclose synthetic fixture data or external exception internals.
        output.write_text(json.dumps({"schema_version": 1, "status": "failed",
                                      "contract_sha256": MANIFEST_SHA256,
                                      "error_type": type(error).__name__}) + "\n", encoding="utf-8")
        print(f"Contract consumer failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Canonical fixtures qualified: {len(observations)}; LaTeX metadata probe rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
