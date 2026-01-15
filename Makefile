ISORT_MODULES = setup.py bin/stratis src tests

UNITTEST_OPTS = --verbose
#
# Ignore bandit B404 errors. Any import of the subprocess module causes this
# error. We know what we are doing when we import that module and do not
# need to be warned.
BANDIT_SKIP = --skip B404

PYLINT_DISABLE = --disable=fixme

.PHONY: lint
lint:
	pylint setup.py ${PYLINT_DISABLE}
	pylint bin/stratis ${PYLINT_DISABLE}
	pylint src/stratis_cli --disable=duplicate-code ${PYLINT_DISABLE} --ignore=_introspect.py
	pylint tests --disable=duplicate-code ${PYLINT_DISABLE}
	bandit setup.py ${BANDIT_SKIP}
	bandit bin/stratis ${BANDIT_SKIP}
	# Ignore B101 errors. We do not distribute optimized code, i.e., .pyo
	# files in Fedora, so we do not need to have concerns that assertions
	# are removed by optimization.
	bandit --recursive ./src ${BANDIT_SKIP},B101
	bandit --recursive ./tests ${BANDIT_SKIP}
	pyright

.PHONY: fmt
fmt:
	isort ${ISORT_MODULES}
	black ./bin/stratis .

.PHONY: fmt-ci
fmt-ci:
	isort --diff --check-only ${ISORT_MODULES}
	black ./bin/stratis . --check

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
	yamllint --strict .github/workflows/*.yml .packit.yaml

.PHONY: package
package:
	(umask 0022; python -m build; python -m twine check --strict ./dist/*)
