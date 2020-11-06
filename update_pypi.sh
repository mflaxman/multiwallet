#! /usr/bin/env bash

# Verbose printing
set -o xtrace

# Hackey timer
date

# Abandon if anything errors
set -e;

# Tests
black --check .
flake8 .
# pytest -v

# Safety
git push

# Package
python3 setup.py sdist bdist_wheel
# Upload to PyPI
python3 -m pip install --upgrade twine
python3 -m twine upload dist/*

# Cleanup
rm -rf dist/
rm -rf multiwallet.egg-info/
rm -rf build/

# Hackey timer
date
