"""
DataModel — 不可变风格的数据包装器
包装 DataFrame + 列类型元数据 + 变更日志
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import pandas as pd


class ColumnType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    MIXED = "mixed"


@dataclass
class ColumnProfile:
    """单列的统计画像"""
    name: str
    detected_type: ColumnType
    dtype: str = ""
    count: int = 0
    missing_count: int = 0
    unique_count: int = 0
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_val: Any = None
    max_val: Any = None
    skewness: Optional[float] = None
    top_values: list[tuple[Any, int]] = field(default_factory=list)

    @property
    def missing_ratio(self) -> float:
        if self.count == 0:
            return 1.0
        return self.missing_count / self.count


@dataclass
class ChangeRecord:
    """单条变更记录"""
    step_name: str
    column: Optional[str] = None
    row_index: Optional[int] = None
    original_value: Any = None
    new_value: Any = None
    reason: str = ""


class DataModel:
    """
    不可变风格的数据模型。
    每个处理步骤返回一个新的 DataModel（内部共享 df 副本）。
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        original_df: Optional[pd.DataFrame] = None,
        column_types: Optional[dict[str, ColumnType]] = None,
        id_columns: Optional[set[str]] = None,
        profiles: Optional[list[ColumnProfile]] = None,
        change_log: Optional[list[ChangeRecord]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.df = df.copy()
        self.original_df = original_df if original_df is not None else df.copy()
        self.column_types = column_types or {}
        self.id_columns = id_columns or set()
        self.profiles = profiles or []
        self.change_log = change_log or []
        self.metadata = metadata or {}

    @property
    def shape(self) -> tuple[int, int]:
        return self.df.shape

    @property
    def rows(self) -> int:
        return self.df.shape[0]

    @property
    def cols(self) -> int:
        return self.df.shape[1]

    def get_preview(self, rows: int = 100, offset: int = 0) -> pd.DataFrame:
        """分页获取预览数据"""
        end = min(offset + rows, self.rows)
        return self.df.iloc[offset:end]

    def add_changes(self, records: list[ChangeRecord]) -> None:
        self.change_log.extend(records)

    def summary(self) -> dict:
        """生成数据摘要"""
        return {
            "rows": self.rows,
            "cols": self.cols,
            "columns": list(self.df.columns),
            "dtypes": {c: str(t) for c, t in self.df.dtypes.items()},
            "missing_total": int(self.df.isna().sum().sum()),
            "metadata": self.metadata,
        }
