test:  # Run tests, lints, format checks.
	pipenv run tox

fix:  # Format py sources.
	pipenv run black $(BLACK_TARGET)
	pipenv run isort $(ISORT_TARGET)
