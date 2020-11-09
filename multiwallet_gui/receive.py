from helper import _clean_submisission, _msgbox_err
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)


class ReceiveTab(QWidget):
    TITLE = "Receive"

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.descriptorLabel = QLabel("Desciptor")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.descriptorEdit = QPlainTextEdit(
            "air air air air air air air air air air air air air air air air air air air air air air air"
        )
        self.descriptorEdit.setPlaceholderText(
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo"
        )

        self.descriptorSubmitButton = QPushButton("Derive Addresses")
        self.descriptorSubmitButton.clicked.connect(self.process_submit)

        self.addrResultsLabel = QLabel("")
        self.addrResultsEdit = QPlainTextEdit("")
        self.addrResultsEdit.setReadOnly(True)
        self.addrResultsEdit.setHidden(True)

        vbox.addWidget(self.descriptorLabel)
        vbox.addWidget(self.descriptorEdit)
        vbox.addWidget(self.descriptorSubmitButton)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.addrResultsEdit.clear()
        self.addrResultsEdit.setHidden(True)
        self.addrResultsLabel.setText("")
        # TODO: why setText and not hide? # FIXME

        return _msgbox_err(
            main_text="Not implemented",
        )

        self.addrResultsLabel.setText("Multisig Addresses")
        self.addrResultsEdit.setHidden(False)
        self.addrResultsEdit.appendPlainText("\n".join("FOO"))
