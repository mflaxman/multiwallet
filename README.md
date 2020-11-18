# THIS REPOSITORY COMES WITH ZERO GUARANTEES! USE AT YOUR OWN RISK!

GUI version of CLI [multiwallet](https://twitter.com/mflaxman/status/1321503036724989952).

#### Seedpicker
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/seedpicker.png)

#### Recieve
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/receive.png)

#### Send
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/send.png)

## Install

### Pillow (for QR Codes)

Mac:
```
$ brew install libtiff libjpeg webp little-cms2
```

Ubuntu:
```
$ sudo apt-get install python3-dev python3-setuptools apt-get install libtiff5-dev libjpeg8-dev libopenjp2-7-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev
```

For more see instructions [here](https://pillow.readthedocs.io/en/latest/installation.html)

### Multiwallet

#### Easy
Downloadable binary link here (MacOS only):  
<https://github.com/mflaxman/multiwallet/releases>

#### Medium
```bash
$ pip3 install multiwallet
$ multiwallet_gui
```

#### Advanced
```bash
git clone https://github.com/mflaxman/multiwallet.git
cd multiwallet
python3 -m virtualenv .venv3
source .venv3/bin/activate
python3 setup.py develop
python multiwallet_gui/app.py 
```

## Roadmap:
* Add support for choosing other checksum words
* Add detailed TX view (not just summary) to UI
* Add QR encode on address verification
* Add QR gifs
* Add units (sats/BTC) toggle
* Test/release on multiple OS
* Better form handling/validation
* Support arbitrary paths
* Add libsec
* Add webcam on receive/send for qrdecode
* Sign binaries
* Dark mode
* Reproducible build

## Maintainer Notes for Releases

Make a new release branch:
```bash
$ git checkout -b v0.x.x
```

Commit your changes, being sure to bump the version number in `setup.py`.

Basic tests:
```bash
$ black --check . && flake8 .
```

Make a downloadable MacOS binary to upload to GitHub:
```
$ ./make_macos_release.sh 
```

Go to [GitHub release page](https://github.com/mflaxman/multiwallet/releases/new) and use tag version `v0.x.x` and target `v0.x.x` (target is the branch name which is independent of the tag).
Write a title, description, and drag the binary from the previous step.
Hit `Publish release`.

Update PyPI:
```
$ ./update_pypi.sh
```

Merge into main:
```
$ git checkout main
$ git merge v0.x.x
```
TODO: better to `merge` into `main` first?
