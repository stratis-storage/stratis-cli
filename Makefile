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
	pylint tests/whitebox --disable=duplicate-code ${PYLINT_DISABLE}
	bandit setup.py ${BANDIT_SKIP}
	bandit bin/stratis ${BANDIT_SKIP}
	# Ignore B101 errors. We do not distribute optimized code, i.e., .pyo
	# files in Fedora, so we do not need to have concerns that assertions
	# are removed by optimization.
	bandit --recursive ./src ${BANDIT_SKIP},B101
	bandit --recursive ./tests ${BANDIT_SKIP}

.PHONY: fmt
fmt:
	isort setup.py bin/stratis src tests
	black ./bin/stratis .

.PHONY: fmt-ci
fmt-ci:
	isort --diff --check-only setup.py bin/stratis src tests
	black ./bin/stratis . --check

.PHONY: fmt-shell
fmt-shell:
	shfmt -l -w shell-completion/bash/stratis

.PHONY: fmt-shell-ci
fmt-shell-ci:
	shfmt -d shell-completion/bash/stratis

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
	pyreverse ${PYREVERSE_OPTS} --project="test-whitebox" tests/whitebox/_misc.py -a 1
	mv classes_test-whitebox.pdf _pyreverse

.PHONY: api-docs
api-docs:
	sphinx-apidoc-3 -P -F -o api src/stratis_cli
	sphinx-build-3 -b html api api/_build/html

dbus-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --top-level-directory ./tests/whitebox --start-directory ./tests/whitebox/integration

unittest-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --start-directory ./tests/whitebox/unittest

.PHONY: coverage-no-html
coverage-no-html:
	python3 -m coverage --version
	python3 -m coverage run --timid --branch -m unittest discover --quiet --top-level-directory ./tests/whitebox --start-directory ./tests/whitebox/integration >& /dev/null
	python3 -m coverage run --timid --branch -a -m unittest discover --quiet --start-directory ./tests/whitebox/unittest
	python3 -m coverage report -m --fail-under=100 --show-missing --include="./src/*"

.PHONY: coverage
coverage: coverage-no-html
	python3 -m coverage html --include="./src/*"

.PHONY: all-tests
all-tests: unittest-tests dbus-tests

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml .packit.yaml

.PHONY: legacy-package
legacy-package:
	python3 setup.py build
	python3 setup.py install
