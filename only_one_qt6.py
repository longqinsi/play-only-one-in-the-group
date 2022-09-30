from typing import Callable

import aqt
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget
from aqt.sound import RecordDialog


class CustomRecordDialog(RecordDialog):
    def __init__(
        self,
        parent: QWidget,
        mw: aqt.main.AnkiQt,
        on_success: Callable[[str], None]
    ):
        RecordDialog.__init__(self, parent, mw, on_success)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.accept()
            event.accept()
        elif event.key() == QtCore.Qt.Key.Key_Q:
            self.reject()
            event.accept()
        else:
            super().keyPressEvent(event)
