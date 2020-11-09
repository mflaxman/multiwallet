#!/usr/bin/env python

from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class TabDialog(QDialog):
    def __init__(self, fileName, parent=None):
        super(TabDialog, self).__init__(parent)

        fileInfo = QFileInfo(fileName)

        tabWidget = QTabWidget()
        tabWidget.addTab(SeedpickerTab(fileInfo), "Seedpicker")
        tabWidget.addTab(ReceiveTab(fileInfo), "Receive")
        tabWidget.addTab(SendTab(fileInfo), "Send")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        self.setLayout(mainLayout)

        self.setWindowTitle("Multiwallet - Stateless PSBT Multisig Wallet")


class SeedpickerTab(QWidget):
    def __init__(self, fileInfo, parent=None):
        super(SeedpickerTab, self).__init__(parent)

        firstWordsLabel = QLabel("Seed Phrase:")
        firstWordsEdit = QLineEdit("zoo zoo zoo...")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(firstWordsLabel)
        mainLayout.addWidget(firstWordsEdit)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class ReceiveTab(QWidget):
    def __init__(self, fileInfo, parent=None):
        super(ReceiveTab, self).__init__(parent)

        descriptorLabel = QLabel("Desciptor:")
        descriptorEdit = QLineEdit("...")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(descriptorLabel)
        mainLayout.addWidget(descriptorEdit)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class SendTab(QWidget):
    def __init__(self, fileInfo, parent=None):
        super(SendTab, self).__init__(parent)

        psbtLabel = QLabel("PSBT To Sign:")
        psbtEdit = QLineEdit("...")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(psbtLabel)
        mainLayout.addWidget(psbtEdit)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)

    if len(sys.argv) >= 2:
        fileName = sys.argv[1]
    else:
        fileName = "."

    tabdialog = TabDialog(fileName)
    tabdialog.show()
    sys.exit(app.exec_())
