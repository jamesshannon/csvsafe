VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
PYINSTALLER := $(VENV)/bin/pyinstaller
PYINSTALLER_CONFIG_DIR := .pyinstaller

.PHONY: install test lint build clean

$(VENV)/bin/python:
	python3.11 -m venv $(VENV)

install: $(VENV)/bin/python
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test: $(VENV)/bin/python
	$(PYTEST) tests/ -v

lint: $(VENV)/bin/python
	$(RUFF) check src/ tests/

build: $(VENV)/bin/python
	PYINSTALLER_CONFIG_DIR=$(PYINSTALLER_CONFIG_DIR) $(PYINSTALLER) -y packaging/csvsafe.spec

clean:
	rm -rf build/ dist/ *.egg-info $(VENV) $(PYINSTALLER_CONFIG_DIR)
