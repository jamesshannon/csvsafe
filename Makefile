VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
PYINSTALLER := $(VENV)/bin/pyinstaller

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
	$(PYINSTALLER) packaging/csvsafe.spec

clean:
	rm -rf build/ dist/ *.egg-info $(VENV)
