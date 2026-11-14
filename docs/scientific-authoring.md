# Optional scientific authoring

The base class remains focused on thesis layout. Load `thesis-science` only if
algorithms, PGFPlots charts, flexible tables or the supplied summary boxes are
required. The extension is deliberately namespaced, synthetic and independent
of any candidate's research or institutional declarations.

```tex
% In the preamble, with TEXINPUTS including template/ as in .latexmkrc:
\usepackage{thesis-science}
```

Included facilities: `amsmath`/`mathtools`, `booktabs`, `tabularx`, `siunitx`,
`tikz`, `pgfplots` (qualified compatibility baseline 1.18), `algorithm2e`,
`pdfpages`, `pdflscape`, and three optional `tcolorbox` environments:
`thesistakehome`, `thesisplainlanguage`, `thesiskeyterms`.
Their standard environments remain available. The `examples/science-demo.tex`
fixture gives non-empirical, standalone examples of each group.

Run `make science-check` to execute all Python regression tests, compile the
fixture in a fresh temporary directory with LuaLaTeX and **no shell escape**,
and inspect the generated PDF for structure and independently extractable
rendered content. The PDF is a disposable validation artifact, not a thesis
submission. `make verify` retains its existing base-template contract.

## Explicit limits

* This optional package has not been qualified for PDF/UA or PDF/A. In particular,
  an imported PDF can have its own tag, licence, copyright and reading-order
  deficiencies. An accessible main document does not repair inaccessible imports.
* Mathematical semantics and alternative descriptions for plotted data are
  author responsibilities. A plotted curve is not accessible merely because it
  is drawn with TikZ/PGFPlots; supply a descriptive explanation and, when useful,
  an equivalent table.
* Algorithms and styled boxes are not automatically meaningful to assistive
  technologies. Perform semantic and human-accessibility review before claiming
  conformance. Those checks belong in the separate accessible-output profile.
* This package deliberately does not load `unicode-math` or `cleveref` globally:
  both can alter existing document semantics or conflict with class command
  names. Their introduction requires class-level compatibility tests.
* `pdfpages` is for legitimate, rights-cleared material. It does not validate
  permissions, signatures or the safety of public-release/redacted derivatives.
* Figures, equations and tables in the fixture are synthetic and make no claim
  of scientific validity.

An optional package is preferable to adding heavy scientific dependencies to
all documents, including those that do not use the corresponding features.
