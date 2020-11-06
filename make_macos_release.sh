#! /usr/bin/env bash

# Verbose printing
set -o xtrace

# Hackey timer
date

# Abandon if anything errors
set -e;

# Remove old files
rm -rfv .venv3/
rm -rfv dist/
rm -rfv build/
rm -rfv multiwallet.egg-info/
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

# Install virtualenv
python3 -m pip install virtualenv
python3 -m virtualenv .venv3
source .venv3/bin/activate
python3 setup.py install
pip freeze

# Install pyinstaller (TODO: install this at system level outside of venv?)
pip install pyinstaller
pyinstaller multiwallet_gui/app.py --clean --windowed --name=multiwallet

# Create DMG
cd dist/
create-dmg \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  multiwallet.dmg \
  "multiwallet.app/"
cd ..

# Hackey timer
date
