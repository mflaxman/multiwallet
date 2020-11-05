from buidl.hd import HDPrivateKey
from buidl.mnemonic import WORD_LOOKUP, WORD_LIST

from tkinter import ttk
from tkinter import messagebox
import tkinter as tk


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
        self.text = tk.Text(self, height=5)
        self.text.grid()

        seedpicker_submit_btn = tk.Button(
            self, text="Calculate Last Word", command=self.first_words_validation
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
