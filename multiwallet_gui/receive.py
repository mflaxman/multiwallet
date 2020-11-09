import re
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)

from helper import _clean_submisission, _msgbox_err

from buidl.hd import HDPublicKey
from buidl.helper import sha256
from buidl.op import OP_CODE_NAMES_LOOKUP
from buidl.script import P2WSHScriptPubKey, WitnessScript


# TODO: package with libsec

def _re_pubkey_info_from_descriptor_fragment(fragment):
    xfp, path, xpub, idx = re.match(
        "\[([0-9a-f]+)\*?(.*?)\]([0-9A-Za-z]+).*([0-9]+?)",  # noqa: W605
        fragment,
    ).groups()
    return {
        "xfp": xfp,
        "path": path.replace("\\/", "/").lstrip("/"),
        "xpub": xpub,
        "idx": int(idx),
    }


def _get_pubkeys_info_from_descriptor(descriptor):
    re_results = re.findall("wsh\(sortedmulti\((.*)\)\)", descriptor)  # noqa: W605
    parts = re_results[0].split(",")
    quorum_m = int(parts.pop(0))
    quorum_n = len(parts)  # remaining entries are pubkeys with fingerprint/path
    assert 0 < quorum_m <= quorum_n

    pubkey_dicts = []
    for fragment in parts:
        pubkey_info = _re_pubkey_info_from_descriptor_fragment(fragment=fragment)
        parent_pubkey_obj = HDPublicKey.parse(pubkey_info["xpub"])
        pubkey_info["parent_pubkey_obj"] = parent_pubkey_obj
        pubkey_info["child_pubkey_obj"] = parent_pubkey_obj.child(
            index=pubkey_info["idx"]
        )
        pubkey_dicts.append(pubkey_info)

    # safety check
    all_pubkeys = [x["xpub"] for x in pubkey_dicts]
    assert (
        len(set([x[:4] for x in all_pubkeys])) == 1
    ), "ERROR: multiple conflicting networks in pubkeys: {}".format(all_pubkeys)

    xpub_prefix = all_pubkeys[0][:4]
    if xpub_prefix == "tpub":
        is_testnet = True
    elif xpub_prefix == "xpub":
        is_testnet = False
    else:
        raise Exception(f"Invalid xpub prefix: {xpub_prefix}")

    return {
        "is_testnet": is_testnet,
        "quorum_m": quorum_m,
        "quorum_n": quorum_n,
        "pubkey_dicts": pubkey_dicts,
    }


def _get_address(pubkey_dicts, quorum_m, quorum_n, index, is_testnet):
    sec_hexes_to_use = []
    for pubkey_dict in pubkey_dicts:
        leaf_xpub = pubkey_dict["child_pubkey_obj"].child(index=index)
        sec_hexes_to_use.append(leaf_xpub.sec().hex())

    commands = [OP_CODE_NAMES_LOOKUP["OP_{}".format(quorum_m)]]
    commands.extend([bytes.fromhex(x) for x in sorted(sec_hexes_to_use)])  # BIP67
    commands.append(OP_CODE_NAMES_LOOKUP["OP_{}".format(quorum_n)])
    commands.append(OP_CODE_NAMES_LOOKUP["OP_CHECKMULTISIG"])
    witness_script = WitnessScript(commands)
    redeem_script = P2WSHScriptPubKey(sha256(witness_script.raw_serialize()))
    return redeem_script.address(testnet=is_testnet)


def get_addresses(pubkey_dicts, quorum_m, quorum_n, limit, offset, is_testnet):
    # Create generator obj
    for cnt in range(limit):
        index = cnt + offset
        address = _get_address(
            pubkey_dicts=pubkey_dicts,
            quorum_m=quorum_m,
            quorum_n=quorum_n,
            index=index,
            is_testnet=is_testnet,
        )
        yield index, address


TEST_PSBT = """
{ "label": "Any Recovery", "blockheight": 1863986, "descriptor": "wsh(sortedmulti(1,[c7d0648a\/48h\/1h\/0h\/2h]tpubDEpefcgzY6ZyEV2uF4xcW2z8bZ3DNeWx9h2BcwcX973BHrmkQxJhpAXoSWZeHkmkiTtnUjfERsTDTVCcifW6po3PFR1JRjUUTJHvPpDqJhr\/0\/*,[12980eed\/48h\/1h\/0h\/2h]tpubDEkXGoQhYLFnYyzUGadtceUKbzVfXVorJEdo7c6VKJLHrULhpSVLC7fo89DDhjHmPvvNyrun2LTWH6FYmHh5VaQYPLEqLviVQKh45ufz8Ae\/0\/*,[3a52b5cd\/48h\/1h\/0h\/2h]tpubDFdbVee2Zna6eL9TkYBZDJVJ3RxGYWgChksXBRgw6y6PU1jWPTXUqag3CBMd6VDwok1hn5HZGvg6ujsTLXykrS3DwbxqCzEvWoT49gRJy7s\/0\/*,[f7d04090\/48h\/1h\/0h\/2h]tpubDF7FTuPECTePubPXNK73TYCzV3nRWaJnRwTXD28kh6Fz4LcaRzWwNtX153J7WeJFcQB2T6k9THd424Kmjs8Ps1FC1Xb81TXTxxbGZrLqQNp\/0\/*))#tatkmj5q" } 
""".strip()  # noqa: W605, W291





class ReceiveTab(QWidget):
    TITLE = "Receive"

    updateProgress = pyqtSignal(str)

    def _return_addr(self, string):
        print('called')
        # self.addrResultsEdit.setHidden(False)
        self.addrResultsEdit.appendPlainText(string)
        self.addrResultsEdit.show()

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.updateProgress.connect(self._return_addr)

        self.descriptorLabel = QLabel("Desciptor")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.descriptorEdit = QPlainTextEdit(TEST_PSBT)
        self.descriptorEdit.setPlaceholderText("wsh(sortedmulti(2,...))#...")

        self.descriptorSubmitButton = QPushButton("Derive Addresses")
        self.descriptorSubmitButton.clicked.connect(self.process_submit)

        self.addrResultsLabel = QLabel("Multisig Addresses")
        self.addrResultsEdit = QPlainTextEdit("")
        self.addrResultsEdit.setReadOnly(True)
        # self.addrResultsEdit.setHidden(True)

        vbox.addWidget(self.descriptorLabel)
        vbox.addWidget(self.descriptorEdit)
        vbox.addWidget(self.descriptorSubmitButton)
        vbox.addWidget(self.addrResultsLabel)
        vbox.addWidget(self.addrResultsEdit)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.addrResultsEdit.clear()
        self.addrResultsEdit.setHidden(True)
        self.addrResultsLabel.setText("")
        # TODO: why setText and not hide? # FIXME

        desciptor_raw = _clean_submisission(self.descriptorEdit.toPlainText())
        pubkeys_info = _get_pubkeys_info_from_descriptor(desciptor_raw)
        if not pubkeys_info:
            return _msgbox_err(
                main_text="Could not parse pubkeys from submission",
            )

        self.addrResultsLabel.setText("Multisig Addresses")
        self.addrResultsEdit.setHidden(False)

        # https://stackoverflow.com/questions/44014108/pass-a-variable-between-two-scripts
        # TODO: make configurable
        OFFSET = 0
        LIMIT = 20

        # https://stackoverflow.com/questions/50104163/update-pyqt-gui-from-a-python-thread
        results = []
        for index, address in get_addresses(
            pubkey_dicts=pubkeys_info["pubkey_dicts"],
            quorum_m=pubkeys_info["quorum_m"],
            quorum_n=pubkeys_info["quorum_n"],
            limit=LIMIT,
            offset=OFFSET,
            is_testnet=pubkeys_info["is_testnet"],
        ):
            result = f"#{index}: {address}"
            print('result', result)
            self.updateProgress.emit(result)
        print('done')
