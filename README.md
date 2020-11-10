# THIS REPOSITORY COMES WITH ZERO GUARANTEES! USE AT YOUR OWN RISK!

GUI version of CLI [multiwallet](https://twitter.com/mflaxman/status/1321503036724989952).

#### Seedpicker
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/seedpicker.png)

#### Recieve
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/receive.png)

#### Send
![](https://raw.githubusercontent.com/mflaxman/multiwallet/main/images/send.png)

## Install

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
* Allow user to select limit/offset for receive address verfication
* Add tooltips/explainers
* Mainnet/testnet toggle
* Add QR code generation on send/receive
* Support arbitrary paths
* Test/release on multiple OS
* Better form handling/validation
* Add libsec
* Add webcam on receive/send
* Sign release
* Dark mode
* Reproducible build

## Maintainer Notes - Make a Release

Downloadable MacOS binary:
```
$ time ./make_macos_release.sh 
```

Update PyPI:
```
$ time ./update_pypi.sh
```
