import re
from PyQt5.QtWidgets import (
    QApplication,
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
    # Use generator for iterative display
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


class ReceiveTab(QWidget):
    TITLE = "Receive"

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.descriptorLabel = QLabel("Wallet Descriptor")
        self.descriptorEdit = QPlainTextEdit("")
        self.descriptorEdit.setPlaceholderText("wsh(sortedmulti(2,...")

        self.descriptorSubmitButton = QPushButton("Derive Addresses")
        self.descriptorSubmitButton.clicked.connect(self.process_submit)

        self.addrResultsLabel = QLabel("")
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
        if not desciptor_raw:
            return _msgbox_err(
                main_text="No Wallet Desciptor",
                informative_text="Enter a wallet descriptor to derive your bitcoin addresses.",
            )
        try:
            pubkeys_info = _get_pubkeys_info_from_descriptor(desciptor_raw)
        except Exception as e:
            return _msgbox_err(
                main_text="Parse Error",
                informative_text=str(e),
            )
        if not pubkeys_info:
            return _msgbox_err(
                main_text="Could not parse pubkeys from submission",
            )

        results_label = f"Multisig Addresses ({pubkeys_info['quorum_m']}-of-{pubkeys_info['quorum_n']})"
        if True:
            # TODO: add test for whether libsec is installed
            results_label += "\nThis is ~100x faster with libsec installed"

        self.addrResultsLabel.setText(results_label)
        self.addrResultsEdit.setHidden(False)

        # https://stackoverflow.com/questions/44014108/pass-a-variable-between-two-scripts
        # TODO: make configurable
        OFFSET = 0
        LIMIT = 5

        # https://stackoverflow.com/questions/50104163/update-pyqt-gui-from-a-python-thread
        for index, address in get_addresses(
            pubkey_dicts=pubkeys_info["pubkey_dicts"],
            quorum_m=pubkeys_info["quorum_m"],
            quorum_n=pubkeys_info["quorum_n"],
            limit=LIMIT,
            offset=OFFSET,
            is_testnet=pubkeys_info["is_testnet"],
        ):
            result = f"#{index}: {address}"
            print("result", result)
            self.addrResultsEdit.appendPlainText(result)
            QApplication.processEvents()  # needed to stream output (otherwise terrible UX)
        print("done")
