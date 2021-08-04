dev: clean check test

.PHONY: clean
clean:
	@pipenv run tox -e clean

.PHONY: check
check: check-manifest  # Run lints, format checks.
	@pipenv run tox -e black,isort,flake8,mypy,pydocstyle -p 2

.PHONY: check-manifest
check-manifest:  # Run check-manifest
	@pipenv run tox -e check-manifest

.PHONY: test
test:  # Run tests.
	@pipenv run tox -e py38,coverage-report

.PHONY: fix
fix:  # Format py sources.
	@pipenv run black $(BLACK_TARGET)
	@pipenv run isort $(ISORT_TARGET)
