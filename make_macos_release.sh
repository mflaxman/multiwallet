#! /usr/bin/env bash

# TODO: script must be run by system python, pyinstaller doesn't play nicely with pyenv :(

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

black --check .
flake8 .

# Python stuff
python3 --version
# Install virtualenv (if not installed)
# python3 -m pip uninstall virtualenv -y
python3 -m pip install virtualenv
# Create virtualenv and install our software inside it
python3 -m virtualenv .venv3
source .venv3/bin/activate
# python3 -m pip uninstall pyinstaller -y
python3 -m pip install -r requirements.txt
python3 -m pip install --editable .
python3 -m pip install pyinstaller
python3 -m pip freeze

# Compile MacOs app
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
# https://askubuntu.com/questions/1028924/how-do-i-use-seconds-inside-a-bash-script
hrs=$(( SECONDS/3600 ))
mins=$(( (SECONDS-hrs*3600)/60))
secs=$(( SECONDS-hrs*3600-mins*60 ))
printf 'Time spent: %02d:%02d:%02d\n' $hrs $mins $secs
