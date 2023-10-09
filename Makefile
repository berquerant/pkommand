.PHONY: dev
dev:
	@pipenv run check
	@pipenv run test

.PHONY: fix
fix:  # Format py sources.
	@pipenv run black setup.py pkommand tests doc
	@pipenv run ruff setup.py pkommand tests doc
