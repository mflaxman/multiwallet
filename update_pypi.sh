#! /usr/bin/env bash

# Verbose printing
set -o xtrace

# Abandon if anything errors
set -e;

# Remove old files
rm -rf .venv3/
rm -rf dist/
rm -rf build/
rm -rf multiwallet.egg-info/
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

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
rm -rfv dist/
rm -rfv multiwallet.egg-info/
rm -rfv build/

# Hackey timer
# https://askubuntu.com/questions/1028924/how-do-i-use-seconds-inside-a-bash-script
hrs=$(( SECONDS/3600 ))
mins=$(( (SECONDS-hrs*3600)/60))
secs=$(( SECONDS-hrs*3600-mins*60 ))
printf 'Time spent: %02d:%02d:%02d\n' $hrs $mins $secs
