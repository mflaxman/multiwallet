from helper import _clean_submisission, _msgbox_err
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)


class SendTab(QWidget):
    TITLE = "Send"

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.psbtLabel = QLabel("Partially Signed Bitcoin Transaction (PSBT) in Base64")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.psbtEdit = QPlainTextEdit(
            "air air air air air air air air air air air air air air air air air air air air air air air"
        )
        self.psbtEdit.setPlaceholderText("deadbeef")

        self.psbtSubmitButton = QPushButton("Decode Transaction")
        self.psbtSubmitButton.clicked.connect(self.process_submit)

        self.psbtResultsLabel = QLabel("")
        self.psbtResultEdit = QPlainTextEdit("")
        self.psbtResultEdit.setReadOnly(True)
        self.psbtResultEdit.setHidden(True)

        vbox.addWidget(self.psbtLabel)
        vbox.addWidget(self.psbtEdit)
        vbox.addWidget(self.psbtSubmitButton)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.psbtResultEdit.clear()
        self.psbtResultEdit.setHidden(True)
        self.psbtResultsLabel.setText("")
        # TODO: why setText and not hide? # FIXME

        return _msgbox_err(
            main_text="Not implemented",
        )

        self.psbtResultsLabel.setText("PSBT To Broadcast")
        self.psbtResultEdit.setHidden(False)
        self.psbtResultEdit.appendPlainText("\n".join("FOO"))
