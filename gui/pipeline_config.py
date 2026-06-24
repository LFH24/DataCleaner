"""
处理步骤配置面板 — 分组的复选框 + 配置按钮
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QPushButton, QScrollArea, QGroupBox, QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from config import PROCESSOR_META
from core.pipeline import PROCESSOR_REGISTRY


class PipelineConfigPanel(QScrollArea):
    """可滚动的处理步骤配置面板"""

    config_changed = Signal()  # 配置变更信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(280)

        self._checkboxes: dict[str, QCheckBox] = {}
        self._config_buttons: dict[str, QPushButton] = {}
        self._step_configs: dict[str, dict] = {}

        self._setup_ui()

    def _setup_ui(self):
        container = QWidget()
        container.setObjectName("configContainer")
        self.setWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 标题
        title = QLabel("处理配置")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; padding: 4px;")
        main_layout.addWidget(title)

        # 按阶段分组
        stages: dict[str, list] = {}
        for meta in PROCESSOR_META:
            stage_key = meta[0]
            if stage_key not in stages:
                stages[stage_key] = {"label": meta[1], "items": []}
            stages[stage_key]["items"].append(meta)

        for stage_key, stage_data in stages.items():
            group = QGroupBox(stage_data["label"])
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    margin-top: 8px;
                    padding-top: 16px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background-color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 6px;
                    color: #555;
                }
            """)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(2)
            group_layout.setContentsMargins(8, 12, 8, 8)

            for meta in stage_data["items"]:
                _, _, proc_key, proc_label, proc_desc, default_enabled, has_config = meta

                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)

                cb = QCheckBox(proc_label)
                cb.setChecked(default_enabled)
                cb.setToolTip(proc_desc)
                cb.stateChanged.connect(self.config_changed.emit)
                self._checkboxes[proc_key] = cb
                row.addWidget(cb, 1)

                if has_config:
                    btn = QPushButton("⚙")
                    btn.setFixedSize(28, 28)
                    btn.setToolTip(f"配置: {proc_label}")
                    btn.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            background-color: #f8f8f8;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #e3f2fd;
                            border-color: #1976d2;
                        }
                    """)
                    btn.clicked.connect(lambda checked, k=proc_key, l=proc_label: self._on_config(k, l))
                    self._config_buttons[proc_key] = btn
                    row.addWidget(btn)

                group_layout.addLayout(row)

            main_layout.addWidget(group)

        main_layout.addStretch()

        # 快捷按钮
        btn_layout = QHBoxLayout()
        select_all = QPushButton("全选")
        select_all.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        select_all.clicked.connect(self._select_all)
        select_none = QPushButton("全不选")
        select_none.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        select_none.clicked.connect(self._select_none)
        restore = QPushButton("恢复默认")
        restore.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        restore.clicked.connect(self._restore_defaults)

        btn_layout.addWidget(select_all)
        btn_layout.addWidget(select_none)
        btn_layout.addWidget(restore)
        main_layout.addLayout(btn_layout)

    def get_enabled_steps(self) -> dict[str, bool]:
        """返回 {processor_name: enabled}"""
        return {key: cb.isChecked() for key, cb in self._checkboxes.items()}

    def get_step_configs(self) -> dict[str, dict]:
        """返回 {processor_name: config_dict}"""
        return dict(self._step_configs)

    def _on_config(self, proc_key: str, proc_label: str):
        """弹出配置对话框"""
        cls = None
        for c in PROCESSOR_REGISTRY:
            if c.name == proc_key:
                cls = c
                break
        if cls is None:
            return

        # 目前显示一个简单的消息框，后续可替换为定制对话框
        current_config = self._step_configs.get(proc_key, cls.default_config())
        config_str = "\n".join([f"  {k}: {v}" for k, v in current_config.items()])

        msg = QMessageBox(self)
        msg.setWindowTitle(f"配置: {proc_label}")
        msg.setText(f"当前配置:\n{config_str}\n\n(详细配置界面将在后续版本中提供)")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _select_none(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _restore_defaults(self):
        for meta in PROCESSOR_META:
            proc_key = meta[2]
            default_enabled = meta[5]
            if proc_key in self._checkboxes:
                self._checkboxes[proc_key].setChecked(default_enabled)
