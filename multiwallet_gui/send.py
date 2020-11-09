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
from buidl.helper import hash256
from buidl.psbt import PSBT
from buidl.script import WitnessScript
from buidl.op import OP_CODE_NAMES


# TODO: is there a standard to use here?
# Inspired by https://github.com/trezor/trezor-firmware/blob/e23bb10ec49710cc2b2b993db9c907d3c7becf2c/core/src/apps/wallet/sign_tx/multisig.py#L37
def _calculate_msig_digest(quorum_m, root_xfp_hexes):
    fingerprints_to_hash = "-".join(sorted(root_xfp_hexes))
    return hash256(f"{quorum_m}:{fingerprints_to_hash}".encode()).hex()


def _format_satoshis(sats, in_btc=False):
    if in_btc:
        btc = sats / 10 ** 8
        return f"{btc:,.8f} BTC"
    return f"{sats:,} sats"


class SendTab(QWidget):
    TITLE = "Send"

    # FIXME (add support and UX for this)
    UNITS = "sats"
    IS_TESTNET = True  # No way to reliably infer this from the PSBT unfortunately :(

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        self.psbtLabel = QLabel("Partially Signed Bitcoin Transaction (PSBT) in Base64")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.psbtEdit = QPlainTextEdit("")
        self.psbtEdit.setPlaceholderText("cHNidP8BAH0CAAAAA...")

        self.fullSeedLabel = QLabel("Enter Your Full 24-Word Seed (to sign)")
        # FIXME: pre-seeding for easier testing, get rid of this
        self.fullSeedEdit = QPlainTextEdit(
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo abstract"
        )
        self.fullSeedEdit.setPlaceholderText(
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo"
        )

        self.psbtDecodedLabel = QLabel("")
        self.psbtDecodedEdit = QPlainTextEdit("")
        self.psbtDecodedEdit.setReadOnly(True)
        self.psbtDecodedEdit.setHidden(True)

        self.psbtSubmitButton = QPushButton("Decode Transaction")
        self.psbtSubmitButton.clicked.connect(self.decode_psbt)

        self.fullSeedSubmitButton = QPushButton("Sign Transaction")
        self.fullSeedSubmitButton.clicked.connect(self.sign_psbt)

        self.psbtSignedLabel = QLabel("")
        self.psbtSignedEdit = QPlainTextEdit("")
        self.psbtSignedEdit.setReadOnly(True)
        self.psbtSignedEdit.setHidden(True)

        vbox.addWidget(self.psbtLabel)
        vbox.addWidget(self.psbtEdit)
        vbox.addWidget(self.psbtSubmitButton)
        vbox.addWidget(self.fullSeedLabel)
        vbox.addWidget(self.fullSeedEdit)
        vbox.addWidget(self.fullSeedSubmitButton)
        vbox.addWidget(self.psbtDecodedLabel)
        vbox.addWidget(self.psbtDecodedEdit)
        vbox.addWidget(self.psbtSignedLabel)
        vbox.addWidget(self.psbtSignedEdit)

        self.setLayout(vbox)

    def decode_psbt(self):
        return self.process_psbt(sign_tx=False)

    def sign_psbt(self):
        return self.process_psbt(sign_tx=True)

    def process_psbt(self, sign_tx=True):
        # Clear any previous submission in case of errors
        self.psbtDecodedLabel.setText("")
        self.psbtDecodedEdit.clear()
        self.psbtDecodedEdit.setHidden(True)

        self.psbtSignedLabel.setText("")
        self.psbtSignedEdit.clear()
        self.psbtSignedEdit.setHidden(True)
        # TODO: why setText and not hide? # FIXME

        psbt_str = _clean_submisission(self.psbtEdit.toPlainText())

        if not psbt_str:
            return _msgbox_err(
                main_text="No PSBT Supplied",
                informative_text="Enter a PSBT to decode and/or sign.",
            )

        try:
            psbt_obj = PSBT.parse_base64(b64=psbt_str, testnet=self.IS_TESTNET)
        except Exception as e:
            return _msgbox_err(
                main_text="PSBT Parse Error",
                informative_text="Are you sure that's a PSBT?",
                detailed_text=str(e),
            )
        TX_FEE_SATS = psbt_obj.tx_obj.fee()

        # Validate multisig transaction
        # TODO: abstract some of this into buidl library?
        # Below is confusing because we perform both validation and coordinate signing.

        # This tool only supports a TX with the following constraints:
        #   We sign ALL inputs and they have the same multisig wallet (quorum + pubkeys)
        #   There can only be 1 output (sweep transaction) or 2 outputs (spend + change).
        #   If there is change, we validate it has the same multisig wallet as the inputs we sign.

        # Gather TX info and validate
        inputs_desc = []
        for cnt, psbt_in in enumerate(psbt_obj.psbt_ins):
            psbt_in.validate()  # redundant but explicit

            if type(psbt_in.witness_script) != WitnessScript:
                return _msgbox_err(
                    main_text="Input #{cnt} does not contain a witness script",
                    informative_text="This tool can only sign p2wsh transactions.",
                )

            # Determine quroum_m (and that it hasn't changed between inputs)
            try:
                quorum_m = OP_CODE_NAMES[psbt_in.witness_script.commands[0]].split(
                    "OP_"
                )[1]
            except Exception:
                return _msgbox_err(
                    main_text="Non-p2wsh Input",
                    informative_text=f"Witness script for input #{cnt} is not p2wsh",
                    detailed_text=f"PSBT Input:\n {psbt_in}",
                )

            # for calculating msig fingerprint
            root_xfp_hexes = []
            for _, details in psbt_in.named_pubs.items():
                root_xfp_hexes.append(details.root_fingerprint.hex())

            input_desc = {
                "quorum": f"{quorum_m}-of-{len(root_xfp_hexes)}",
                "root_xfp_hexes": root_xfp_hexes,
                "prev_txhash": psbt_in.tx_in.prev_tx.hex(),
                "prev_idx": psbt_in.tx_in.prev_index,
                "n_sequence": psbt_in.tx_in.sequence,
                "sats": psbt_in.tx_in.value(),
                # TODO: would be possible for transaction to be p2sh-wrapped p2wsh (can we tell?)
                "addr": psbt_in.witness_script.address(testnet=self.IS_TESTNET),
                # "p2sh_addr": psbt_in.witness_script.p2sh_address(testnet=self.IS_TESTNET),
                "witness_script": str(psbt_in.witness_script),
                "msig_digest": _calculate_msig_digest(
                    quorum_m=quorum_m, root_xfp_hexes=root_xfp_hexes
                ),
            }
            inputs_desc.append(input_desc)

        if not all(
            x["msig_digest"] == inputs_desc[0]["msig_digest"] for x in inputs_desc
        ):
            return _msgbox_err(
                main_text="Inputs Contain Conflicting Wallet Quorums",
                informative_text="This transaction is not inherently bad, but transactions of this type are only possible for experts. Please construct 1 or more transactions with one input instead.",
                detailed_text=f"For developers: {inputs_desc}",
            )

        TOTAL_INPUT_SATS = sum([x["sats"] for x in inputs_desc])

        # This too only supports TXs with 1-2 outputs (sweep TX OR spend+change TX):
        if len(psbt_obj.psbt_outs) > 2:
            return _msgbox_err(
                main_text="Too Many Outputs",
                informative_text=f"Multiwallet does not support batching, and your transaction has {len(psbt_obj.psbt_outs)} outputs.",
                detailed_text="Please construct a transaction with <= 2 outputs.",
            )

        spend_addr, output_spend_sats = "", 0
        outputs_desc = []
        for cnt, psbt_out in enumerate(psbt_obj.psbt_outs):
            psbt_out.validate()  # redundant but explicit

            output_desc = {
                "sats": psbt_out.tx_out.amount,
                "addr_type": psbt_out.tx_out.script_pubkey.__class__.__name__.rstrip(
                    "ScriptPubKey"
                ),
            }

            if psbt_out.witness_script:
                output_desc["addr"] = psbt_out.witness_script.address(
                    testnet=self.IS_TESTNET
                )
            else:
                output_desc["addr"] = psbt_out.tx_out.script_pubkey.address(
                    testnet=self.IS_TESTNET
                )

            if psbt_out.named_pubs:
                # Validate below that this is correct and abort otherwise
                output_desc["is_change"] = True

                root_xfp_hexes = []  # for calculating msig fingerprint
                for _, details in psbt_out.named_pubs.items():
                    root_xfp_hexes.append(details.root_fingerprint.hex())

                # Determine quroum_m (and that it hasn't changed between inputs)
                try:
                    quorum_m = OP_CODE_NAMES[psbt_out.witness_script.commands[0]].split(
                        "OP_"
                    )[1]
                except Exception:
                    return _msgbox_err(
                        main_text="Non-p2wsh Change Output",
                        informative_text="This transaction may be trying to trick you into sending change to a third party.",
                        detailed_text=f"Witness script for output #{cnt} is not p2wsh: {psbt_out}",
                    )

                output_msig_digest = _calculate_msig_digest(
                    quorum_m=quorum_m, root_xfp_hexes=root_xfp_hexes
                )
                if output_msig_digest != inputs_desc[0]["msig_digest"]:
                    return _msgbox_err(
                        main_text="Invalid Change Detected",
                        informative_text=f"Output #{cnt} is claiming to be change but has different multisig wallet(s)! Do a sweep transaction (1-output) if you want this wallet to cosign.",
                        detailed_text=f"For developers: {outputs_desc}",
                    )
            else:
                output_desc["is_change"] = False
                spend_addr = output_desc["addr"]
                output_spend_sats = output_desc["sats"]

            outputs_desc.append(output_desc)

        # Sanity check
        if len(outputs_desc) != len(psbt_obj.psbt_outs):
            return _msgbox_err(
                main_text="PSBT Parse Error",
                informative_text=f"{len(outputs_desc)} outputs in TX summary doesn't match {len(psbt_obj.psbt_outs)} outputs in PSBT.",
            )

        # Confirm if 2 outputs we only have 1 change and 1 spend (can't be 2 changes or 2 spends)
        if len(outputs_desc) == 2:
            if all(
                x["is_change"] == outputs_desc[0]["is_change"] for x in outputs_desc
            ):
                return _msgbox_err(
                    main_text="Change-Only Transaction with 2 Outputs",
                    informative_text="Transactions with 2 outputs that are BOTH change are not allowed, as only experts can properly validate them. Please construct a transaction with fewer outputs.",
                    detailed_text=f"For developers: {outputs_desc}",
                )

        TX_SUMMARY = " ".join(
            [
                "PSBT sends",
                _format_satoshis(output_spend_sats, in_btc=self.UNITS == "btc"),
                "to",
                spend_addr,
                "with a fee of",
                _format_satoshis(TX_FEE_SATS, in_btc=self.UNITS == "btc"),
                f"({round(TX_FEE_SATS / TOTAL_INPUT_SATS * 100, 2)}% of spend)",
            ]
        )
        self.psbtDecodedLabel.setText("Decoded Transaction Summary")
        self.psbtDecodedEdit.setHidden(False)
        self.psbtDecodedEdit.appendPlainText(TX_SUMMARY)

        # TODO: surface this to user somehow
        to_print = []
        to_print.append("DETAILED VIEW")
        to_print.append(f"TXID: {psbt_obj.tx_obj.id()}")
        to_print.append("-" * 80)
        to_print.append(f"{len(inputs_desc)} Input(s):")
        for cnt, input_desc in enumerate(inputs_desc):
            to_print.append(f"  input #{cnt}")
            for k in input_desc:
                to_print.append(f"    {k}: {input_desc[k]}")
        to_print.append("-" * 80)
        to_print.append(f"{len(outputs_desc)} Output(s):")
        for cnt, output_desc in enumerate(outputs_desc):
            to_print.append(f"  output #{cnt}")
            for k in output_desc:
                to_print.append(f"    {k}: {output_desc[k]}")
        print("\n".join(to_print))

        seed_phrase = _clean_submisission(self.fullSeedEdit.toPlainText())

        if not sign_tx:
            return

        if not seed_phrase:
            return _msgbox_err(
                main_text="No Seed Phrase Supplied",
                informative_text="Cannot Sign Transaction Without Seed Phrase",
            )

        seed_phrase_num = len(seed_phrase.split())
        if seed_phrase_num not in (12, 15, 18, 21, 24):
            return _msgbox_err(
                main_text="Enter 24 word seed-phrase",
                informative_text=f"You entered {seed_phrase_num} words)",
            )

        try:
            hd_priv = HDPrivateKey.from_mnemonic(seed_phrase, testnet=self.IS_TESTNET)
        except Exception as e:
            return _msgbox_err(
                main_text="Invalid BIP39 Seed Phrase",
                informative_text="Transaction NOT signed",
                detailed_view=str(e),
            )

        # Derive list of child private keys we'll use to sign the TX
        root_paths = set()
        for cnt, psbt_in in enumerate(psbt_obj.psbt_ins):
            # Redundant safety check:
            bad_txhash = inputs_desc[cnt]["prev_txhash"] != psbt_in.tx_in.prev_tx.hex()
            bad_idx = inputs_desc[cnt]["prev_idx"] != psbt_in.tx_in.prev_index
            if bad_txhash or bad_idx:
                return _msgbox_err(
                    main_text="PSBT Parse Error",
                    informative_text="Transaction NOT signed",
                    detailed_view=f"For developers: Input #{cnt} prev_txhash or prev_idx mismatch: \n{PSBT.serialize_base64()}",
                )

            for _, details in psbt_in.named_pubs.items():
                if details.root_fingerprint.hex() == hd_priv.fingerprint().hex():
                    root_paths.add(details.root_path)

        if not root_paths:
            return _msgbox_err(
                main_text="Wrong Seed",
                informative_text="Seed supplied does not correspond to transaction input(s). Does it belong to another wallet?",
            )

        private_keys = [
            hd_priv.traverse(root_path).private_key for root_path in root_paths
        ]

        try:
            if psbt_obj.sign_with_private_keys(private_keys) is True:
                self.psbtSignedLabel.setText("Signed PSBT to Broadcast")
                self.psbtSignedEdit.setHidden(False)
                self.psbtSignedEdit.appendPlainText(psbt_obj.serialize_base64())
            else:
                return _msgbox_err(
                    main_text="Transaction Not Signed",
                    informative_text="Couldn't find private key to sign with",
                    detailed_view="This should've been checked earlier and should not be possible!",
                )
        except Exception as e:
            return _msgbox_err(
                main_text="Transaction Not Signed",
                informative_text="There was an error during signing.",
                detailed_view=f"For developers: {e}",
            )
