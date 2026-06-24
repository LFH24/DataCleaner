"""
ProcessingPipeline — 流水线编排器
按顺序执行处理器，累积变更日志
"""
from __future__ import annotations

import time
from typing import Callable, Optional
from core.datamodel import DataModel
from core.io_handler import load_file
from core.report import generate_text_report, generate_json_report
from processors.base import BaseProcessor

# 按顺序导入所有处理器
from processors.encoding_normalizer import EncodingNormalizer
from processors.column_name_cleaner import ColumnNameCleaner
from processors.type_detector import TypeDetector
from processors.id_column_detector import IdColumnDetector
from processors.text_standardizer import TextStandardizer
from processors.datetime_standardizer import DatetimeStandardizer
from processors.value_replacer import ValueReplacer
from processors.duplicate_handler import DuplicateHandler
from processors.constant_remover import ConstantRemover
from processors.unit_detector import UnitDetector
from processors.percentage_unifier import PercentageUnifier
from processors.decimal_unifier import DecimalUnifier
from processors.outlier_detector import OutlierDetector
from processors.missing_handler import MissingHandler
from processors.feature_scaler import FeatureScaler
from processors.skewness_corrector import SkewnessCorrector
from processors.binning import Binning
from processors.categorical_encoder import CategoricalEncoder
from processors.correlation_analyzer import CorrelationAnalyzer
from processors.profiler import Profiler


# 处理器注册表（按执行顺序）
PROCESSOR_REGISTRY: list[type[BaseProcessor]] = [
    EncodingNormalizer,
    ColumnNameCleaner,
    TypeDetector,
    IdColumnDetector,
    TextStandardizer,
    DatetimeStandardizer,
    ValueReplacer,
    DuplicateHandler,
    ConstantRemover,
    UnitDetector,
    PercentageUnifier,
    DecimalUnifier,
    OutlierDetector,
    MissingHandler,
    FeatureScaler,
    SkewnessCorrector,
    Binning,
    CategoricalEncoder,
    CorrelationAnalyzer,
    Profiler,
]


class ProcessingPipeline:
    """数据处理流水线"""

    def __init__(
        self,
        enabled_steps: Optional[dict[str, bool]] = None,
        step_configs: Optional[dict[str, dict]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        """
        enabled_steps: {processor_name: enabled}
        step_configs: {processor_name: config_dict}
        progress_callback: (step_index, step_label) -> None
        """
        self.enabled_steps = enabled_steps or {}
        self.step_configs = step_configs or {}
        self.progress_callback = progress_callback
        self._processors: list[BaseProcessor] = []

    def _build_processors(self) -> list[BaseProcessor]:
        """根据配置构建处理器实例列表"""
        processors = []
        for cls in PROCESSOR_REGISTRY:
            name = cls.name
            # user override takes priority; fall back to class default
            if name in self.enabled_steps:
                if not self.enabled_steps[name]:
                    continue  # user disabled
            elif not cls.enabled:
                continue  # default disabled and user didn't enable
            cfg = self.step_configs.get(name, {})
            processor = cls(config=cfg if cfg else None)
            processors.append(processor)
        return processors

    def run(self, model: DataModel) -> DataModel:
        """运行完整流水线"""
        self._processors = self._build_processors()

        for i, processor in enumerate(self._processors):
            if self.progress_callback:
                self.progress_callback(i, processor.label)

            model = processor.process(model)

        return model

    def run_step_by_step(self, model: DataModel) -> list[DataModel]:
        """逐步运行，返回每个步骤的结果（用于撤销）"""
        self._processors = self._build_processors()
        snapshots = [model]

        for processor in self._processors:
            model = processor.process(model)
            snapshots.append(model)

        return snapshots

    def get_report(self, model: DataModel) -> str:
        return generate_text_report(model)

    def get_report_json(self, model: DataModel) -> dict:
        return generate_json_report(model)

    @staticmethod
    def get_processor_list() -> list[dict]:
        """返回所有处理器元数据（供 GUI 使用）"""
        result = []
        for cls in PROCESSOR_REGISTRY:
            result.append({
                "name": cls.name,
                "label": cls.label,
                "description": cls.description,
                "has_config": cls.has_config,
                "default_enabled": hasattr(cls, "enabled") and cls.enabled,
                "default_config": cls.default_config(),
            })
        return result


def run_pipeline(
    file_path: str,
    enabled_steps: Optional[dict[str, bool]] = None,
    step_configs: Optional[dict[str, dict]] = None,
    encoding: str = "auto",
) -> DataModel:
    """
    便捷函数：加载文件 → 运行流水线 → 返回处理后的 DataModel
    """
    df, metadata = load_file(file_path, encoding=encoding)
    model = DataModel(df=df, metadata=metadata)

    pipeline = ProcessingPipeline(
        enabled_steps=enabled_steps,
        step_configs=step_configs,
    )
    return pipeline.run(model)
