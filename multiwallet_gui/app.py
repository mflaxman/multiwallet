from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
)
from PyQt5.QtGui import QIcon

import sys


class MultiwalletApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiwallet - Stateless PSBT Multisig Wallet")

        vbox = QVBoxLayout()
        tabWidget = QTabWidget()

        for tab in (SeedpickerTab, ReceiveTab, SendTab):
            tab_obj= tab()
            tabWidget.addTab(tab_obj, tab_obj.TITLE)

        vbox.addWidget(tabWidget)

        self.setLayout(vbox)


class SeedpickerTab(QWidget):
    TITLE = "Seedpicker"

    def __init__(self):
        super().__init__()
        firstWordsLabel = QLabel("Seed Phrase:")
        firstWordsEdit = QLineEdit("zoo zoo zoo...")

        vbox = QVBoxLayout()
        vbox.addWidget(firstWordsLabel)
        vbox.addWidget(firstWordsEdit)
        self.setLayout(vbox)


class ReceiveTab(QWidget):
    TITLE = "Receive"
    
    def __init__(self, parent=None):
        super(ReceiveTab, self).__init__(parent)

        descriptorLabel = QLabel("Desciptor:")
        descriptorEdit = QLineEdit("...")

        vbox = QVBoxLayout()
        vbox.addWidget(descriptorLabel)
        vbox.addWidget(descriptorEdit)
        self.setLayout(vbox)


class SendTab(QWidget):
    TITLE = "Send"

    def __init__(self, parent=None):
        super(SendTab, self).__init__(parent)

        psbtLabel = QLabel("PSBT To Sign:")
        psbtEdit = QLineEdit("...")

        vbox = QVBoxLayout()
        vbox.addWidget(psbtLabel)
        vbox.addWidget(psbtEdit)
        self.setLayout(vbox)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_app = MultiwalletApp()
    my_app.show()
    app.exec()
