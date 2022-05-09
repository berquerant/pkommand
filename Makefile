dev: clean check test

.PHONY: clean
clean:
	@pipenv run tox -e clean

.PHONY: check
check: # Run lints, format checks.
	@pipenv run tox -e black,isort,flake8,mypy -p 2

.PHONY: checkdoc
checkdoc:
	@pipenv run tox -e pydocstyle

.PHONY: test
test:  # Run tests.
	@pipenv run tox -e py310,coverage-report

.PHONY: fix
fix:  # Format py sources.
	@pipenv run black $(BLACK_TARGET)
	@pipenv run isort $(ISORT_TARGET)
