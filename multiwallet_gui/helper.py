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
