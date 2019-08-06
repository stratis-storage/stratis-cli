PYTEST_OPTS = -rsx

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
	PYTHONPATH=src pyreverse ${PYREVERSE_OPTS} --project="stratis-cli" src/stratis_cli
	mv classes_stratis-cli.pdf _pyreverse
	mv packages_stratis-cli.pdf _pyreverse

.PHONY: archive
archive:
	git archive --output=./stratis_cli.tar.gz HEAD

.PHONY: upload-release
upload-release:
	python setup.py register sdist upload

.PHONY: docs
docs:
	cd doc/_build/html; zip -r ../../../docs *

dbus-tests:
	py.test-3 ${PYTEST_OPTS} ./tests/whitebox
