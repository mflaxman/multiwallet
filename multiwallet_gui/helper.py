import qrcode
import re

from io import BytesIO
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QIcon


def strip_html(data):
    # https://stackoverflow.com/questions/3398852/using-python-remove-html-tags-formatting-from-a-string
    p = re.compile(r"<.*?>")
    return p.sub("", data)


def create_qr_icon():
    return QIcon("multiwallet_gui/images/qr.png")


def create_qt_pixmap_qr(text):
    """
    How to use this:
      label.setText("")
      label.setPixmap(create_qt_pixmap_qr(text="foo"))

    https://stackoverflow.com/a/58251630/1754586
    """
    buf = BytesIO()
    img = qrcode.make(text)
    img.save(buf, "PNG")
    qt_pixmap = QPixmap()
    qt_pixmap.loadFromData(buf.getvalue(), "PNG")
    return qt_pixmap


def _clean_submisission(string):
    # TODO: more advanced regex
    return string.replace("  ", " ").strip()


def _msgbox_err(main_text=None, informative_text=None, detailed_text=None):
    msg = QMessageBox()
    # msg.setWindowTitle("foo")  # TODO: this doesn't work
    if main_text:
        msg.setText(main_text)
    msg.setIcon(QMessageBox.Critical)
    if informative_text:
        msg.setInformativeText(informative_text)

    if detailed_text:
        msg.setDetailedText(detailed_text)
    msg.exec_()


class QRPopup(QDialog):
    def __init__(self, qr_text, window_title, window_height):
        super().__init__()

        self.setWindowTitle(window_title)
        # self.height = window_height

        self.setMaximumHeight(16777215)
        self.setMaximumWidth(16777215)

        self.qr_text = qr_text

        self.vbox = QVBoxLayout()

        self.labelImage = QLabel()
        self.labelImage.setMaximumHeight(16777215)
        self.labelImage.setMaximumWidth(16777215)

        self._set_pixmap(height_to_use=window_height * 0.9)

        self.vbox.addWidget(self.labelImage)
        self.setLayout(self.vbox)

        self.show()

    def _set_pixmap(self, height_to_use=None):
        if height_to_use is None:
            height_to_use = self.height() * 0.9

        self.pixmap = create_qt_pixmap_qr(text=self.qr_text).scaledToHeight(
            height_to_use
        )
        self.labelImage.setPixmap(self.pixmap)

    def resizeEvent(self, event):
        self.pixmap = self._set_pixmap()


def qr_dialog(qwidget, qr_text, window_title):
    # set to 90% of max size: https://stackoverflow.com/questions/35887237/current-screen-size-in-python3-with-pyqt5
    window_height = qwidget.screen().size().height() * 0.9
    dialog = QRPopup(
        qr_text=qr_text,
        window_title=strip_html(window_title),
        window_height=window_height,
    )
    return dialog.exec_()


def _is_libsec_enabled():
    # TODO: move to buidl
    try:
        from buidl import cecc  # noqa: F401

        return True
    except ModuleNotFoundError:
        return False


BITCOIN_NETWORK_TOOLTIP = (
    "Testnet is a great tool for practicing, as Testnet coins have no monetary value. "
    "We recommend new users do a dry-run on Testnet before receiving real bitcoins."
    "<br/><br/>"
    "You can get free Testnet coins from several Testnet faucets."
    "Testnet blocks"
)

BITCOIN_TESTNET_TOOLTIP = "Segwit Testnet addresses start with <i>tb1</i>..."

BITCOIN_MAINNET_TOOLTIP = (
    "Regular bitcoin transaction" "Segwit Mainnet addresses start with <i>bc1</i>..."
)
