# Make file for creating the PyPI package and generating sphinx docs

.PHONY: all dist doc clean

all: dist doc clean

dist:
	python setup.py sdist
	python setup.py sdist upload

doc:
	pip install -e .[doc]
	python setup.py build_sphinx

clean:
	find . -name '*.py[co]' -delete

