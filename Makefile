UNITTEST_OPTS = --verbose

.PHONY: lint
lint:
	./check.py check.py
	./check.py bin/stratis
	./check.py src/stratis_cli
	./check.py tests/blackbox/stratis_cli_cert.py
	./check.py tests/blackbox/stratisd_cert.py
	./check.py tests/blackbox/testlib
	./check.py tests/whitebox

.PHONY: fmt
fmt:
	isort --recursive check.py setup.py bin/stratis src tests
	black ./bin/stratis .

.PHONY: fmt-travis
fmt-travis:
	isort --recursive --diff --check-only check.py setup.py bin/stratis src tests
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

.PHONY: archive
archive:
	git archive --output=./stratis_cli.tar.gz HEAD

.PHONY: upload-release
upload-release:
	python setup.py register sdist upload

.PHONY: docs
api-docs:
	sphinx-apidoc-3 -P -F -o api src/stratis_cli
	sphinx-build-3 -b html api api/_build/html

dbus-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --top-level-directory ./tests/whitebox --start-directory ./tests/whitebox/integration > /dev/null

unittest-tests:
	python3 -m unittest discover ${UNITTEST_OPTS} --start-directory ./tests/whitebox/unittest

.PHONY: coverage-no-html
coverage-no-html:
	python3 -m coverage --version
	python3 -m coverage run --timid --branch -m unittest discover --quiet --top-level-directory ./tests/whitebox --start-directory ./tests/whitebox/integration > /dev/null
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

test-travis: unittest-tests

.PHONY: yamllint
yamllint:
	yamllint --strict .travis.yml
