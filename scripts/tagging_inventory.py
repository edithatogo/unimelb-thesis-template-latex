#!/usr/bin/env python3
"""A source-level LaTeX tagging compatibility inventory, never a PDF/UA test.

Package statuses are a dated snapshot of an upstream mutable inventory.
Even all-compatible statuses cannot establish tagged PDF conformance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = 'https://latex3.github.io/tagging-project/tagging-status/'
REVIEW_DATE = '2026-11-17'
SOURCE_TYPE = 'mutable-upstream-status-list'
KNOWN = {
    'caption': 'currently-incompatible',
    'subcaption': 'currently-incompatible',
    'algorithm2e': 'currently-incompatible',
    'pgfplots': 'currently-incompatible',
    'pdfpages': 'currently-incompatible',
    'biblatex': 'partially-compatible',
    'tikz': 'partially-compatible',
    'tcolorbox': 'partially-compatible',
    'amsmath': 'partially-compatible',
    'glossaries': 'unchecked',
    'fancyhdr': 'compatible',
    'longtable': 'compatible',
}
CMD = re.compile(r'\\(?:RequirePackage|usepackage)\b(?:\s*\[[^]]*\])?\s*\{([^{}]+)\}', re.DOTALL)
TAG = re.compile(r'\\(?:RequirePackage|usepackage)\b')


class InventoryError(ValueError):
    """Source inventory cannot prove what packages are loaded."""


def strip_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        end = len(line)
        for index, char in enumerate(line):
            if char != '%':
                continue
            slashes = 0
            for position in range(index - 1, -1, -1):
                if line[position] != '\\':
                    break
                slashes += 1
            if slashes % 2 == 0:
                end = index
                break
        lines.append(line[:end])
    return '\n'.join(lines)


def extract_packages(source: str) -> set[str]:
    cleaned = strip_comments(source)
    matches = list(CMD.finditer(cleaned))
    if len(matches) != len(TAG.findall(cleaned)):
        raise InventoryError('Unparseable package declaration: review source changes')
    packages = set()
    for match in matches:
        for package in match.group(1).split(','):
            package = package.strip()
            if not re.fullmatch('[A-Za-z0-9_./+-]+', package):
                raise InventoryError('Invalid package identifier in source')
            packages.add(package)
    return packages


def report(base_packages: set[str], science_packages: set[str]) -> dict:
    all_packages = set(base_packages) | set(science_packages)
    if not all_packages:
        raise InventoryError('No active package declarations found')
    observed = {name: KNOWN.get(name, 'unreviewed') for name in sorted(all_packages)}
    incompatible = sorted(name for name, status in observed.items() if status in {'currently-incompatible','no-support'})
    conditional = sorted(name for name, status in observed.items() if status == 'partially-compatible')
    unreviewed = sorted(name for name, status in observed.items() if status in {'unchecked', 'unreviewed'})
    return {
        'schema_version': 1, 'status': 'tagging-unqualified',
        'source_url': SOURCE_URL, 'source_type': SOURCE_TYPE,
        'review_date': REVIEW_DATE,
        'direct_package_count': len(all_packages),
        'base_packages': sorted(base_packages), 'optional_science_packages': sorted(science_packages),
        'observed_statuses': observed,
        'incompatible': incompatible, 'conditional': conditional, 'unreviewed': unreviewed,
        'pdf_ua_qualified': False,
        'pdf_a_qualified': False,
        'requires_compiler_package_version_check': True,
        'requires_machine_validator': True,
        'requires_human_accessibility_review': True,
        'claim_boundary': 'source-level triage only; no rendered tagged-PDF conformance was tested',
    }


def inventory(base: Path, science: Path) -> dict:
    for path in (base, science):
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise InventoryError('Missing or unsafe LaTeX package source')
    return report(extract_packages(base.read_text(encoding='utf-8')),
                  extract_packages(science.read_text(encoding='utf-8')))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=ROOT/'template/Thesis.cls')
    parser.add_argument('--science',type=Path,default=ROOT/'template/thesis-science.sty')
    args = parser.parse_args(argv)
    try:
        result = inventory(args.base,args.science)
    except (OSError,UnicodeError,InventoryError) as exc:
        print(f'Accessibility-readiness inventory blocked: {type(exc).__name__}',file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
