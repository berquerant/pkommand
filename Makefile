.PHONY: dev
dev:
	@uvx tox run-parallel -m check --parallel-no-spinner --parallel-live
	@uvx tox run-parallel -m test --parallel-no-spinner --parallel-live

.PHONY: fix
fix: black ruff # Format py sources.

.PHONY: black
black:
	@uvx black setup.py pkommand tests doc

.PHONY: ruff
ruff:
	@uvx ruff setup.py pkommand tests doc
