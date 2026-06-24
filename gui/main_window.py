"""
主窗口 — 拖放区 + 配置面板 + 预览表格 + 日志
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QTableView, QLabel,
    QStatusBar, QMenuBar, QMenu, QToolBar, QPushButton,
    QHeaderView, QTextEdit, QMessageBox, QFileDialog, QProgressBar,
    QAbstractItemView, QFrame,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QColor

from core.datamodel import DataModel, ChangeRecord
from core.io_handler import save_file
from core.report import generate_text_report
from gui.drop_area import DropArea
from gui.pipeline_config import PipelineConfigPanel
from gui.workers import LoadWorker, ProcessWorker
from gui.styles import get_stylesheet
from config import APP_NAME, APP_VERSION, PREVIEW_ROWS_PER_PAGE, EXPORT_FORMATS


class PandasTableModel(QAbstractTableModel):
    """懒加载 Pandas DataFrame 的表格模型"""

    def __init__(self, df=None):
        super().__init__()
        self._df = df
        self._fetched_rows = 0
        self._chunk_size = PREVIEW_ROWS_PER_PAGE

    def set_df(self, df):
        self.beginResetModel()
        self._df = df
        self._fetched_rows = 0
        self.endResetModel()

    def get_df(self):
        return self._df

    def rowCount(self, parent=QModelIndex()):
        if self._df is None:
            return 0
        return min(self._fetched_rows, len(self._df))

    def columnCount(self, parent=QModelIndex()):
        if self._df is None:
            return 0
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._df is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            return str(val) if val is not None else ""
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and self._df is not None:
                return str(self._df.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def canFetchMore(self, index=QModelIndex()):
        if self._df is None:
            return False
        return self._fetched_rows < len(self._df)

    def fetchMore(self, index=QModelIndex()):
        remainder = len(self._df) - self._fetched_rows
        items_to_fetch = min(self._chunk_size, remainder)
        if items_to_fetch <= 0:
            return
        begin = self._fetched_rows
        self.beginInsertRows(QModelIndex(), begin, begin + items_to_fetch - 1)
        self._fetched_rows += items_to_fetch
        self.endInsertRows()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        self._model: DataModel | None = None
        self._original_model: DataModel | None = None
        self._is_processing = False

        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()

        self.setStyleSheet(get_stylesheet())

    # ---- 菜单栏 ----
    def _setup_menu_bar(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        open_action = QAction("打开(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("导出处理结果(&E)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_export)
        file_menu.addAction(save_action)

        save_report_action = QAction("导出处理报告(&R)", self)
        save_report_action.setShortcut("Ctrl+Shift+S")
        save_report_action.triggered.connect(self._on_export_report)
        file_menu.addAction(save_report_action)

        file_menu.addSeparator()
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ---- 工具栏 ----
    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_btn = QPushButton("📂 打开")
        open_btn.clicked.connect(self._on_open)
        toolbar.addWidget(open_btn)

        self.run_btn = QPushButton("▶  开始处理")
        self.run_btn.setObjectName("runButton")
        self.run_btn.clicked.connect(self._on_run)
        self.run_btn.setEnabled(False)
        toolbar.addWidget(self.run_btn)

        export_btn = QPushButton("💾 导出")
        export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(export_btn)

        toolbar.addSeparator()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)

    # ---- 中央区域 ----
    def _setup_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # === 左侧面板 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)

        # 拖放区域
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self._on_file_dropped)
        left_layout.addWidget(self.drop_area)

        # 文件信息
        self.file_info_label = QLabel("")
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet("font-size: 11px; color: #888; padding: 4px;")
        left_layout.addWidget(self.file_info_label)

        # 配置面板
        self.config_panel = PipelineConfigPanel()
        left_layout.addWidget(self.config_panel, 1)

        main_splitter.addWidget(left_widget)

        # === 右侧面板 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)

        self.tab_widget = QTabWidget()

        # Tab 1: 数据预览
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_model = PandasTableModel()
        self.table_view.setModel(self.table_model)
        self.tab_widget.addTab(self.table_view, "📋 数据预览")

        # Tab 2: 处理日志
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: monospace; font-size: 12px;")
        self.tab_widget.addTab(self.log_view, "📝 处理日志")

        right_layout.addWidget(self.tab_widget, 1)

        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([350, 850])

        main_layout = QHBoxLayout(central)
        main_layout.addWidget(main_splitter)

    # ---- 状态栏 ----
    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)

        self.shape_label = QLabel("")
        self.statusbar.addPermanentWidget(self.shape_label)

        self.missing_label = QLabel("")
        self.statusbar.addPermanentWidget(self.missing_label)

    # ---- 槽函数 ----
    @Slot(str)
    def _on_file_dropped(self, file_path: str):
        """文件拖放或选择后加载"""
        self.status_label.setText("正在加载文件...")
        self.run_btn.setEnabled(False)
        self.drop_area.setEnabled(False)

        self._load_worker = LoadWorker(file_path)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self._load_worker.start()

    @Slot(object)
    def _on_load_finished(self, model: DataModel):
        self._model = model
        self._original_model = DataModel(
            df=model.df.copy(),
            original_df=model.df.copy(),
            metadata=dict(model.metadata),
        )
        self.run_btn.setEnabled(True)
        self.drop_area.setEnabled(True)

        # 更新表格
        self.table_model.set_df(model.df)
        self.table_view.resizeColumnsToContents()

        # 更新信息
        file_name = model.metadata.get("file_name", "")
        encoding = model.metadata.get("encoding", "?")
        size_mb = model.metadata.get("file_size", 0) / (1024 * 1024)
        self.file_info_label.setText(
            f"📄 {file_name}\n"
            f"📐 {model.rows} 行 × {model.cols} 列\n"
            f"🔤 编码: {encoding}\n"
            f"💾 {size_mb:.1f} MB"
        )

        self.shape_label.setText(f"行列: {model.rows} × {model.cols}")
        self.missing_label.setText(f"缺失值: {model.df.isna().sum().sum()}")
        self.status_label.setText(f"加载完成: {file_name}")

        self.log_view.clear()
        self.log_view.append(f"✅ 文件加载成功: {file_name}")
        self.log_view.append(f"   维度: {model.rows} 行 × {model.cols} 列")
        self.log_view.append("")

    @Slot(str)
    def _on_load_error(self, error_msg: str):
        self.run_btn.setEnabled(False)
        self.drop_area.setEnabled(True)
        self.status_label.setText("加载失败")
        QMessageBox.critical(self, "加载错误", f"无法加载文件:\n{error_msg}")

    @Slot()
    def _on_run(self):
        """运行处理流水线"""
        if self._model is None:
            return

        self._is_processing = True
        self.run_btn.setEnabled(False)
        self.status_label.setText("正在处理...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        enabled_steps = self.config_panel.get_enabled_steps()
        step_configs = self.config_panel.get_step_configs()

        enabled_count = sum(1 for v in enabled_steps.values() if v)
        self.progress_bar.setMaximum(enabled_count)

        self._process_worker = ProcessWorker(
            self._original_model or self._model,
            enabled_steps,
            step_configs,
        )
        self._process_worker.step_completed.connect(self._on_step_done)
        self._process_worker.finished.connect(self._on_process_finished)
        self._process_worker.error.connect(self._on_process_error)
        self._process_worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self._process_worker.start()

    @Slot(int, str)
    def _on_step_done(self, index: int, label: str):
        self.progress_bar.setValue(index + 1)
        self.log_view.append(f"  [{index + 1:02d}] {label}")

    @Slot(object)
    def _on_process_finished(self, model: DataModel):
        self._model = model
        self._is_processing = False
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理完成")

        # 更新表格
        self.table_model.set_df(model.df)
        self.table_view.resizeColumnsToContents()

        self.shape_label.setText(f"行列: {model.rows} × {model.cols}")
        self.missing_label.setText(f"缺失值: {model.df.isna().sum().sum()}")

        # 更新日志
        self.log_view.append("")
        self.log_view.append("=" * 50)
        self.log_view.append(f"处理完成，共 {len(model.change_log)} 处变更")

        from collections import Counter
        steps = Counter(c.step_name for c in model.change_log)
        for step, count in steps.items():
            self.log_view.append(f"  [{step}]: {count} 处变更")

        self.log_view.append("")
        self.log_view.append("--- 详细变更 ---")
        for c in model.change_log:
            line = f"  [{c.step_name}]"
            if c.column:
                line += f" 列「{c.column}」"
            if c.row_index is not None:
                line += f" 第{c.row_index}行"
            if c.reason:
                line += f"  {c.reason}"
            self.log_view.append(line)

        QMessageBox.information(
            self, "处理完成",
            f"数据预处理完成！\n\n"
            f"共进行了 {len(model.change_log)} 处变更。\n"
            f"请切换到「📝 处理日志」标签页查看详情。"
        )

    @Slot(str)
    def _on_process_error(self, error_msg: str):
        self._is_processing = False
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理出错")
        self.log_view.append(f"❌ 错误: {error_msg}")
        QMessageBox.critical(self, "处理错误", f"处理过程中发生错误:\n{error_msg}")

    @Slot()
    def _on_open(self):
        """打开文件对话框"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "数据文件 (*.csv *.tsv *.xlsx *.xls *.json *.parquet *.dta *.dat);;所有文件 (*.*)",
        )
        if file_path:
            self.drop_area.reset()
            self._on_file_dropped(file_path)

    @Slot()
    def _on_export(self):
        """导出处理结果"""
        if self._model is None:
            QMessageBox.warning(self, "无数据", "请先加载并处理数据。")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出处理结果",
            "",
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;JSON 文件 (*.json);;TSV 文件 (*.tsv)",
        )
        if file_path:
            try:
                save_file(self._model.df, file_path)
                self.status_label.setText(f"已导出: {os.path.basename(file_path)}")
                QMessageBox.information(self, "导出成功", f"数据已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    @Slot()
    def _on_export_report(self):
        """导出处理报告"""
        if self._model is None:
            QMessageBox.warning(self, "无数据", "请先加载并处理数据。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出处理报告",
            "处理报告.txt",
            "文本文件 (*.txt);;JSON 文件 (*.json)",
        )
        if file_path:
            try:
                if file_path.endswith(".json"):
                    from core.report import generate_json_report
                    import json
                    report = generate_json_report(self._model)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(report, f, ensure_ascii=False, indent=2)
                else:
                    report = generate_text_report(self._model)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report)
                self.status_label.setText(f"报告已导出: {os.path.basename(file_path)}")
                QMessageBox.information(self, "导出成功", f"处理报告已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    @Slot()
    def _on_about(self):
        QMessageBox.about(
            self, f"关于 {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>自动化数据预处理工具</p>"
            f"<p>功能：编码规范化、类型检测、单位剥离、百分号统一、"
            f"小数位统一、异常值检测、缺失值处理、特征工程等。</p>"
            f"<p>纯离线工具，所有数据处理均在本地完成。</p>",
        )

    def closeEvent(self, event):
        if self._is_processing:
            reply = QMessageBox.question(
                self, "确认退出",
                "处理正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()
