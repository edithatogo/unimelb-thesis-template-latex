# Build from the repository root. Verification overrides the output directory
# with a fresh temporary directory, so checked-in PDFs cannot satisfy the gate.
$pdf_mode = 4;
$lualatex = 'lualatex -no-shell-escape %O %S';
$biber = 'biber %O %S';
ensure_path('TEXINPUTS', 'template//');
@default_files = ('example/Thesis.tex');
$out_dir = 'example/out';

# Run glossary tools explicitly, without enabling TeX shell escape.
use File::Basename;
add_cus_dep('glo', 'gls', 0, 'build_glossaries');
add_cus_dep('acn', 'acr', 0, 'build_glossaries');
sub build_glossaries {
  my ($base) = @_;
  return system('makeglossaries', '-d', dirname($base), basename($base));
}

# Formatting is an explicit authoring operation, never a build side effect.
