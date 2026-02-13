VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
PYINSTALLER := $(VENV)/bin/pyinstaller
PYINSTALLER_CONFIG_DIR := .pyinstaller
VERSION := $(shell $(PYTHON) -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" 2>/dev/null)
PACKAGE_ZIP := dist/CSVSafe-$(VERSION)-macos.zip

.PHONY: install test test-integration lint build package clean

$(VENV)/bin/python:
	python3.11 -m venv $(VENV)

install: $(VENV)/bin/python
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test: $(VENV)/bin/python
	$(PYTEST) tests/ -v -m "not integration"

test-integration: build
	CSVSAFE_RUN_GUI_TESTS=1 $(PYTEST) tests/integration/ -v -m integration

lint: $(VENV)/bin/python
	$(RUFF) check src/ tests/

build: $(VENV)/bin/python
	PYINSTALLER_CONFIG_DIR=$(PYINSTALLER_CONFIG_DIR) $(PYINSTALLER) -y packaging/csvsafe.spec

package: build
	rm -f $(PACKAGE_ZIP)
	cd dist && zip -r CSVSafe-$(VERSION)-macos.zip CSVSafe.app

clean:
	rm -rf build/ dist/ *.egg-info $(VENV) $(PYINSTALLER_CONFIG_DIR)
