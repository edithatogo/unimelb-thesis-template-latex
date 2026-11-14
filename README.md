# University of Melbourne Thesis Template

This is a modernized version of the University of Melbourne PhD thesis template. It uses modern LaTeX packages and includes a worked example. Authors must check current university submission requirements; successful template verification does not establish institutional compliance.

## Features

* Modern Packages: Utilizes `biblatex` for bibliography, `fontspec` for Unicode fonts, `geometry` for page layout, `hyperref` for PDF features, `microtype` for typography, and more.
* Structured Example: A comprehensive `example/` directory showcasing common thesis elements like figures, tables, equations, and code listings.
* Optional Scientific Authoring: A separate [scientific extension](docs/scientific-authoring.md) provides advanced mathematics, algorithms, PGFPlots, flexible tables and structured summaries, with its own synthetic rendered-output validation.
* Automated Build: Includes a `.latexmkrc` file for automated compilation with `lualatex` and `biber`.
* Verification: Clean builds check PDF structure, rendered content, bibliography, glossary and cross-references; behavioral tests exercise the verifier.
* Clear Customization: Well-commented class file (`template/Thesis.cls`) and example files.
* CI/CD Integration: Automated verification, workflow linting, dependency review, privacy scanning and tag-only releases; formatting remains opt-in.
* Thesis Metadata: Examples include ORCID support and declarations, subject to the author's institutional review.

## Compiled Example

A compiled PDF example is available for immediate download:

* **[Thesis-example.pdf](Thesis-example.pdf)** - Complete compiled thesis example in the repository root
* **[example/Thesis-compiled.pdf](example/Thesis-compiled.pdf)** - Same file in the example directory

These committed examples illustrate formatting and structure. They are not proof that the current source passes verification; use the newly generated PDF for that review.

## Requirements

* A full LaTeX distribution, such as [TeX Live](https://www.tug.org/texlive/), [MiKTeX](https://miktex.org/), or [MacTeX](https://www.tug.org/mactex/).
* LuaLaTeX, `latexmk`, `biber`, and `makeglossaries`: For compilation and reference material (usually included with full TeX distributions).
* Python 3.10 or newer, GNU Make, `qpdf`, and Poppler utilities (`pdfinfo` and `pdftotext`): For running `make verify`.
* Python 3.11 or newer and the hash-pinned development requirements: Only for the optional local `make coverage` command; see [CONTRIBUTING.md](CONTRIBUTING.md#verifier-coverage).
* `chktex` (optional): For linting LaTeX code.
* `latexindent` (optional): For formatting LaTeX code.

## Usage

### Local Compilation

1. Open a terminal in the repository root (the directory containing `.latexmkrc`).
2. Build and validate the example:

    ```bash
    make verify
    ```

    This runs verifier tests, compiles `example/Thesis.tex` in a fresh temporary directory with shell escape disabled, and validates the PDF and reference material. The retained PDF is `build/verification/Thesis.pdf`, with selected diagnostics and `report.json` alongside it. Compilation or validation errors fail the command. Temporary build files are cleaned automatically.
3. Run `make test` for the fast verifier suite without TeX. Run `make replay` for two fresh builds that must produce the same normalized text and page count in the same toolchain; replay evidence is retained in `build/replay/`.

For the optional scientific-authoring fixture, run `make science-check` (Python tests plus a fresh LuaLaTeX build and PDF checks). The base verifier remains unchanged.

The output assertions describe this repository's example. Update them deliberately when adapting the example to a different thesis. They do not replace visual review or institutional requirements. See [quality checks](docs/quality-checks.md) for verification and coverage limits.

### Usage with Overleaf

1. **Upload:** Download this template as a ZIP file and upload it to your Overleaf project.
2. **Compiler:** In the Overleaf menu, set the "LaTeX engine" to `LuaLaTeX`.
3. **Main Document:** Ensure the main document is set to `example/Thesis.tex`. Overleaf usually detects this, but you can confirm in the project settings.
4. **Compile:** Click "Recompile".

### Linting (Optional)

To lint the LaTeX code (from the repository root):

```bash
chktex **/*.tex # Or specify individual files
```

### Formatting (Optional)

To format the LaTeX code (from the repository root, this will modify files in place):

```bash
latexindent -w -s -y **/*.tex # Or specify individual files
```

## Customization

The primary files you'll edit are within the `example/` directory:

* **`example/Thesis.tex`**: This is the main file for your thesis.
  * Set metadata like `\title`, `\authors`, `\degree`, `\university`, `\department`, `\school`, `\supervisor`, etc. here.
  * Include or exclude chapters and preamble sections.
* **`example/Chapters/`**: Contains the individual chapters of your thesis (e.g., `Chapter1.tex`). Add, remove, or rename files here and update their inclusion in `example/Thesis.tex`.
* **`example/Preamble/`**: Contains pre-main matter content like `Abstract.tex`, `Acknowledgements.tex`, `Declaration.tex`, and `Preface.tex`. Edit these to add your own content.
* **`example/Bibliography.bib`**: This is your bibliography file. Add your references here in BibTeX format.
* **`example/Figures/`**: Place your figure files (PDF, PNG, JPG, EPS) in this directory.

Advanced customization can be done in `template/Thesis.cls`:

* **Fonts:**
  * The template uses `fontspec` and defaults to Latin Modern fonts.
  * To change fonts, uncomment and modify the relevant lines in `template/Thesis.cls` (search for `\usepackage{fontspec}`). For example:

    ```latex
    % \setmainfont{Times New Roman}
    % \setsansfont{Arial}
    % \setmonofont{Courier New}
    ```

  * Ensure the fonts you choose are available on your system or on Overleaf.
* **Bibliography Style:**
  * The template uses `biblatex` with `style=numeric-comp`.
  * You can change the style in `template/Thesis.cls` by modifying the `\usepackage[backend=biber, style=...] {biblatex}` line. Common styles include `authoryear`, `apa`, `mla`, etc. Refer to the `biblatex` documentation for available styles and options.
* **`hyperref` Colors:**
  * Link colors are defined in `template/Thesis.cls` within the `\usepackage[...]{hyperref}` command. You can change `linkcolor`, `citecolor`, and `urlcolor` (e.g., to `black` for printing if desired).
* **Other Class Options:** The `Thesis.cls` file is commented to explain various sections and package choices. For deeper modifications, refer to the comments and the documentation of the respective LaTeX packages.

## Troubleshooting

* **Compilation Errors:**
  * Check `build/verification/report.json` and the retained `Thesis.log` for details. A failure before the compiler creates a log may appear only in the report or command output.
  * Ensure all necessary packages are installed.
  * Run `make verify` from the repository root so the class, bibliography and input paths resolve consistently; latexmk manages the necessary compilation passes.
* **Fonts Not Found:** If you've changed fonts via `fontspec`, ensure they are correctly named and installed on your system (or supported by Overleaf).
* **Bibliography Issues:**
  * Ensure `biber` is run correctly (automated by `latexmk`).
  * Check `Bibliography.bib` for syntax errors in your BibTeX entries.
  * Ensure all cited keys exist in your `.bib` file.
* **EPS Figures:** If you have issues with EPS figures, ensure `epstopdf` is working or pre-convert them to PDF. The template comments out `\usepackage{epstopdf}` in `Thesis.cls` as `lualatex` often handles this, but it can be re-enabled if needed.

## LaTeX Best Practices

This template attempts to follow several LaTeX best practices:

* **Vector Graphics:** Use vector graphics (PDF, EPS) for diagrams, plots, and illustrations whenever possible to ensure they scale without loss of quality. Use raster graphics (PNG, JPG) for photographs.
* **`booktabs` for Tables:** Use the `booktabs` package for professional-looking tables (avoid vertical rules, use horizontal rules sparingly). See `example/Chapters/Chapter1.tex`.
* **`microtype` for Typography:** The `microtype` package is included to improve the visual appearance of text (e.g., character protrusion, font expansion).
* **`csquotes` for Quotations:** The `csquotes` package provides context-sensitive quotation marks and is recommended for use with `biblatex`.
* **Semantic Markup:** Use commands and environments for their semantic meaning (e.g., `\emph` for emphasis, specific theorem environments) rather than just for visual styling.
* **Separate Content and Presentation:** Keep your main content in `.tex` files within `Chapters/` and `Preamble/`. Styling is primarily handled by `template/Thesis.cls`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for validation and PDF review, and [repository controls](docs/repository-controls.md) for automated gates and outstanding settings acceptance.

## License

The template is licensed under the [MIT License](LICENSE). University branding assets remain subject to the University's own rights and branding rules. Authors are responsible for documents produced with the template.
