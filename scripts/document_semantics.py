"""Rendered-page assertions for an explicitly described synthetic document.

This is an observation adapter, not a second metadata schema or a claim of
institutional, accessibility or archival conformance.
"""
from __future__ import annotations


def _normalise(text: str) -> str:
    return ' '.join(text.split())


def validate_document_semantics(
    pdfinfo: str, extracted_text: str, expected: dict[str, str],
) -> dict[str, int]:
    """Validate metadata retention and physical section order, not ToC mentions.

    Page indices are one-based physical pages from Poppler form-feed boundaries.
    Expected values must be plain, already-decoded PDF text, not TeX source.
    """
    fields = ('title', 'author', 'degree', 'submission_date', 'department', 'school')
    for field in (*fields, 'bibliography_content', 'appendix_content'):
        value = expected.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Missing or blank document expectation: {field}')

    metadata: dict[str, str] = {}
    for line in pdfinfo.splitlines():
        key, separator, value = line.partition(':')
        if separator and key in ('Title', 'Author'):
            if key in metadata:
                raise ValueError(f'Duplicate PDF metadata field: {key}')
            metadata[key] = _normalise(value)
    for key, field in (('Title', 'title'), ('Author', 'author')):
        if metadata.get(key) != _normalise(expected[field]):
            raise ValueError(f'PDF metadata does not match expected {field}')

    raw_pages = extracted_text.split('\f')
    pages = [_normalise(page) for page in raw_pages]
    title_page = pages[0]
    locations = [title_page.find(_normalise(expected[field])) for field in fields]
    if any(position < 0 for position in locations):
        raise ValueError('Required metadata missing from physical title page')
    if locations != sorted(locations) or len(set(locations)) != len(locations):
        raise ValueError('Incorrect title page metadata order')

    def section(heading: str, content: str) -> int:
        matches = [
            index for index, raw in enumerate(raw_pages)
            if heading in [_normalise(line) for line in raw.splitlines()]
            and _normalise(content) in pages[index]
        ]
        if len(matches) != 1:
            raise ValueError(f'Expected unique {heading.lower()} section with rendered content')
        return matches[0]

    abstract = section('Abstract', expected['title'])
    if abstract == 0 or _normalise(expected['author']) not in pages[abstract]:
        raise ValueError('Required title/author missing from separate abstract page')
    declaration = section('Declaration of Authorship', expected['title'])
    if not abstract < declaration or _normalise(expected['author']) not in pages[declaration]:
        raise ValueError('Required title/author missing from following declaration page')
    bibliography = section('Bibliography', expected['bibliography_content'])
    appendix = section('An Appendix', expected['appendix_content'])
    if not declaration < bibliography < appendix:
        raise ValueError('Expected abstract, bibliography, appendix in physical page order')
    return {
        'title_page': 1, 'abstract_page': abstract + 1,
        'declaration_page': declaration + 1,
        'bibliography_page': bibliography + 1, 'appendix_page': appendix + 1,
    }
