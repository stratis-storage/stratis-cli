UNITTEST_OPTS = --verbose

.PHONY: lint
lint:
	ruff check bin/stratis
	ruff check
	pyright

.PHONY: fmt
fmt:
	ruff check --fix --select I bin/stratis
	ruff check --fix --select I
	ruff format

.PHONY: fmt-ci
fmt-ci:
	ruff check --select I bin/stratis
	ruff check --select I
	ruff format --check

.PHONY: check-typos
check-typos:
	typos

PYREVERSE_OPTS = --output=pdf
.PHONY: view
view:
	-rm -Rf _pyreverse
	mkdir _pyreverse
	pyreverse ${PYREVERSE_OPTS} --project="stratis-cli" src/stratis_cli
	mv classes_stratis-cli.pdf _pyreverse
	rm packages_stratis-cli.pdf
	pyreverse ${PYREVERSE_OPTS} --project="stratis-cli-errors" src/stratis_cli/_errors.py
	mv classes_stratis-cli-errors.pdf _pyreverse
	pyreverse ${PYREVERSE_OPTS} --project="test" tests/_misc.py -a 1
	mv classes_test.pdf _pyreverse

.PHONY: api-docs
api-docs:
	sphinx-apidoc-3 -P -F -o api src/stratis_cli
	sphinx-build-3 -b html api api/_build/html

dbus-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --top-level-directory ./tests --start-directory ./tests/integration

unit-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --start-directory ./tests/unit

.PHONY: coverage
coverage:
	python3 -m coverage run -p --timid --branch -m unittest discover --quiet --top-level-directory ./tests --start-directory ./tests/integration >& /dev/null
	python3 -m coverage run -p --timid --branch -m unittest discover --quiet --start-directory ./tests/unit

.PHONY: coverage-report
coverage-report:
	python3 -m coverage combine
	python3 -m coverage report -m --fail-under=100 --show-missing --include="./src/*"

.PHONY: coverage-html
coverage-html:
	python3 -m coverage combine
	python3 -m coverage html --include="./src/*"

.PHONY: all-tests
all-tests: unit-tests dbus-tests

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml .packit.yaml .yamllint.yaml

.PHONY: package
package:
	(umask 0022; python -m build; python -m twine check --strict ./dist/*)
