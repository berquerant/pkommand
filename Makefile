.PHONY: dev
dev:
	@pipenv run check
	@pipenv run test

.PHONY: fix
fix: black ruff # Format py sources.

.PHONY: black
black:
	@pipenv run black setup.py pkommand tests doc

.PHONY: ruff
ruff:
	@pipenv run ruff setup.py pkommand tests doc
