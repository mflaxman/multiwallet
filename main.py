from tkinter import ttk
from tkinter import messagebox
import tkinter as tk

from buidl.hd import HDPrivateKey, HDPublicKey
from buidl.helper import sha256
from buidl.mnemonic import WORD_LOOKUP, WORD_LIST
from buidl.op import OP_CODE_NAMES_LOOKUP
from buidl.script import P2WSHScriptPubKey, WitnessScript

import re


def _get_all_valid_checksum_words(first_words):
    to_return = []
    for word in WORD_LIST:
        try:
            HDPrivateKey.from_mnemonic(first_words + " " + word)
            to_return.append(word)
        except KeyError as e:
            # We have a word in first_words that is not in WORD_LIST
            return [], "Invalid BIP39 Word: {}".format(e.args[0])
        except ValueError:
            pass

    return to_return, ""


class SeedpickerFrame(tk.Frame):
    TAB_NAME = "Seedpicker"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Enter first 23 words of your seed:")
        label.grid(column=0, row=1)

        # https://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html
        # vcmd = parent.register(self.validate) # we have to wrap the command
        self.text = tk.Text(self, height=5)
        self.text.grid()

        seedpicker_submit_btn = tk.Button(
            self, text="Calculate", command=self.first_words_validation
        )
        seedpicker_submit_btn.grid()

        self.result = tk.Text(self, height=15)
        self.result.grid_forget()

    def first_words_validation(self):
        # delete whatever text might have been in the results box
        self.result.delete(1.0, tk.END)

        first_words = self.text.get("1.0", tk.END).replace("  ", " ").strip()
        if not first_words:
            return
        print("first_words", first_words)

        fw_num = len(first_words.split())
        if fw_num not in (11, 14, 17, 20, 23):
            # TODO: 11, 14, 17, or 20 word seed phrases also work but this is not documented as it's for advanced users
            err = f"Enter 23 word seed-phrase (you entered {fw_num} words)"
            tk.messagebox.showinfo(message=err)

        wordlist_errors = []
        for cnt, word in enumerate(first_words.split()):
            if word not in WORD_LOOKUP:
                wordlist_errors.append([cnt + 1, word])
        if wordlist_errors:
            # self.text.config(fg='red') (need a UI to turn this off on typing)
            msg = [
                "The following are not valid:",
            ]
            msg.extend([f"  word #{x[0]} {x[1]}" for x in wordlist_errors])
            print("msg", msg)
            tk.messagebox.showinfo(message="\n".join(msg))
            return

        # self.text.config(fg='black')

        valid_checksum_words, err_str = _get_all_valid_checksum_words(first_words)
        if err_str:
            tk.messagebox.showinfo(f"Error calculating checksum word: {err_str}")
            return

        IS_TESTNET = True  # TESTNET ONLY FOR NOW
        if IS_TESTNET:
            PATH = "m/48'/1'/0'/2'"
            SLIP132_VERSION_BYTES = "02575483"
        else:
            PATH = "m/48'/0'/0'/2'"
            SLIP132_VERSION_BYTES = "02aa7ed3"

        last_word = valid_checksum_words[0]
        hd_priv = HDPrivateKey.from_mnemonic(first_words + " " + last_word)

        to_display = [
            "SECRET INFO - guard this VERY carefully",
            f"Last Word: {last_word}",
            f"Full {fw_num + 1} word mnemonic (including last word): {first_words + ' ' + last_word}",
            "",
            f"PUBLIC KEY INFO ({'testnet' if IS_TESTNET else 'mainnet'})",
            "Copy-paste this into Specter-Desktop:",
            "",
            "  [{}{}]{}".format(
                hd_priv.fingerprint().hex(),
                PATH.replace("m", "").replace("'", "h"),
                hd_priv.traverse(PATH).xpub(
                    version=bytes.fromhex(SLIP132_VERSION_BYTES)
                ),
            ),
        ]

        self.result.insert(tk.END, "\n".join(to_display))
        # TODO: disable editing in a way that still allows copy-paste
        self.result.grid()


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
    commands.extend(
        [bytes.fromhex(x) for x in sorted(sec_hexes_to_use)]  # BIP67
    )
    commands.append(
        OP_CODE_NAMES_LOOKUP["OP_{}".format(quorum_n)]
    )
    commands.append(OP_CODE_NAMES_LOOKUP["OP_CHECKMULTISIG"])
    witness_script = WitnessScript(commands)
    redeem_script = P2WSHScriptPubKey(sha256(witness_script.raw_serialize()))
    return redeem_script.address(testnet=is_testnet)


def information(pubkey_dicts, quorum_m, quorum_n, limit, offset, is_testnet):
    # Create generator obj
    for cnt in range(limit):
        index = cnt+offset
        print('index', index)
        address = _get_address(
            pubkey_dicts=pubkey_dicts,
            quorum_m=quorum_m,
            quorum_n=quorum_n,
            index=index,
            is_testnet=is_testnet,
        )
        yield index, address
        

class RecieveFrame(tk.Frame):
    TAB_NAME = "Receive"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        label = tk.Label(
            self, text="Verify Recieve Addresses (paste output descriptor):"
        )
        label.grid()

        self.descriptor_text = tk.Text(self, height=15)
        self.descriptor_text.grid()

        seedpicker_submit_btn = tk.Button(
            self, text="Calculate Addresses", command=self.run_script
        )
        seedpicker_submit_btn.grid()

        self.result = tk.Text(self, height=15)
        self.result.grid_forget()

    def do_update(self, gen, var):
        # https://stackoverflow.com/questions/44014108/pass-a-variable-between-two-scripts
        DELAY = 1  # in millisecs
        try:
            next_value = next(gen)
        except StopIteration:
            print("Done")
        else:
            self.result.insert(tk.END, f"#{next_value[0]}: {next_value[1]}\n")
            # import pdb; pdb.set_trace()
            # self.parent.master
            self.parent.after(DELAY, self.do_update, gen, var)  # call again after delay


    def run_script(self):
        # delete whatever text might have been in the results box
        self.result.delete(1.0, tk.END)

        descriptor = self.descriptor_text.get("1.0", tk.END).replace("  ", " ").strip()
        if not descriptor:
            return

        pubkeys_info = _get_pubkeys_info_from_descriptor(descriptor)
        if not pubkeys_info:
            return

        # TODO: package with libsec
        self.result.grid()
        self.result.insert(tk.END, "Multisig Addresses\n")

        # https://stackoverflow.com/questions/44014108/pass-a-variable-between-two-scripts
        # TODO: make configurable
        OFFSET = 0
        LIMIT = 10
        var = dict (
            pubkey_dicts=pubkeys_info["pubkey_dicts"],
            quorum_m=pubkeys_info["quorum_m"],
            quorum_n=pubkeys_info["quorum_n"],
            limit=LIMIT,
            offset=OFFSET,
            is_testnet=pubkeys_info['is_testnet'],
        )
        gen = information(**var)
        self.do_update(gen, var)



class SpendFrame(tk.Frame):
    TAB_NAME = "Spend"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Spend via PSBT")
        label.pack(fill="both", expand=True, padx=20, pady=10)


class Multiwallet(tk.Frame):
    TITLE = "Multiwallet - Stateless PSBT Multisig Wallet"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.TITLE)
        tk.Frame.__init__(self, self.root)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        seedpicker_frame = SeedpickerFrame(self.notebook)
        receive_frame = RecieveFrame(self.notebook)
        spend_frame = SpendFrame(self.notebook)

        for frame in (seedpicker_frame, receive_frame, spend_frame):
            self.notebook.add(frame, text=frame.TAB_NAME)

        self.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = Multiwallet()
    app.run()
