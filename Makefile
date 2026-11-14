.PHONY: build verify clean

build:
	latexmk -g -lualatex -file-line-error -halt-on-error -interaction=nonstopmode -no-shell-escape example/Thesis.tex

verify: build
	test -s example/out/Thesis.pdf
	qpdf --check example/out/Thesis.pdf
	pdfinfo example/out/Thesis.pdf
	pdftotext example/out/Thesis.pdf example/out/Thesis.txt
	grep -q '[^[:space:]]' example/out/Thesis.txt

clean:
	latexmk -C example/Thesis.tex
