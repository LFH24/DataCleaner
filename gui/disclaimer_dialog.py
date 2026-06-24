"""
免责声明弹窗 — 应用启动时显示
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QApplication,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon

from config import (
    DISCLAIMER_TITLE, DISCLAIMER_TEXT,
    DISCLAIMER_CHECKBOX, DISCLAIMER_AGREE, DISCLAIMER_EXIT,
    APP_NAME,
)


SETTINGS_ORG = "DataPreprocessor"
SETTINGS_APP = "DataCleaner"


class DisclaimerDialog(QDialog):
    """免责声明对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(DISCLAIMER_TITLE)
        self.setMinimumSize(520, 480)
        self.setMaximumSize(600, 580)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        # 阻止关闭按钮直接关闭
        self._accepted = False

        self._setup_ui()
        self.setModal(True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        title = QLabel(DISCLAIMER_TITLE)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #d32f2f;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 分割线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)

        # 内容
        content = QLabel(DISCLAIMER_TEXT)
        content.setWordWrap(True)
        content.setTextFormat(Qt.TextFormat.RichText)
        content.setStyleSheet("font-size: 12px; line-height: 1.6; color: #444;")
        layout.addWidget(content)

        layout.addStretch()

        # 复选框
        self.checkbox = QCheckBox(DISCLAIMER_CHECKBOX)
        self.checkbox.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.checkbox.stateChanged.connect(self._on_checkbox)
        layout.addWidget(self.checkbox)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.exit_btn = QPushButton(DISCLAIMER_EXIT)
        self.exit_btn.clicked.connect(self._on_exit)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: 1px solid #ccc;
                border-radius: 6px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #eee;
            }
        """)

        self.agree_btn = QPushButton(DISCLAIMER_AGREE)
        self.agree_btn.clicked.connect(self._on_agree)
        self.agree_btn.setEnabled(False)
        self.agree_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: none;
                border-radius: 6px;
                background-color: #1976d2;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #90caf9;
            }
        """)

        btn_layout.addWidget(self.exit_btn)
        btn_layout.addWidget(self.agree_btn)
        layout.addLayout(btn_layout)

    def _on_checkbox(self, state):
        self.agree_btn.setEnabled(state == Qt.CheckState.Checked.value)

    def _on_agree(self):
        self._accepted = True
        self.accept()

    def _on_exit(self):
        self._accepted = False
        self.reject()

    def closeEvent(self, event):
        if not self._accepted:
            QApplication.quit()
            event.accept()
        else:
            super().closeEvent(event)


def should_show_disclaimer() -> bool:
    """检查是否需要显示免责声明"""
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    return settings.value("disclaimer/accepted", False, type=bool) is False


def mark_disclaimer_accepted():
    """标记免责声明已接受"""
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    settings.setValue("disclaimer/accepted", True)
    settings.sync()
