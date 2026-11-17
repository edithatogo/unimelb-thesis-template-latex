PYTHON ?= python3

.PHONY: test verify replay coverage science-check contract-check

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

# Qualify the optional scientific authoring pack without changing base verification.
science-check: test
	$(PYTHON) -m scripts.verify_science

# Consume the canonical UMTHESIS v1 bundle from an immutable checkout.
# The base thesis verifier remains independently runnable offline.
CONTRACT_UPSTREAM ?= build/contract-upstream
contract-check: test
	$(PYTHON) -m scripts.contract_consumer --upstream $(CONTRACT_UPSTREAM)
