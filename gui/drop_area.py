"""
拖放区域组件 — 接受 CSV/XLSX 等文件拖放
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QFont

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet", ".dta", ".dat"}


class DropArea(QFrame):
    """可拖放文件的目标区域"""

    file_dropped = Signal(str)  # 发射文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setMaximumHeight(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_hovering = False
        self._file_path: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图标符号
        self.icon_label = QLabel("📂")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 36px;")
        layout.addWidget(self.icon_label)

        # 提示文字
        self.label = QLabel("拖放数据文件到此处\n或点击选择文件")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            "font-size: 15px; color: #666; padding: 8px;"
        )

        layout.addWidget(self.label)

        self.hint = QLabel(f"支持格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setStyleSheet("font-size: 11px; color: #999;")
        layout.addWidget(self.hint)

        self.setStyleSheet("""
            QFrame {
                border: 3px dashed #bbb;
                border-radius: 12px;
                background-color: #fafafa;
            }
            QFrame:hover {
                border-color: #1976d2;
                background-color: #f0f7ff;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._is_hovering:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("#1976d2"), 3)
            painter.setPen(pen)
            painter.drawRoundedRect(3, 3, self.width() - 6, self.height() - 6, 12, 12)
            painter.end()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self._is_hovering = True
                    self.update()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._is_hovering = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._is_hovering = False
        self.update()

        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    self._file_path = file_path
                    self._update_display(file_path)
                    self.file_dropped.emit(file_path)

    def mousePressEvent(self, event):
        """点击选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "数据文件 (*.csv *.tsv *.xlsx *.xls *.json *.parquet *.dta *.dat);;"
            "CSV 文件 (*.csv);;"
            "Excel 文件 (*.xlsx *.xls);;"
            "所有文件 (*.*)",
        )
        if file_path:
            self._file_path = file_path
            self._update_display(file_path)
            self.file_dropped.emit(file_path)

    def _update_display(self, file_path: str):
        basename = os.path.basename(file_path)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.icon_label.setText("📋")
        self.label.setText(f"{basename}\n{size_mb:.1f} MB")
        self.label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2; padding: 8px;")
        self.hint.setText("点击可重新选择文件")

    def reset(self):
        self._file_path = None
        self.icon_label.setText("📂")
        self.label.setText("拖放数据文件到此处\n或点击选择文件")
        self.label.setStyleSheet("font-size: 15px; color: #666; padding: 8px;")
        self.hint.setText(f"支持格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
