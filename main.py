from tkinter import ttk
import tkinter as tk

from seedpicker import SeedpickerFrame
from receive import ReceiveFrame
from send import SendFrame


class Multiwallet(tk.Frame):
    TITLE = "Multiwallet - Stateless PSBT Multisig Wallet"

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


if __name__ == "__main__":
    app = Multiwallet()
    app.run()
