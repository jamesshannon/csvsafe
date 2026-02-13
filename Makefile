install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

build:
	pyinstaller packaging/csvsafe.spec

clean:
	rm -rf build/ dist/ *.egg-info
