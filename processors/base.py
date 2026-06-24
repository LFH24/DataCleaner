"""
BaseProcessor — 所有处理器的抽象基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from core.datamodel import DataModel, ChangeRecord


class BaseProcessor(ABC):
    """每个处理步骤继承此类"""

    name: str = "base"                 # 处理器标识（英文）
    label: str = "基础处理器"           # 显示名称（中文）
    description: str = ""              # 功能描述
    enabled: bool = True               # 是否默认启用
    has_config: bool = False           # 是否有可配置参数
    config: dict[str, Any] = {}        # 配置参数

    def __init__(self, config: dict[str, Any] | None = None):
        if config is not None:
            self.config = {**self.default_config(), **config}
        else:
            self.config = self.default_config()

    @staticmethod
    def default_config() -> dict[str, Any]:
        """返回默认配置（子类覆写）"""
        return {}

    @abstractmethod
    def process(self, model: DataModel) -> DataModel:
        """处理数据，返回新 DataModel"""
        ...

    @staticmethod
    def _add_changes(model: DataModel, records: list[ChangeRecord]) -> None:
        model.change_log.extend(records)

    @staticmethod
    def _make_record(
        step_name: str,
        column: str | None = None,
        row_index: int | None = None,
        original_value: Any = None,
        new_value: Any = None,
        reason: str = "",
    ) -> ChangeRecord:
        return ChangeRecord(
            step_name=step_name,
            column=column,
            row_index=row_index,
            original_value=original_value,
            new_value=new_value,
            reason=reason,
        )

    # ---- 辅助方法供子类使用 ----

    def get_numeric_columns(self, model: DataModel) -> list[str]:
        """获取所有数值列"""
        return [
            c for c, t in model.column_types.items()
            if t.value == "numeric" and c not in model.id_columns
        ]

    def get_text_columns(self, model: DataModel) -> list[str]:
        """获取所有文本列"""
        return [
            c for c, t in model.column_types.items()
            if t.value in ("text", "mixed")
        ]

    def get_categorical_columns(self, model: DataModel) -> list[str]:
        """获取所有分类列"""
        return [
            c for c, t in model.column_types.items()
            if t.value == "categorical"
        ]
