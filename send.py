import tkinter as tk
from tkinter import messagebox  # https://stackoverflow.com/a/29780454/1754586

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


class SendFrame(tk.Frame):
    TAB_NAME = "Spend"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        psbt_label = tk.Label(self, text="Paste PSBT from Specter-Desktop")
        psbt_label.grid()

        self.psbt_text = tk.Text(self, height=25)
        self.psbt_text.grid()

        bip39_label = tk.Label(self, text="Enter your FULL 24-word BIP39 seed")
        bip39_label.grid()

        self.bip39_text = tk.Text(self, height=5)
        self.bip39_text.grid()

        psbt_submit_btn = tk.Button(self, text="Sign PSBT", command=self.sign_psbt)
        psbt_submit_btn.grid()

        self.separator = tk.ttk.Separator(self)
        self.separator.grid_forget()

        self.tx_summary_label = tk.Message(self, text="", width=800)
        self.tx_summary_label.grid_forget()

        self.signed_psbt_result = tk.Text(self, height=10)
        self.signed_psbt_result.grid_forget()

    def sign_psbt(self):
        # Clear state:
        self.separator.grid_forget()
        self.signed_psbt_result.delete(1.0, tk.END)
        self.signed_psbt_result.grid_forget()
        self.tx_summary_label.config(text="")
        self.tx_summary_label.grid_forget()

        # fetch values
        psbt_b64 = self.psbt_text.get("1.0", tk.END).replace("  ", " ").strip()
        bip39_str = self.bip39_text.get("1.0", tk.END).replace("  ", " ").strip()

        if not psbt_b64 or not bip39_str:
            return

        seed_phrase_num = len(bip39_str.split())
        if seed_phrase_num not in (12, 15, 18, 21, 24):
            msg = f"Enter 24 word seed-phrase (you entered {seed_phrase_num} words)"
            messagebox.showinfo(message=msg)
            return

        # FIXME:
        IS_TESTNET = True
        UNITS = "sats"

        try:
            hd_priv = HDPrivateKey.from_mnemonic(bip39_str, testnet=IS_TESTNET)
        except Exception as e:
            messagebox.showinfo(message=f"BIP39 Seed Error: {e}")
            return

        try:
            psbt_obj = PSBT.parse_base64(psbt_b64, testnet=IS_TESTNET)
        except Exception as e:
            messagebox.showinfo(message=f"PSBT Parse Error: {e}")
            return

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
                msg = f"Input #{cnt} does not contain a witness script, this tool can only sign p2wsh transactions."
                messagebox.showinfo(message=msg)

            # Determine quroum_m (and that it hasn't changed between inputs)
            try:
                quorum_m = OP_CODE_NAMES[psbt_in.witness_script.commands[0]].split(
                    "OP_"
                )[1]
            except Exception:
                messagebox.showinfo(
                    message=f"Witness script for input #{cnt} is not p2wsh:\n{psbt_in})"
                )
                return

            root_path_used = None
            root_xfp_hexes = []  # for calculating msig fingerprint
            for _, details in psbt_in.named_pubs.items():
                root_xfp_hexes.append(details.root_fingerprint.hex())
                if details.root_fingerprint.hex() == hd_priv.fingerprint().hex():
                    root_path_used = details.root_path

            input_desc = {
                "quorum": f"{quorum_m}-of-{len(root_xfp_hexes)}",
                "root_xfp_hexes": root_xfp_hexes,
                "root_path_used": root_path_used,
                "prev_txhash": psbt_in.tx_in.prev_tx.hex(),
                "prev_idx": psbt_in.tx_in.prev_index,
                "n_sequence": psbt_in.tx_in.sequence,
                "sats": psbt_in.tx_in.value(),
                # TODO: would be possible for transaction to be p2sh-wrapped p2wsh (can we tell?)
                "addr": psbt_in.witness_script.address(testnet=IS_TESTNET),
                # "p2sh_addr": psbt_in.witness_script.p2sh_address(testnet=IS_TESTNET),
                "witness_script": str(psbt_in.witness_script),
                "msig_digest": _calculate_msig_digest(
                    quorum_m=quorum_m, root_xfp_hexes=root_xfp_hexes
                ),
            }
            if not root_path_used:
                msg = f"This key is not a participant in input #{cnt}:\n{input_desc}"
                messagebox.showinfo(message=msg)
                return

            inputs_desc.append(input_desc)

        if not all(
            x["msig_digest"] == inputs_desc[0]["msig_digest"] for x in inputs_desc
        ):
            msg = "Multiple different multisig quorums in inputs. Construct a transaction with one input to continue."
            messagebox.showinfo(message=msg)
            return

        TOTAL_INPUT_SATS = sum([x["sats"] for x in inputs_desc])

        # This too only supports TXs with 1-2 outputs (sweep TX OR spend+change TX):
        if len(psbt_obj.psbt_outs) > 2:
            msg = f"This tool does not support batching, your transaction has {len(psbt_obj.psbt_outs)} outputs. Please construct a transaction with <= 2 outputs."
            messagebox.showinfo(message=msg)
            return

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
                    testnet=IS_TESTNET
                )
            else:
                output_desc["addr"] = psbt_out.tx_out.script_pubkey.address(
                    testnet=IS_TESTNET
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
                    msg = f"Witness script for input #{cnt} is not p2wsh:\n{psbt_in})"
                    messagebox.showinfo(message=msg)
                    return

                output_msig_digest = _calculate_msig_digest(
                    quorum_m=quorum_m, root_xfp_hexes=root_xfp_hexes
                )
                if (
                    output_msig_digest != inputs_desc[0]["msig_digest"]
                ):  # ALL inputs have the same msig_digest
                    msg = f"Output #{cnt} is claiming to be change but has different multisig wallet(s)! Do a sweep transaction (1-output) if you want this wallet to cosign."
                    messagebox.showinfo(message=msg)
                    return
            else:
                output_desc["is_change"] = False
                spend_addr = output_desc["addr"]
                output_spend_sats = output_desc["sats"]

            outputs_desc.append(output_desc)

        # Sanity check
        if len(outputs_desc) != len(psbt_obj.psbt_outs):
            msg = f"{len(outputs_desc)} outputs in summary doesn't match {len(psbt_obj.psbt_outs)} outputs in PSBT"
            messagebox.showinfo(message=msg)
            return

        # Confirm if 2 outputs we only have 1 change and 1 spend (can't be 2 changes or 2 spends)
        if len(outputs_desc) == 2:
            if all(
                x["is_change"] == outputs_desc[0]["is_change"] for x in outputs_desc
            ):
                msg = f"Cannot have both outputs be change or spend, must be 1-and-1. {outputs_desc}"
                messagebox.showinfo(message=msg)
                return

        self.separator.grid(sticky="ew")

        # Derive list of child private keys we'll use to sign the TX
        private_keys = []
        for root_path in set([x["root_path_used"] for x in inputs_desc]):
            private_keys.append(hd_priv.traverse(root_path).private_key)

        TX_SUMMARY = " ".join(
            [
                "Signed PSBT sending",
                _format_satoshis(output_spend_sats, in_btc=UNITS == "btc"),
                "to",
                spend_addr,
                "with a fee of",
                _format_satoshis(TX_FEE_SATS, in_btc=UNITS == "btc"),
                f"({round(TX_FEE_SATS / TOTAL_INPUT_SATS * 100, 2)}% of spend)",
            ]
        )
        self.tx_summary_label.config(text=TX_SUMMARY)
        self.tx_summary_label.grid()

        if True:
            # TODO: move this to UI
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

        if psbt_obj.sign_with_private_keys(private_keys) is True:
            self.signed_psbt_result.insert(tk.END, psbt_obj.serialize_base64())
            self.signed_psbt_result.grid()
        else:
            messagebox.showinfo(message="PSBT wasn't signed")
            return
