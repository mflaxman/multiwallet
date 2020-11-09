from helper import _clean_submisission, _msgbox_err
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)


TEST_PSBT = """
{ "label": "Any Recovery", "blockheight": 1863986, "descriptor": "wsh(sortedmulti(1,[c7d0648a\/48h\/1h\/0h\/2h]tpubDEpefcgzY6ZyEV2uF4xcW2z8bZ3DNeWx9h2BcwcX973BHrmkQxJhpAXoSWZeHkmkiTtnUjfERsTDTVCcifW6po3PFR1JRjUUTJHvPpDqJhr\/0\/*,[12980eed\/48h\/1h\/0h\/2h]tpubDEkXGoQhYLFnYyzUGadtceUKbzVfXVorJEdo7c6VKJLHrULhpSVLC7fo89DDhjHmPvvNyrun2LTWH6FYmHh5VaQYPLEqLviVQKh45ufz8Ae\/0\/*,[3a52b5cd\/48h\/1h\/0h\/2h]tpubDFdbVee2Zna6eL9TkYBZDJVJ3RxGYWgChksXBRgw6y6PU1jWPTXUqag3CBMd6VDwok1hn5HZGvg6ujsTLXykrS3DwbxqCzEvWoT49gRJy7s\/0\/*,[f7d04090\/48h\/1h\/0h\/2h]tpubDF7FTuPECTePubPXNK73TYCzV3nRWaJnRwTXD28kh6Fz4LcaRzWwNtX153J7WeJFcQB2T6k9THd424Kmjs8Ps1FC1Xb81TXTxxbGZrLqQNp\/0\/*))#tatkmj5q" } 
""".strip()


class ReceiveTab(QWidget):
    TITLE = "Receive"

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.descriptorLabel = QLabel("Desciptor")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.descriptorEdit = QPlainTextEdit(TEST_PSBT)
        self.descriptorEdit.setPlaceholderText("wsh(sortedmulti(2,...))#...")

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
