import re

from buidl.hd import HDPublicKey
from buidl.helper import sha256
from buidl.op import OP_CODE_NAMES_LOOKUP
from buidl.script import P2WSHScriptPubKey, WitnessScript

import tkinter as tk


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


def _yield_address(pubkey_dicts, quorum_m, quorum_n, limit, offset, is_testnet):
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


class ReceiveFrame(tk.Frame):
    TAB_NAME = "Receive"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Paste Output Descriptor from Specter-Desktop:")
        label.grid()

        self.descriptor_text = tk.Text(self, height=15)
        self.descriptor_text.grid()

        seedpicker_submit_btn = tk.Button(
            self, text="Verify Addresses", command=self.calc_addresses
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

    def calc_addresses(self):
        # delete whatever text might have been in the results box
        self.result.delete(1.0, tk.END)
        self.result.grid_forget()

        descriptor = self.descriptor_text.get("1.0", tk.END).replace("  ", " ").strip()
        if not descriptor:
            return

        pubkeys_info = _get_pubkeys_info_from_descriptor(descriptor)
        if not pubkeys_info:
            return

        # TODO: package with libsec
        self.result.grid()
        self.result.insert(tk.END, "Multisig Addresses:\n\n")

        # https://stackoverflow.com/questions/44014108/pass-a-variable-between-two-scripts
        # TODO: make configurable
        OFFSET = 0
        LIMIT = 10
        kwargs = dict(
            pubkey_dicts=pubkeys_info["pubkey_dicts"],
            quorum_m=pubkeys_info["quorum_m"],
            quorum_n=pubkeys_info["quorum_n"],
            limit=LIMIT,
            offset=OFFSET,
            is_testnet=pubkeys_info["is_testnet"],
        )
        yield_func = _yield_address(**kwargs)
        self.do_update(yield_func, kwargs)
