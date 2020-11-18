#! /usr/bin/env bash

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

ABOUT_COPY = """
<h2>
  Welcome to Multiwallet
</h2>
<p>
  Multiwallet generates seeds (wallets), validates receive addresses (before getting a payment), and signs transactions (to spend your bitcoin).
  It is designed for use on an airgapped/eternally quarantined machine.
</p>
<p>
  Multiwallet is free open-source software with no warranty.
  <b>Use at your own risk.</b>
</p>
<hr/>
<p>
  Good:
  <ul>
    <li>Free and open-source</li>
    <li>Native support for multisig segwit transactions via PSBT</li>
    <li>1-click downloadable binary for MacOS. Windows/Linux coming soon</li>
  </ul>
</p>
<p>
  Bad:
  <ul>
    <li>Software-wallets are less secure than hardware wallets for non-experts</li>
    <li>Stateless wallets <a href="https://btcguide.github.io/known-issues/verify-receive-address">can't keep track of your cosigners</a> (but you can)</li>
    <li>Early software. QR code support is currently limited for example.</li>
  </ul>
</p>
<p>
  Read more about Multiwallet <a href="https://github.com/mflaxman/multiwallet/">on GitHub</a>.
  Our community Telegram group can be found at <a href="https://t.me/multiwallet">https://t.me/multiwallet</a>.
</p>
"""


class AboutTab(QWidget):
    TITLE = "About"
    HOVER = "Info about Multiwallet GUI"

    def __init__(self):
        super().__init__()

        vbox = QVBoxLayout(self)

        self.mainLabel = QLabel(ABOUT_COPY)
        self.mainLabel.setWordWrap(True)

        vbox.addWidget(self.mainLabel)
        vbox.setAlignment(Qt.AlignTop)

        self.setLayout(vbox)
