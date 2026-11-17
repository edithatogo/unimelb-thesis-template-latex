#!/usr/bin/env python3
"""Conservative UMTHESIS rights plans and synthetic textual leak checks.

No PDF, archive, redaction or permission approval is performed. This is a
fail-closed *preflight* over already normalized canonical metadata, not an
independent rights schema or a publication-authorisation mechanism.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]*$')
SAFE_PATH = re.compile(r'^[A-Za-z0-9._/-]+$')
STATUSES = {'owned', 'licensed', 'permission-required', 'excluded'}
SURFACES = {'pdf_text', 'pdf_metadata', 'bookmarks', 'attachments'}


class RightsError(ValueError):
    """Invalid or insufficient rights evidence prevents publication projection."""


def _items(value: object, name: str) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise RightsError(f'{name} must be a list of objects')
    return value


def _id(value: object) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise RightsError('invalid resource identifier')
    return value


def _path(value: object) -> str:
    if (not isinstance(value, str) or not SAFE_PATH.fullmatch(value)
            or value.startswith('/') or '//' in value
            or any(segment in ('.', '..') for segment in value.split('/'))):
        raise RightsError('unsafe resource path')
    return value


def projection_plan(configuration: dict, audience: str = 'public') -> dict:
    """Plan—not enact—a full or public rights projection.

    An opaque permission_ref is not proof that permission was granted. Inclusion
    cannot be authorized until a separately reviewed decision and real artifact
    checks have occurred. All resource rights must be explicitly categorized.
    """
    if not isinstance(configuration, dict) or configuration.get('contract_version') != '1.0.0':
        raise RightsError('unsupported canonical contract version')
    if audience not in ('full', 'public'):
        raise RightsError('unsupported distribution audience')
    if audience == 'public' and configuration.get('purpose') != 'deposit-public':
        raise RightsError('public output requires deposit-public purpose')
    if audience == 'full' and configuration.get('purpose') not in ('deposit-full', 'examination'):
        raise RightsError('full output requires a qualified full or examination purpose')
    metadata = configuration.get('metadata')
    if not isinstance(metadata, dict):
        raise RightsError('missing normalized metadata')
    resources = {}
    paths = set()
    for item in _items(metadata.get('resources', []), 'resources'):
        if set(item) - {'id', 'kind', 'path', 'description'}:
            raise RightsError('unexpected resource fields')
        identifier = _id(item.get('id'))
        path = _path(item.get('path'))
        if identifier in resources or path in paths:
            raise RightsError('duplicate resource ID or path')
        paths.add(path)
        resources[identifier] = item
    rights = {}
    for item in _items(metadata.get('rights', []), 'rights'):
        if set(item) - {'resource_id', 'status', 'permission_ref'}:
            raise RightsError('unexpected rights fields')
        identifier = _id(item.get('resource_id'))
        if identifier in rights:
            raise RightsError('duplicate rights record')
        if item.get('status') not in STATUSES:
            raise RightsError('unknown rights status')
        if 'permission_ref' in item:
            _id(item['permission_ref'])
        rights[identifier] = item
    if set(rights) != set(resources):
        raise RightsError('missing rights or rights for unknown resources')
    for group in ('publications', 'creative_outputs'):
        for item in _items(metadata.get(group, []), group):
            references = item.get('resource_ids', [])
            if not isinstance(references, list):
                raise RightsError('invalid resource references')
            for reference in references:
                if _id(reference) not in resources:
                    raise RightsError('unknown referenced resource')
    include, exclude, holds = [], [], []
    for identifier in sorted(resources):
        status = rights[identifier]['status']
        if status == 'owned':
            include.append(identifier)
        elif status == 'excluded':
            exclude.append(identifier)
        else:
            holds.append({'resource_id': identifier, 'reason':
                          'human-permission-review-required' if status == 'licensed'
                          else 'permission-not-established'})
    return {
        'contract_version': '1.0.0', 'audience': audience,
        'status': 'blocked' if holds else 'plan-only',
        'include_candidate_ids': include, 'excluded_ids': exclude, 'holds': holds,
        'requires_output_scan': True, 'release_authorized': False,
        'human_permission_review': 'required' if holds else 'not-assessed',
        'scope': 'rights-preflight-only',
    }


def scan_text_surfaces(surfaces: dict[str, str], sentinels: list[str]) -> dict:
    """Require synthetic restricted tokens absent from *supplied* text surfaces.

    Not a binary PDF/ZIP scan, image recognition, or accessible-tag validation.
    Consumers must independently extract all surfaces from the final artifacts.
    """
    if (not isinstance(surfaces, dict) or set(surfaces) != SURFACES
            or any(not isinstance(value, str) for value in surfaces.values())
            or not surfaces['pdf_text'].strip()):
        raise RightsError('incomplete final artifact text surfaces')
    if (not isinstance(sentinels, list) or not sentinels
            or any(not isinstance(value, str) or not value.strip() for value in sentinels)):
        raise RightsError('invalid sentinel list')
    normal = lambda text: unicodedata.normalize('NFKC', text).casefold()
    tokens = [normal(item) for item in sentinels]
    if len(tokens) != len(set(tokens)):
        raise RightsError('duplicate restricted sentinels')
    for name, text in surfaces.items():
        flattened = normal(text)
        if any(token in flattened for token in tokens):
            raise RightsError(f'restricted sentinel remains in {name}')
    return {
        'status': 'text-surfaces-cleared', 'scanned_surfaces': sorted(SURFACES),
        'release_authorized': False, 'scope': 'supplied-text-surfaces-only',
        'image_and_accessibility_review': 'unexecuted',
    }


def _unique_json(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise RightsError('duplicate JSON key')
        value[key] = item
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configuration', type=Path, help='canonical normalized synthetic JSON')
    parser.add_argument('--audience', choices=('public', 'full'), default='public')
    args = parser.parse_args(argv)
    try:
        if args.configuration.is_symlink() or not args.configuration.is_file():
            raise RightsError('missing or symlinked configuration')
        with args.configuration.open('rb') as source:
            content = source.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise RightsError('configuration too large')
        configuration = json.loads(content, object_pairs_hook=_unique_json,
                                   parse_constant=lambda value: (_ for _ in ()).throw(RightsError('nonfinite JSON')))
        plan = projection_plan(configuration, args.audience)
    except (OSError, ValueError) as error:
        print(f'Rights preflight failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(plan, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
