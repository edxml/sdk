.PHONY: all dependencies dist pypi pypi-test doc check test coverage coverage-report dist-clean clean

all: dependencies dist doc check test clean

dependencies:
	@echo "Installing dependencies:"
	python3 -m pip install --upgrade pip setuptools wheel
	pip3 install flake8 pytest
	pip3 install -r requirements.txt

dist: dist-clean
	pip3 install wheel
	python3 setup.py sdist bdist_wheel

pypi-test: dist
	# NOTE: twine will read TWINE_USERNAME and TWINE_PASSWORD from environment
	pip3 install twine
	twine check dist/*
	@echo "Uploading to PyPI (test instance):"
	-twine upload --repository testpypi dist/*

pypi: dist
	# NOTE: twine will read TWINE_USERNAME and TWINE_PASSWORD from environment
	pip3 install twine
	twine check dist/*
	@echo "Uploading to PyPI:"
	twine upload dist/*

doc:
	pip3 install -e .[doc]
	python3 setup.py build_sphinx

check:
	@echo "Checking your code..."
	@python3 -m flake8 --max-line-length=120 edxml/ tests/ && echo "Well done. Your code is in shiny style!"

test: dependencies
	@echo "Running tests:"
	@python3 -m pytest tests -W ignore::DeprecationWarning

coverage: dependencies
	@echo "Gathering coverage data:"
	@python3 -m coverage run --omit '*/venv/*' -m pytest tests -W ignore::DeprecationWarning

coverage-report:
	coverage html

dist-clean:
	rm -rf build dist edxml.egg-info

clean: dist-clean
	find . -name '*.py[co]' -delete
	rm -rf .coverage htmlcov
