PYTHON := python3
PIP := $(PYTHON) -m pip
CONFIG ?= config.txt

.PHONY: all install run debug clean lint lint-strict test build

all: run

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

build:
	$(PYTHON) -c "from setuptools import build_meta; build_meta.build_wheel('.'); build_meta.build_sdist('.')"
	rm -rf build *.egg-info

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist *.egg-info
