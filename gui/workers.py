"""
QThread 后台工作线程 — 文件加载 & 数据处理
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.datamodel import DataModel
from core.io_handler import load_file
from core.pipeline import ProcessingPipeline


class LoadWorker(QThread):
    """后台加载文件，避免界面卡死"""
    finished = Signal(object)   # DataModel
    error = Signal(str)
    progress = Signal(str)      # 状态消息

    def __init__(self, file_path: str, encoding: str = "auto"):
        super().__init__()
        self.file_path = file_path
        self.encoding = encoding

    def run(self):
        try:
            self.progress.emit("正在检测文件编码...")
            df, metadata = load_file(self.file_path, encoding=self.encoding)
            self.progress.emit(f"加载完成: {df.shape[0]} 行 × {df.shape[1]} 列")
            model = DataModel(df=df, metadata=metadata)
            self.finished.emit(model)
        except Exception as e:
            self.error.emit(str(e))


class ProcessWorker(QThread):
    """后台运行处理流水线"""
    finished = Signal(object)       # DataModel
    error = Signal(str)
    step_completed = Signal(int, str)  # step_index, step_label
    progress = Signal(str)          # 状态消息
    total_steps = Signal(int)

    def __init__(
        self,
        model: DataModel,
        enabled_steps: dict[str, bool],
        step_configs: dict[str, dict],
    ):
        super().__init__()
        self.model = model
        self.enabled_steps = enabled_steps
        self.step_configs = step_configs

    def run(self):
        try:
            pipeline = ProcessingPipeline(
                enabled_steps=self.enabled_steps,
                step_configs=self.step_configs,
                progress_callback=self._on_step,
            )
            result = pipeline.run(self.model)
            self.progress.emit("处理完成")
            self.finished.emit(result)
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n{traceback.format_exc()}")

    def _on_step(self, index: int, label: str):
        self.step_completed.emit(index, label)
        self.progress.emit(f"正在处理: {label}")
