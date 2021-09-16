UNITTEST_OPTS = --verbose

.PHONY: lint
lint:
	pylint setup.py
	pylint bin/stratis
	pylint src/stratis_cli --disable=duplicate-code --ignore=_introspect.py
	pylint tests/whitebox --disable=duplicate-code

.PHONY: fmt
fmt:
	isort setup.py bin/stratis src tests
	black ./bin/stratis .

.PHONY: fmt-ci
fmt-ci:
	isort --diff --check-only setup.py bin/stratis src tests
	black ./bin/stratis . --check

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
	python3 -m coverage run --timid --branch -a -m unittest --quiet tests.whitebox.monkey_patching.test_keyboard_interrupt.KeyboardInterruptTestCase
	python3 -m coverage run --timid --branch -a -m unittest --quiet tests.whitebox.monkey_patching.test_stratisd_version.StratisdVersionTestCase
	python3 -m coverage report -m --fail-under=100 --show-missing --include="./src/*"

.PHONY: coverage
coverage: coverage-no-html
	python3 -m coverage html --include="./src/*"

keyboard-interrupt-test:
	python3 -m unittest ${UNITTEST_OPTS} tests.whitebox.monkey_patching.test_keyboard_interrupt.KeyboardInterruptTestCase

stratisd-version-test:
	python3 -m unittest ${UNITTEST_OPTS} tests.whitebox.monkey_patching.test_stratisd_version.StratisdVersionTestCase

.PHONY: sim-tests
sim-tests: dbus-tests keyboard-interrupt-test stratisd-version-test

.PHONY: all-tests
all-tests: unittest-tests sim-tests

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml
