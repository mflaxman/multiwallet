#! /usr/bin/env bash

from multiwallet_gui.helper import _clean_submisission, _msgbox_err
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
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

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.firstWordsLabel = QLabel("<b>First 23 Words of Your Seed</b>")
        self.firstWordsEdit = QPlainTextEdit("")
        self.firstWordsEdit.setPlaceholderText(
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo"
        )

        self.firstWordsSubmitButton = QPushButton("Calculate Full Seed")
        self.firstWordsSubmitButton.clicked.connect(self.process_submit)

        self.privResultsLabel = QLabel("")
        self.privResultsEdit = QPlainTextEdit("")
        self.privResultsEdit.setReadOnly(True)
        self.privResultsEdit.setHidden(True)

        self.pubResultsLabel = QLabel("")
        self.pubResultsEdit = QPlainTextEdit("")
        self.pubResultsEdit.setReadOnly(True)
        self.pubResultsEdit.setHidden(True)

        vbox.addWidget(self.firstWordsLabel)
        vbox.addWidget(self.firstWordsEdit)
        vbox.addWidget(self.firstWordsSubmitButton)
        vbox.addWidget(self.privResultsLabel)
        vbox.addWidget(self.privResultsEdit)
        vbox.addWidget(self.pubResultsLabel)
        vbox.addWidget(self.pubResultsEdit)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.privResultsEdit.clear()
        self.privResultsEdit.setHidden(True)
        self.privResultsLabel.setText("")
        self.pubResultsEdit.clear()
        self.pubResultsEdit.setHidden(True)
        self.pubResultsLabel.setText("")
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

        IS_TESTNET = True  # TESTNET ONLY FOR NOW
        if IS_TESTNET:
            PATH = "m/48'/1'/0'/2'"
            SLIP132_VERSION_BYTES = "02575483"
        else:
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

        self.privResultsLabel.setText("<b>SECRET INFO</b> - guard this very carefully")
        self.privResultsEdit.setHidden(False)
        self.privResultsEdit.appendPlainText("\n".join(priv_to_display))

        self.pubResultsLabel.setText(
            f"<b>PUBLIC KEY INFO</b> - {'Testnet' if IS_TESTNET else 'Mainnet'}"
        )
        self.pubResultsEdit.setHidden(False)
        self.pubResultsEdit.appendPlainText("\n".join(pub_to_display))
