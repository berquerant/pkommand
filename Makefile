.PHONY: dev
dev:
	@pipenv run check
	@pipenv run test

.PHONY: fix
fix:  # Format py sources.
	@pipenv run black $(BLACK_TARGET)
	@pipenv run isort $(ISORT_TARGET)
