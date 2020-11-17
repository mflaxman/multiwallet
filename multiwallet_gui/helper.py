from PyQt5.QtWidgets import QMessageBox


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
