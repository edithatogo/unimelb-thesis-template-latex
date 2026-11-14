PYTHON ?= python3

.DEFAULT_GOAL := build

.PHONY: build clean test verify replay

build:
	latexmk -g -lualatex -file-line-error -halt-on-error -interaction=nonstopmode -no-shell-escape example/Thesis.tex

clean:
	latexmk -C example/Thesis.tex

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	$(PYTHON) scripts/verify.py

replay: test
	$(PYTHON) scripts/verify.py --replay
