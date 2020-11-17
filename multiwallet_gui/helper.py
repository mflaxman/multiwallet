import qrcode

from io import BytesIO
from PyQt5.QtWidgets import QMessageBox, QSizePolicy, QTextEdit, QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ResizeableMessageBox(QMessageBox):
    # https://stackoverflow.com/a/2664019/1754586

    def __init__(self):
        QMessageBox.__init__(self)
        self.setSizeGripEnabled(True)

    def event(self, e):
        result = QMessageBox.event(self, e)

        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        textEdit = self.findChild(QTextEdit)
        if textEdit != None :
            textEdit.setMinimumHeight(0)
            textEdit.setMaximumHeight(16777215)
            textEdit.setMinimumWidth(0)
            textEdit.setMaximumWidth(16777215)
            textEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return result


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

    def __init__(self, text):
        super().__init__()

        self.setMaximumHeight(16777215)
        self.setMaximumWidth(16777215)

        self.text = text

        self.vbox = QVBoxLayout()
        # self.labelImage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.labelImage.setPixmap(self.pixmap)

        self.labelImage = QLabel()
        self.labelImage.setMaximumWidth(16777215)

        self._set_pixmap()

        self.vbox.addWidget(self.labelImage)
        self.setLayout(self.vbox)

        self.show()

    def _set_pixmap(self):
        self.pixmap = create_qt_pixmap_qr(text=self.text).scaledToWidth(self.width() * .8)
        print("width", self.width(), self.pixmap.width())
        self.labelImage.setPixmap(self.pixmap)
        self.labelImage.resize(self.width() * .8, self.height() * .8)
        self.setLayout(self.vbox)
        self.show()

    def resizeEvent(self, event):
        print("resize")
        self.pixmap = self._set_pixmap()

def _msgbox_image(text):
    dialog = QRPopup(text=text)
    dialog.exec_()


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
