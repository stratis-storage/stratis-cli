PYTEST_OPTS = --verbose

TOX=tox

.PHONY: lint
lint:
	$(TOX) -c tox.ini -e lint

.PHONY: fmt
fmt:
	black .

.PHONY: fmt-travis
fmt-travis:
	black . --check

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
	py.test-3 ${PYTEST_OPTS} ./tests/whitebox/integration

unittest-tests:
	py.test-3 ${PYTEST_OPTS} ./tests/whitebox/unittest

coverage:
	python3 -m coverage --version
	python3 -m coverage run --timid --branch -m pytest ./tests/whitebox/integration
	python3 -m coverage run --timid --branch -a -m pytest ./tests/whitebox/unittest
	python3 -m coverage run --timid --branch -a -m pytest ./tests/whitebox/monkey_patching/test_keyboard_interrupt.py
	python3 -m coverage html --include="./src/*"
	python3 -m coverage report -m --fail-under=93 --show-missing --include="./src/*"

keyboard-interrupt-test:
	py.test-3 ${PYTEST_OPTS} ./tests/whitebox/monkey_patching/test_keyboard_interrupt.py

test-travis:
	$(TOX) -c tox.ini -e test
