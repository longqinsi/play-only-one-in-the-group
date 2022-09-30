from typing import Callable

import aqt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from aqt import qconnect
from aqt.sound import RecordDialog
from aqt.utils import restoreGeom


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

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)

    def _setup_dialog(self) -> None:
        self.setWindowTitle("Anki")
        icon = QLabel()
        icon.setPixmap(QPixmap("icons:media-record.png"))
        self.label = QLabel("...")
        hbox = QHBoxLayout()
        hbox.addWidget(icon)
        hbox.addWidget(self.label)
        v = QVBoxLayout()
        v.addLayout(hbox)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Save)  # type: ignore
        v.addWidget(b)
        self.setLayout(v)
        save_button = b.button(QDialogButtonBox.StandardButton.Save)
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        qconnect(save_button.clicked, self.accept)
        restoreGeom(self, "audioRecorder2")
        self.show()
