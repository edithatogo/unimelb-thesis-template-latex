#!/usr/bin/env python3
"""Emit narrowly scoped provenance for an independently verified example PDF.

A hash identifies bytes; this is not cross-machine reproducibility, policy
compliance, rights clearance, scientific validation or PDF/UA conformance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    ".latexmkrc", "template/Thesis.cls", "example/Thesis.tex",
    "example/Bibliography.bib", "scripts/verify.py", "scripts/document_semantics.py",
)
VERSION_TOOLS = {
    "lualatex": "--version", "latexmk": "--version", "biber": "--version",
    "makeglossaries": "--version", "qpdf": "--version", "pdfinfo": "-v",
    "pdffonts": "-v", "pdftotext": "-v",
}


class ProvenanceError(ValueError):
    """The evidence is missing, stale, unsafe or insufficient."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _unique_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ProvenanceError('duplicate JSON key')
        result[key] = value
    return result


def _bad_constant(_):
    raise ProvenanceError('invalid JSON number')


def read_receipt(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ProvenanceError('missing or linked build receipt')
    with path.open('rb') as stream:
        content = stream.read(4 * 1024 * 1024 + 1)
    if len(content) > 4 * 1024 * 1024:
        raise ProvenanceError('build receipt too large')
    try:
        receipt = json.loads(content, object_pairs_hook=_unique_keys, parse_constant=_bad_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProvenanceError('invalid build receipt JSON') from exc
    if not isinstance(receipt, dict) or receipt.get('schema_version') != 1 or receipt.get('status') != 'passed':
        raise ProvenanceError('build receipt is not an executed verification success')
    return receipt


def run_command(args: list[str], *, cwd: Path, timeout: int) -> str:
    """No shell, bounded runtime, combined diagnostic streams for version tools."""
    try:
        completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                   errors='replace', check=True, timeout=timeout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ProvenanceError(f'required provenance command failed: {args[0]}') from exc
    return (completed.stdout or '') + '\n' + (completed.stderr or '')


def _require_source(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ProvenanceError('required source file missing or unsafe')


def _git_identity(root: Path) -> tuple[str, bool]:
    revision = run_command(['git','-C',str(root),'rev-parse','HEAD'],cwd=root,timeout=15).strip()
    if not re.fullmatch('[a-f0-9]{40}', revision):
        raise ProvenanceError('invalid Git source revision')
    dirty = bool(run_command(['git','-C',str(root),'status','--porcelain','--untracked-files=all'],cwd=root,timeout=15).strip())
    return revision, dirty


def run_fresh_verify(root: Path) -> str:
    """Bind the current clean source checkout to a newly validated output."""
    before, dirty = _git_identity(root)
    if dirty:
        raise ProvenanceError('source checkout must be clean before verification')
    from scripts import verify as existing_verifier
    verified = existing_verifier.verify(root)
    if verified.get('status') != 'passed':
        raise ProvenanceError('fresh native verifier did not pass')
    after, dirty_after = _git_identity(root)
    if after != before or dirty_after:
        raise ProvenanceError('source checkout changed during fresh verification')
    return before


def create_manifest(root: Path) -> dict:
    root = root.absolute()
    folder = root / 'build' / 'verification'
    receipt = read_receipt(folder / 'report.json')
    pdf = folder / 'Thesis.pdf'
    _require_source(pdf)
    with pdf.open('rb') as stream:
        if stream.read(5) != b'%PDF-':
            raise ProvenanceError('retained PDF has no PDF header')
    actual_hash = sha256(pdf)
    actual_size = pdf.stat().st_size
    if (receipt.get('pdf_sha256') != actual_hash or receipt.get('pdf_bytes') != actual_size
            or not isinstance(receipt.get('page_count'), int) or receipt['page_count'] <= 0
            or type(receipt.get('embedded_font_count')) is not int or receipt['embedded_font_count'] < 1
            or not re.fullmatch(r'[a-f0-9]{64}', receipt.get('normalized_text_sha256', ''))):
        raise ProvenanceError('retained PDF does not match the successful verification receipt')
    epoch = receipt.get('source_date_epoch')
    if not isinstance(epoch, str) or not epoch.isascii() or not epoch.isdigit():
        raise ProvenanceError('Missing or invalid SOURCE_DATE_EPOCH in build receipt')
    source_hashes = {}
    for name in SOURCE_FILES:
        candidate = root / name
        _require_source(candidate)
        source_hashes[name] = sha256(candidate)
    revision, dirty = _git_identity(root)
    fonts = run_command(['pdffonts',str(pdf)],cwd=root,timeout=15)
    lines = [line for line in fonts.splitlines() if line.strip()]
    if len(lines) < 3 or not lines[0].startswith('name ') or 'emb' not in lines[0]:
        raise ProvenanceError('incomplete font inventory')
    count = len(lines) - 2
    if count != receipt['embedded_font_count']:
        raise ProvenanceError('font inventory disagrees with verified font count')
    for row in lines[2:]:
        fields = row.split()
        if len(fields) < 7 or fields[-5] != 'yes':
            raise ProvenanceError('font inventory contains unembedded/malformed rows')
    versions = {}
    for executable, option in VERSION_TOOLS.items():
        text = run_command([executable, option],cwd=root,timeout=15)
        version = next((line.strip() for line in text.splitlines() if line.strip()), '')
        if not version:
            raise ProvenanceError('required tool version is missing')
        versions[executable] = version[:240]
    return {
        'schema_version': 1, 'status': 'evidence-only',
        'scope': 'same-run-validated-synthetic-PDF',
        'source': {'revision': revision, 'tracked_dirty': dirty},
        'sources': source_hashes,
        'pdf': {'sha256': actual_hash, 'bytes': actual_size,
                'page_count': receipt['page_count'],
                'normalized_text_sha256': receipt['normalized_text_sha256']},
        'font_inventory': {'count': count,
                           'sha256': hashlib.sha256(fonts.encode('utf-8')).hexdigest()},
        'tool_versions': versions,
        'source_date_epoch': receipt.get('source_date_epoch'),
        'cross_environment_reproducible': False,
        'institutional_acceptance': False,
        'accessibility_conformance': 'unverified',
        'human_review': 'not-assessed',
    }


def validate_output_path(path: Path) -> Path:
    root = ROOT.absolute()
    target = path.absolute()
    allowed = root / 'build' / 'verification'
    if '..' in target.parts or target.parent != allowed:
        raise ProvenanceError('output path must be an immediate child of build/verification without traversal')
    if target.name != 'provenance.json':
        raise ProvenanceError('only provenance.json is allowed; verifier inputs must never be overwritten')
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ProvenanceError('refusing symlinked evidence path')
    if target.exists() and not target.is_file():
        raise ProvenanceError('evidence target is not a file')
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/verification/provenance.json'))
    args = parser.parse_args(argv)
    path = validate_output_path(ROOT / args.output)
    path.write_text('{"schema_version":1,"status":"running"}\n',encoding='utf-8')
    try:
        verified_revision = run_fresh_verify(ROOT)
        result = create_manifest(ROOT)
        if result['source']['revision'] != verified_revision or result['source']['tracked_dirty']:
            raise ProvenanceError('source checkout changed after fresh verification')
        result['source_binding'] = 'fresh-verified-clean-checkout'
    except (OSError, ProvenanceError) as exc:
        path.write_text('{"schema_version":1,"status":"failed"}\n',encoding='utf-8')
        print(f'Provenance not established: {type(exc).__name__}',file=sys.stderr)
        return 1
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('Provenance evidence emitted (not a reproducibility or compliance certificate)')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
