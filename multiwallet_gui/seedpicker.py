#! /usr/bin/env bash

from multiwallet_gui.helper import (
    BITCOIN_NETWORK_TOOLTIP,
    BITCOIN_TESTNET_TOOLTIP,
    BITCOIN_MAINNET_TOOLTIP,
    create_qr_icon,
    _clean_submisission,
    _msgbox_err,
    qr_dialog,
)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from buidl.hd import HDPrivateKey
from buidl.mnemonic import WORD_LOOKUP, WORD_LIST


def _get_all_valid_checksum_words(first_words, first_match=True):
    # TODO: move to buidl library
    to_return = []
    for word in WORD_LIST:
        try:
            HDPrivateKey.from_mnemonic(first_words + " " + word)
            if first_match:
                return [word], ""
            to_return.append(word)
        except KeyError as e:
            # We have a word in first_words that is not in WORD_LIST
            return [], "Invalid BIP39 Word: {}".format(e.args[0])
        except ValueError:
            pass

    return to_return, ""


class SeedpickerTab(QWidget):
    TITLE = "Seedpicker"
    HOVER = (
        "<b>Protect yourself against a bad random number generator.</b> "
        "Pick 23 words of your seed phrase and Seedpicker will calculate the last word."
    )

    def __init__(self):
        super().__init__()

        vbox = QVBoxLayout(self)

        self.firstWordsLabel = QLabel("<b>First 23 Words of Your Seed Phrase</b>")
        self.firstWordsLabel.setToolTip(
            "Pull words out of a hat so you don't have to trust a random number generator."
        )
        self.firstWordsEdit = QPlainTextEdit("")
        self.firstWordsEdit.setPlaceholderText(
            "Something like this:\n\nzoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo"
        )

        # Network toggle
        # https://www.tutorialspoint.com/pyqt/pyqt_qradiobutton_widget.htm
        self.button_label = QLabel("<b>Bitcoin Network</b>")
        self.button_label.setToolTip(BITCOIN_NETWORK_TOOLTIP)

        hbox = QHBoxLayout(self)

        self.mainnet_button = QRadioButton("Mainnet")
        self.mainnet_button.setToolTip(BITCOIN_MAINNET_TOOLTIP)
        self.mainnet_button.setChecked(False)

        self.testnet_button = QRadioButton("Testnet")
        self.testnet_button.setToolTip(BITCOIN_TESTNET_TOOLTIP)
        self.testnet_button.setChecked(True)

        for widget in self.mainnet_button, self.testnet_button:
            hbox.addWidget(widget)
        hbox.setAlignment(Qt.AlignCenter)

        self.firstWordsSubmitButton = QPushButton("Calculate Full Seed")
        self.firstWordsSubmitButton.clicked.connect(self.process_submit)

        self.privResultsLabel = QLabel("")
        self.privResultsLabel.setToolTip(
            "Write the full mnemonic <b>offline</b> and store in a <b>secure</b> place."
            "<br/><br/>"
            "This represents your bitcoin <i>private</i> keys."
        )
        self.privResultsEdit = QPlainTextEdit("")
        self.privResultsEdit.setReadOnly(True)
        self.privResultsEdit.setHidden(True)

        self.pubResultsLabel = QLabel("")
        self.pubResultsLabel.setToolTip(
            "For export to your online computer and eventaully other hardware wallets."
            "<br/><br/>"
            "This represents your bitcoin <i>public</i> keys, which are neccesary-but-not-sufficient to spend your bitcoin."
        )
        self.pubResultsROEdit = QPlainTextEdit("")
        self.pubResultsROEdit.setReadOnly(True)
        self.pubResultsROEdit.setHidden(True)

        self.qrButton = QPushButton()
        self.qrButton.setText("QR")
        self.qrButton.setToolTip(
            "For transmitting to your online computer via webcam."
            "<br/><br/>"
            "This is a great way to preserve your airgap."
        )
        self.qrButton.setHidden(True)
        self.qrButton.clicked.connect(self.make_qr_popup)

        for widget in (self.firstWordsLabel, self.firstWordsEdit, self.button_label):
            vbox.addWidget(widget)

        vbox.addLayout(hbox)

        for widget in (
            self.firstWordsSubmitButton,
            self.privResultsLabel,
            self.privResultsEdit,
            self.pubResultsLabel,
            self.pubResultsROEdit,
            self.qrButton,
        ):
            vbox.addWidget(widget)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.privResultsEdit.clear()
        self.privResultsEdit.setHidden(True)
        self.privResultsLabel.setText("")
        self.pubResultsROEdit.clear()
        self.pubResultsROEdit.setHidden(True)
        self.pubResultsLabel.setText("")
        self.qrButton.setHidden(True)
        self.qrButton.setText("")
        # TODO: why setText and not hide?

        first_words = _clean_submisission(self.firstWordsEdit.toPlainText())
        fw_num = len(first_words.split())
        if fw_num not in (11, 14, 17, 20, 23):
            # TODO: 11, 14, 17, or 20 word seed phrases also work but this is not documented as it's for advanced users
            return _msgbox_err(
                main_text="Seed Phrase Must Be 23 Words",
                informative_text=f"you entered {fw_num} words",
            )

        wordlist_errors = []
        for cnt, word in enumerate(first_words.split()):
            if word not in WORD_LOOKUP:
                wordlist_errors.append([cnt + 1, word])
        if wordlist_errors:
            return _msgbox_err(
                main_text="Invalid BIP39 Word(s)",
                informative_text="\n".join(
                    [f"Word #{x[0]}: {x[1]}" for x in wordlist_errors]
                ),
            )

        valid_checksum_words, err_str = _get_all_valid_checksum_words(
            first_words, first_match=True
        )
        if err_str:

            return _msgbox_err(
                main_text="Error calculating checksum word",
                informative_text=err_str,
            )

        self.IS_TESTNET = self.testnet_button.isChecked()
        if self.IS_TESTNET:
            PATH = "m/48'/1'/0'/2'"
            SLIP132_VERSION_BYTES = "02575483"
        else:
            # Mainnet
            PATH = "m/48'/0'/0'/2'"
            SLIP132_VERSION_BYTES = "02aa7ed3"

        last_word = valid_checksum_words[0]
        hd_priv = HDPrivateKey.from_mnemonic(first_words + " " + last_word)

        priv_to_display = [
            f"Last Word: {last_word}",
            f"Full {fw_num + 1} word mnemonic (including last word): {first_words + ' ' + last_word}",
        ]
        pub_to_display = [
            "[{}{}]{}".format(
                hd_priv.fingerprint().hex(),
                PATH.replace("m", "").replace("'", "h"),
                hd_priv.traverse(PATH).xpub(
                    version=bytes.fromhex(SLIP132_VERSION_BYTES)
                ),
            ),
        ]

        self.privResultsLabel.setText("<b>SECRET INFO</b>")
        self.privResultsEdit.setHidden(False)
        self.privResultsEdit.appendPlainText("\n".join(priv_to_display))

        pubkey_results_text = (
            f"<b>PUBLIC KEY INFO</b> - {'testnet' if self.IS_TESTNET else 'mainnet'}"
        )
        self.pubResultsLabel.setText(pubkey_results_text)
        self.pubResultsROEdit.setHidden(False)
        self.pubResultsROEdit.appendPlainText("\n".join(pub_to_display))

        self.qrButton.setHidden(False)
        self.qrButton.setText("QR")
        self.qrButton.setIcon(create_qr_icon())

    def make_qr_popup(self):
        qr_dialog(
            qwidget=self,
            qr_text=self.pubResultsROEdit.toPlainText(),
            window_title=self.pubResultsLabel.text(),
        )
