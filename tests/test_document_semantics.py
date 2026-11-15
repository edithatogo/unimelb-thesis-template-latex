"""Synthetic extraction cases; no compiler or institutional acceptance implied."""
import unittest
from scripts.document_semantics import validate_document_semantics

EXPECTED = {
    'title': 'Persistent Metadata Fixture', 'author': 'Example Author',
    'degree': 'Doctor of Philosophy', 'submission_date': 'January 2025',
    'department': 'Example Department', 'school': 'Example Faculty',
    'bibliography_content': 'The TeXbook', 'appendix_content': 'Synthetic appendix body.',
}
INFO = 'Title: Persistent Metadata Fixture\nAuthor: Example Author\nPages: 7\n'
PAGES = [
    'Persistent Metadata Fixture\nby\nExample Author\nDoctor of Philosophy\nJanuary 2025\nExample Department\nExample Faculty',
    'Abstract\nPersistent Metadata Fixture\nby Example Author\nSynthetic abstract body.',
    'Declaration of Authorship\nExample Author confirms the work titled Persistent Metadata Fixture.',
    'Contents\nAbstract 2\nBibliography 6\nAn Appendix 7',
    'Introduction\nSynthetic chapter body.',
    'Bibliography\nThe TeXbook',
    'Appendix A\nAn Appendix\nSynthetic appendix body.',
]

class DocumentSemanticsChecks(unittest.TestCase):
    def validate(self, pages=None, info=INFO, expected=None):
        return validate_document_semantics(info, '\f'.join(PAGES if pages is None else pages) + '\f', EXPECTED if expected is None else expected)

    def test_valid_document_reports_observed_page_positions(self):
        self.assertEqual(self.validate(), {'title_page': 1, 'abstract_page': 2, 'declaration_page': 3, 'bibliography_page': 6, 'appendix_page': 7})

    def test_pdf_metadata_matches_visible_title_and_author(self):
        for field, value in [('Title', EXPECTED['title']), ('Author', EXPECTED['author'])]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'metadata'):
                self.validate(info=INFO.replace(value, 'Wrong value'))

    def test_missing_or_duplicate_metadata_fails(self):
        for info in ['Pages: 7\n', INFO + 'Title: Conflicting title\n']:
            with self.subTest(info=info), self.assertRaisesRegex(ValueError, 'metadata'):
                self.validate(info=info)

    def test_each_title_page_field_is_required_on_that_page(self):
        for field in ('title', 'author', 'degree', 'submission_date', 'department', 'school'):
            pages = PAGES.copy()
            pages[0] = pages[0].replace(EXPECTED[field], '')
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'title page'):
                self.validate(pages)

    def test_submission_date_after_department_is_rejected(self):
        pages = PAGES.copy()
        pages[0] = pages[0].replace('January 2025\n', '') + '\nJanuary 2025'
        with self.assertRaisesRegex(ValueError, 'order'):
            self.validate(pages)

    def test_abstract_requires_title_and_author_after_titlepage_cleanup(self):
        for field in ('title', 'author'):
            pages = PAGES.copy()
            pages[1] = pages[1].replace(EXPECTED[field], '')
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'abstract'):
                self.validate(pages)

    def test_declaration_requires_persistent_title_and_author(self):
        for field in ('title', 'author'):
            pages = PAGES.copy()
            pages[2] = pages[2].replace(EXPECTED[field], '')
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'declaration'):
                self.validate(pages)

    def test_contents_entry_does_not_substitute_for_abstract(self):
        with self.assertRaisesRegex(ValueError, 'abstract'):
            self.validate(PAGES[:1] + PAGES[2:])

    def test_empty_initial_page_is_not_silently_removed(self):
        with self.assertRaisesRegex(ValueError, 'title page'):
            self.validate([''] + PAGES)

    def test_bibliography_must_precede_appendix_in_rendered_output(self):
        with self.assertRaisesRegex(ValueError, 'bibliography.*appendix'):
            self.validate(PAGES[:5] + [PAGES[6], PAGES[5]])

    def test_contents_or_headings_alone_do_not_prove_section_content(self):
        for index, marker in [(5, 'The TeXbook'), (6, 'Synthetic appendix body.')]:
            pages = PAGES.copy()
            pages[index] = pages[index].replace(marker, '')
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'content'):
                self.validate(pages)

    def test_duplicate_section_evidence_is_ambiguous(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.validate(PAGES + [PAGES[5]])

    def test_whitespace_wrapping_does_not_change_semantic_identity(self):
        pages = [p.replace('Persistent Metadata Fixture', 'Persistent\nMetadata Fixture') for p in PAGES]
        self.assertEqual(self.validate(pages)['abstract_page'], 2)

    def test_missing_or_blank_expectations_are_rejected(self):
        for value in ('', None):
            expected = dict(EXPECTED, title=value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'expectation'):
                self.validate(expected=expected)

if __name__ == '__main__':
    unittest.main()
