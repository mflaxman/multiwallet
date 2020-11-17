#! /usr/bin/env bash

import sys

from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QTabWidget,
    QVBoxLayout,
)

from multiwallet_gui.seedpicker import SeedpickerTab
from multiwallet_gui.receive import ReceiveTab
from multiwallet_gui.send import SendTab


class MultiwalletApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Multiwallet - Stateless PSBT Multisig Wallet - ALPHA VERSION"
        )
        self.setFixedWidth(800)

        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget()

        # Initialize tab screen
        self.seedpicker_tab = SeedpickerTab()
        self.receive_tab = ReceiveTab()
        self.send_tab = SendTab()

        # Add tabs
        for cnt, tab in enumerate(
            [self.seedpicker_tab, self.receive_tab, self.send_tab]
        ):
            self.tab_widget.addTab(tab, tab.TITLE)
            self.tab_widget.setTabToolTip(cnt, tab.HOVER)

        # Add tabs to widget
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)


def main():
    qapp = QApplication(sys.argv)
    my_app = MultiwalletApp()
    my_app.show()
    qapp.exec()


if __name__ == "__main__":
    main()
