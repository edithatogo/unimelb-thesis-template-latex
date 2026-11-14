PYTHON ?= python3

.PHONY: test verify replay

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	$(PYTHON) scripts/verify.py

replay: test
	$(PYTHON) scripts/verify.py --replay
