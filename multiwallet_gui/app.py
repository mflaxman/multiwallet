from tkinter import ttk
import tkinter as tk

from multiwallet_gui.seedpicker import SeedpickerFrame
from multiwallet_gui.receive import ReceiveFrame
from multiwallet_gui.send import SendFrame

import pkg_resources
import sys


def _get_version():

    try:
        return "v " + pkg_resources.get_distribution("multiwallet").version
    except pkg_resources.DistributionNotFound:
        return "custom"


class Multiwallet(tk.Frame):
    VERSION = _get_version()
    TITLE = f"Multiwallet - Stateless PSBT Multisig Wallet - ALPHA VERSION TESTNET ONLY ({VERSION} - {sys.version})"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.TITLE)
        tk.Frame.__init__(self, self.root)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        seedpicker_frame = SeedpickerFrame(self.notebook)
        receive_frame = ReceiveFrame(self.notebook)
        spend_frame = SendFrame(self.notebook)

        for frame in (seedpicker_frame, receive_frame, spend_frame):
            self.notebook.add(frame, text=frame.TAB_NAME)

        self.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()


def main():
    app = Multiwallet()
    return app.run()


if __name__ == "__main__":
    main()
