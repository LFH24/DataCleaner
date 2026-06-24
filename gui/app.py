"""
QApplication 启动 & 免责声明弹窗
"""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from gui.main_window import MainWindow
from gui.disclaimer_dialog import DisclaimerDialog, should_show_disclaimer, mark_disclaimer_accepted
from config import APP_NAME


def launch_gui():
    """启动 GUI 应用"""
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DataPreprocessor")

    # 显示免责声明
    if should_show_disclaimer():
        dialog = DisclaimerDialog()
        if dialog.exec() != DisclaimerDialog.DialogCode.Accepted:
            sys.exit(0)
        mark_disclaimer_accepted()

    # 启动主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
