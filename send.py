import tkinter as tk


class SendFrame(tk.Frame):
    TAB_NAME = "Spend"

    def __init__(self, parent):
        # TODO: WET
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Spend via PSBT")
        label.pack(fill="both", expand=True, padx=20, pady=10)
