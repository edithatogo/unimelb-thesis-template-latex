#!/usr/bin/env python3
"""Consume an already normalized, pinned UMTHESIS v1 configuration in LaTeX.

The Typst repository remains the only canonical schema/resolver owner. This
adapter verifies envelope identity and emits a narrow metadata fragment.
Source generation is not an executed LaTeX document or submission clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


CANONICAL_MANIFEST_SHA256 = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
VERSION = "1.0.0"
ENVELOPE = {
    "contract_version", "contract_sha256", "configuration",
    "configuration_sha256", "diagnostics",
}
CONFIGURATION = {
    "contract_version", "purpose", "layout", "double_sided", "identity",
    "output", "pdf_standards", "language", "label_locale", "bibliography",
    "metadata", "approval_refs",
}
SUPPORTED_META = {
    "title", "author", "degree", "academic_units", "submission",
    "abstract", "declarations",
}
SUBFIELDS = {
    "author": {"student_record_name", "orcid"},
    "degree": {"kind", "course"},
    "submission": {"month"},
    "declarations": {"original_work", "word_count"},
}
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


class ConsumerError(ValueError):
    """Privacy-safe rejection without exposing author metadata or source paths."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


class UnsupportedConfiguration(ConsumerError):
    """Well-formed configuration outside the implemented source-only slice."""


def canonical_digest(configuration):
    try:
        payload = json.dumps(
            configuration, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ConsumerError("invalid-configuration-json") from exc
    return hashlib.sha256(payload).hexdigest()


def _text(value, name, *, required=False):
    if value is None:
        if required:
            raise ConsumerError("missing-" + name)
        return None
    if type(value) is not str or len(value) > 4000:
        raise ConsumerError("invalid-" + name)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ConsumerError("invalid-" + name)
    if required and not value.strip():
        raise ConsumerError("missing-" + name)
    return value


def _tex_escape(value):
    mapping = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "#": r"\#", "$": r"\$", "%": r"\%", "&": r"\&",
        "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(char, char) for char in value)


def _month(value, required):
    value = _text(value, "submission-month", required=required)
    if value is None:
        return None
    if not re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", value):
        raise ConsumerError("invalid-submission-month")
    return MONTHS[int(value[-2:]) - 1] + " " + value[:4]


def _validate(envelope):
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE:
        raise ConsumerError("invalid-envelope-shape")
    if (envelope["contract_version"] != VERSION
            or envelope["contract_sha256"] != CANONICAL_MANIFEST_SHA256):
        raise ConsumerError("wrong-contract")
    conf = envelope["configuration"]
    if type(conf) is not dict or set(conf) != CONFIGURATION:
        raise ConsumerError("invalid-configuration-shape")
    if conf["contract_version"] != VERSION:
        raise ConsumerError("wrong-configuration-version")
    if (type(envelope["configuration_sha256"]) is not str
            or envelope["configuration_sha256"] != canonical_digest(conf)):
        raise ConsumerError("configuration-digest-mismatch")
    if type(envelope["diagnostics"]) is not list:
        raise ConsumerError("invalid-diagnostics")
    for entry in envelope["diagnostics"]:
        if type(entry) is not dict or set(entry) != {"code", "path"}:
            raise ConsumerError("invalid-diagnostics")
        if any(type(x) is not str for x in entry.values()):
            raise ConsumerError("invalid-diagnostics")

    for field in ("purpose", "layout", "identity", "output", "language", "label_locale"):
        if type(conf[field]) is not str:
            raise ConsumerError("invalid-" + field)
    if type(conf["double_sided"]) is not bool:
        raise ConsumerError("invalid-double-sided")
    if type(conf["pdf_standards"]) is not list:
        raise ConsumerError("invalid-pdf-standards")
    if type(conf["approval_refs"]) is not dict:
        raise ConsumerError("invalid-approvals")
    if type(conf["bibliography"]) is not dict:
        raise ConsumerError("invalid-bibliography")
    if type(conf["metadata"]) is not dict:
        raise ConsumerError("invalid-metadata")

    supported = (
        conf["purpose"] in ("draft", "examination")
        and conf["layout"] == "default"
        and conf["double_sided"] is False
        and conf["identity"] == "identified" and conf["output"] == "pdf"
        and conf["pdf_standards"] == [] and conf["language"] == "en"
        and conf["label_locale"] == "en"
        and conf["bibliography"] == {"mode": "unified", "style": "apa"}
        and conf["approval_refs"] == {}
    )
    if not supported or any(k not in SUPPORTED_META for k in conf["metadata"]):
        raise UnsupportedConfiguration("unsupported-canonical-configuration")

    meta = conf["metadata"]
    for group, allowed in SUBFIELDS.items():
        if group in meta:
            value = meta[group]
            if type(value) is not dict:
                raise ConsumerError("invalid-" + group)
            if any(field not in allowed for field in value):
                raise UnsupportedConfiguration("unsupported-metadata-field")
    if "academic_units" in meta:
        units = meta["academic_units"]
        if type(units) is not list or any(type(x) is not str or not x.strip() for x in units):
            raise ConsumerError("invalid-academic-units")
        if len(units) > 1:
            raise UnsupportedConfiguration("multiple-academic-units-not-mapped")
    if "declarations" in meta:
        attestation = meta["declarations"].get("original_work")
        if attestation is not None and type(attestation) is not bool:
            raise ConsumerError("invalid-attestation")
        if attestation is False:
            raise UnsupportedConfiguration("unconfirmed-original-work")
        word_count = meta["declarations"].get("word_count")
        if word_count is not None and (type(word_count) is not int or word_count < 0):
            raise ConsumerError("invalid-word-count")
    for field in ("title", "abstract"):
        if field in meta:
            _text(meta[field], field)
    for group, fields in (("author", ("student_record_name", "orcid")),
                          ("degree", ("kind", "course"))):
        for field in fields:
            if field in meta.get(group, {}):
                _text(meta[group][field], group + "-" + field)
    final = conf["purpose"] != "draft"
    _text(meta.get("title"), "title", required=final)
    _text(meta.get("author", {}).get("student_record_name"), "author", required=final)
    _text(meta.get("degree", {}).get("course"), "degree", required=final)
    _month(meta.get("submission", {}).get("month"), required=final)
    if final:
        if not meta.get("academic_units"):
            raise ConsumerError("missing-academic-units")
        if meta.get("degree", {}).get("kind") not in ("doctoral", "research-masters"):
            raise ConsumerError("invalid-degree-kind")
        _text(meta.get("abstract"), "abstract", required=True)
        declarations = meta.get("declarations", {})
        if declarations.get("original_work") is not True:
            raise ConsumerError("missing-original-work")
        if type(declarations.get("word_count")) is not int:
            raise ConsumerError("missing-word-count")
    return conf


def prepare(envelope):
    """Return TeX metadata fragment plus non-PII receipt for a narrow input.

    It intentionally does not render abstract/declaration or claim PDF parity.
    """
    conf = _validate(envelope)
    metadata = conf["metadata"]
    draft = conf["purpose"] == "draft"
    def value(item, placeholder):
        return item if item is not None and item.strip() else "[Draft " + placeholder + " not supplied]"
    title = value(metadata.get("title"), "title")
    author = value(metadata.get("author", {}).get("student_record_name"), "author")
    degree = value(metadata.get("degree", {}).get("course"), "degree")
    month = value(_month(metadata.get("submission", {}).get("month"), required=False), "month")
    units = metadata.get("academic_units", [])
    school = units[0] if units else "[Draft academic unit not supplied]"
    fields = [
        ("title", title), ("authors", author), ("degree", degree),
        ("submissiondate", month), ("school", school),
    ]
    orcid = metadata.get("author", {}).get("orcid")
    if orcid:
        fields.append(("orcid", orcid))
    lines = [
        "% UMTHESIS 1.0.0 bounded normalized metadata consumer.",
        "% Source-only. Do not treat this as an approved examination/deposit.",
    ]
    lines.extend("\\" + command + "{" + _tex_escape(text) + "}" for command, text in fields)
    text = "\n".join(lines) + "\n"
    return text, {
        "schema_version": 1, "status": "source-only-not-rendered",
        "contract_version": VERSION,
        "contract_sha256": CANONICAL_MANIFEST_SHA256,
        "configuration_sha256": envelope["configuration_sha256"],
        "tex_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "supported_configuration": True,
        "requires_author_review": draft,
        "university_approved": False,
        "observed_rendered_order": "unexecuted",
    }


def _decode_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConsumerError("duplicate-input-key")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        paths = (args.input.absolute(), args.output.absolute(), args.report.absolute())
        if len(set(paths)) != 3 or any(p.is_symlink() for p in paths):
            raise ConsumerError("overlapping-input-output")
        if args.output.exists() or args.report.exists():
            raise ConsumerError("output-already-exists")
        raw = args.input.read_bytes()
        if len(raw) > 512_000:
            raise ConsumerError("oversized-input")
        payload = json.loads(raw, object_pairs_hook=_decode_pairs,
                             parse_constant=lambda _: (_ for _ in ()).throw(ConsumerError("nonfinite-input")))
        tex, receipt = prepare(payload)
        # Inputs are already validated before either file can be created.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(tex, encoding="utf-8")
        args.report.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    except (ConsumerError, UnicodeError, OSError, json.JSONDecodeError) as exc:
        if args.output.exists() and args.output != args.input:
            args.output.unlink()
        code = exc.code if isinstance(exc, ConsumerError) else "invalid-io-or-json"
        print("umthesis-latex: " + code, file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "tex_sha256": receipt["tex_sha256"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
