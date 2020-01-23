# Make file for creating the PyPI package and generating sphinx docs

.PHONY: all dependencies dist doc check test clean

all: dependencies dist doc check test clean

dependencies:
	@echo "Installing dependencies:"
	pip3 install -r requirements.txt

dist:
	python3 setup.py sdist
	python3 setup.py sdist upload

doc:
	pip3 install -e .[doc]
	python3 setup.py build_sphinx

check:
	@echo "Checking your code..."
	@python3 -m flake8 --max-line-length=120 && echo "Well done. Your code is in shiny style!"

test: dependencies
	@echo "Running tests:"
	@python3 -m pytest

clean:
	find . -name '*.py[co]' -delete

