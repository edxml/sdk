# Make file for creating the PyPI package and generating sphinx docs

.PHONY: all dependencies dist doc check test clean

all: dependencies dist doc check test clean

dependencies:
	@echo "Installing dependencies:"
	pip2 install -r requirements.txt

dist:
	python setup.py sdist
	python setup.py sdist upload

doc:
	pip install -e .[doc]
	python setup.py build_sphinx

check:
	@echo "Checking your code..."
	@python2 -m flake8 --max-line-length=120 && echo "Well done. Your code is in shiny style!"

test: dependencies
	@echo "Running tests:"
	@python2 -m pytest

clean:
	find . -name '*.py[co]' -delete

