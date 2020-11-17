#! /usr/bin/env bash

import re

from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
)

from multiwallet_gui.helper import _clean_submisission, _msgbox_err, _is_libsec_enabled

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
    HOVER = "Verify your bitcoin addresses belong to you qourum."

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.descriptorLabel = QLabel("<b>Wallet Descriptor</b>")
        self.descriptorLabel.setToolTip(
            "This extended <i>public</i> key information (from all your hardware wallets) is used to generate your bitcoin addresses."
            "<br><br>From Specter-Desktop: Wallet > Settings > Export To Wallet Software > Export > Copy wallet data."
        )
        self.descriptorEdit = QPlainTextEdit("")
        self.descriptorEdit.setPlaceholderText(
            "Something like this:\n\nwsh(sortedmulti(2,[deadbeef/48h/1h/0h/2h]xpub.../0/*,"
        )

        self.limit_label = QLabel("<b>Limit of Addresses to Derive</b>")
        self.limit_label.setToolTip("Address derivation is slow.")
        self.limit_box = QSpinBox()
        self.limit_box.setValue(5)
        self.limit_box.setRange(1, 10000)

        self.offset_label = QLabel("<b>Offset of Addresses to Derive</b>")
        self.offset_label.setToolTip("Advanced users only.")
        self.offset_box = QSpinBox()
        self.offset_box.setValue(0)
        self.offset_box.setMinimum(0)

        self.descriptorSubmitButton = QPushButton("Derive Addresses")
        self.descriptorSubmitButton.clicked.connect(self.process_submit)

        self.addrResultsLabel = QLabel("")
        self.addrResultsLabel.setToolTip(
            "These bitcoin addresses belong to the quorum of extended public keys above. You may want to print this out for future reference."
        )
        self.addrResultsEdit = QPlainTextEdit("")
        self.addrResultsEdit.setReadOnly(True)
        self.addrResultsEdit.setHidden(True)

        vbox.addWidget(self.descriptorLabel)
        vbox.addWidget(self.descriptorEdit)
        vbox.addWidget(self.limit_label)
        vbox.addWidget(self.limit_box)
        vbox.addWidget(self.offset_label)
        vbox.addWidget(self.offset_box)
        vbox.addWidget(self.descriptorSubmitButton)
        vbox.addWidget(self.addrResultsLabel)
        vbox.addWidget(self.addrResultsEdit)

        self.setLayout(vbox)

    def process_submit(self):
        # Clear any previous submission in case of errors
        self.addrResultsEdit.clear()
        self.addrResultsEdit.setHidden(True)
        self.addrResultsLabel.setText("")
        # TODO: why setText and not hide?

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

        results_label = f"<b>{pubkeys_info['quorum_m']}-of-{pubkeys_info['quorum_n']} Multisig Addresses</b>"
        if not _is_libsec_enabled():
            results_label += "<br>(this is ~100x faster with libsec installed)"

        self.addrResultsLabel.setText(results_label)
        self.addrResultsEdit.setHidden(False)

        limit = self.limit_box.value()
        offset = self.offset_box.value()

        # https://stackoverflow.com/questions/50104163/update-pyqt-gui-from-a-python-thread
        for index, address in get_addresses(
            pubkey_dicts=pubkeys_info["pubkey_dicts"],
            quorum_m=pubkeys_info["quorum_m"],
            quorum_n=pubkeys_info["quorum_n"],
            limit=limit,
            offset=offset,
            is_testnet=pubkeys_info["is_testnet"],
        ):
            result = f"#{index}: {address}"
            self.addrResultsEdit.appendPlainText(result)
            QApplication.processEvents()  # needed to stream output (otherwise terrible UX)
