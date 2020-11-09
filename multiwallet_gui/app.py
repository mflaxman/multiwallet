from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QTabWidget,
    QVBoxLayout,
)

import sys

from seedpicker import SeedpickerTab
from receive import ReceiveTab
from send import SendTab


class MultiwalletApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiwallet - Stateless PSBT Multisig Wallet - ALPHA VERSION TESTNET ONLY")

        vbox = QVBoxLayout()
        tabWidget = QTabWidget()

        for tab in (SeedpickerTab, ReceiveTab, SendTab):
            tab_obj = tab()
            tabWidget.addTab(tab_obj, tab_obj.TITLE)

        vbox.addWidget(tabWidget)

        self.setLayout(vbox)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_app = MultiwalletApp()
    my_app.show()
    app.exec()
