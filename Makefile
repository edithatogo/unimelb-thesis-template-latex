PYTHON ?= python3

.PHONY: test verify replay coverage

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	$(PYTHON) scripts/verify.py

replay: test
	$(PYTHON) scripts/verify.py --replay

coverage:
	mkdir -p build/coverage
	$(PYTHON) -m coverage run -m unittest discover -s tests -v
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage xml
