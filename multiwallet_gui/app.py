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
    QPlainTextEdit,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtGui import QIcon

import sys

from buidl.hd import HDPrivateKey
from buidl.mnemonic import WORD_LOOKUP, WORD_LIST


def _clean_submisission(string):
    # TODO: more advanced regex
    return string.replace("  ", " ").strip()


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
        vbox = QVBoxLayout()

        self.firstWordsLabel = QLabel("Enter first 23 words of your seed:")
        self.firstWordsEdit = QPlainTextEdit()
        self.firstWordsEdit.setPlaceholderText("zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo")

        self.firstWordsSubmitButton = QPushButton("Calculate Seed")
        self.firstWordsSubmitButton.clicked.connect(self.process_submit)

        vbox.addWidget(self.firstWordsLabel)
        vbox.addWidget(self.firstWordsEdit)
        vbox.addWidget(self.firstWordsSubmitButton)

        self.setLayout(vbox)

    def _error(self, main_text=None, informative_text=None, detailed_text=None):
            msg = QMessageBox()
            # msg.setWindowTitle("foo")  # TODO: this doesn't work
            if main_text:
                msg.setText(main_text)
            msg.setIcon(QMessageBox.Critical)
            if informative_text:
                msg.setInformativeText(informative_text)

            if detailed_text:
                msg.setDetailedText(detailed_text)
            msg.exec_()


    def process_submit(self):
        first_words = _clean_submisission(self.firstWordsEdit.toPlainText())
        fw_num = len(first_words.split())
        if fw_num not in (11, 14, 17, 20, 23):
            # TODO: 11, 14, 17, or 20 word seed phrases also work but this is not documented as it's for advanced users
            return self._error(
                    main_text="Invalid seed phrase",
                    informative_text="Seed phrase must be 23 words",
                    detailed_text=f"you entered {fw_num} words",
                    )

        wordlist_errors = []
        for cnt, word in enumerate(first_words.split()):
            if word not in WORD_LOOKUP:
                wordlist_errors.append([cnt + 1, word])
        if wordlist_errors:
            # self.text.config(fg='red') (need a UI to turn this off on typing)
            detailed_text = [
                "The following are not valid:",
            ]
            detailed_text.extend([f"  word #{x[0]} {x[1]}" for x in wordlist_errors])
            return self._error(
                main_text="Non BIP39 words",
                informative_text="Your seed phrase can ONLY contain BIP39 words",
                detailed_text="\n".join(detailed_text),
            )



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
