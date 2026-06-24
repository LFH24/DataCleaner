"""
③ 类型检测与自动转换
逐列识别：数值 / 分类 / 日期 / 布尔 / 文本，并转换 pandas dtype
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional
from core.datamodel import DataModel, ColumnType, ColumnProfile, ChangeRecord
from processors.base import BaseProcessor
from config import (
    TYPE_DETECT_NUMERIC_RATIO,
    TYPE_DETECT_DATETIME_RATIO,
    CATEGORICAL_MAX_RATIO,
)

# 布尔值正则模式
BOOL_PATTERNS = {
    frozenset({"true", "false"}),
    frozenset({"yes", "no"}),
    frozenset({"y", "n"}),
    frozenset({"是", "否"}),
    frozenset({"真", "假"}),
    frozenset({"0", "1"}),
    frozenset({"1", "0"}),
    frozenset({"t", "f"}),
}


class TypeDetector(BaseProcessor):
    name = "type_detector"
    label = "类型检测与转换"
    description = "自动识别每列为数值/分类/日期/布尔/文本，并转换数据类型"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "auto_convert": True,
            "numeric_threshold": TYPE_DETECT_NUMERIC_RATIO,
            "datetime_threshold": TYPE_DETECT_DATETIME_RATIO,
            "categorical_max_ratio": CATEGORICAL_MAX_RATIO,
            "datetime_formats": None,  # None = auto
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        column_types: dict[str, ColumnType] = {}
        profiles: list[ColumnProfile] = []

        for col in df.columns:
            series = df[col]
            col_type = self._detect_type(series, config)
            column_types[col] = col_type

            if config["auto_convert"]:
                df[col], conv_changes = self._convert_column(
                    df[col], col, col_type, config
                )
                changes.extend(conv_changes)

            # 构建画像
            profile = self._build_profile(series, col, col_type)
            profiles.append(profile)

        model.df = df
        model.column_types = column_types
        model.profiles = profiles
        self._add_changes(model, changes)
        return model

    def _detect_type(self, series: pd.Series, config: dict) -> ColumnType:
        non_null = series.dropna()
        if len(non_null) == 0:
            return ColumnType.TEXT

        n = len(non_null)

        # 已是数值类型
        if pd.api.types.is_numeric_dtype(series):
            return ColumnType.NUMERIC

        # 已是日期类型
        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME

        # 已是布尔类型
        if pd.api.types.is_bool_dtype(series):
            return ColumnType.BOOLEAN

        str_series = series.astype(str)

        # 1. 尝试日期检测
        dt = pd.to_datetime(str_series, errors="coerce", )
        dt_ratio = dt.notna().mean()
        if dt_ratio >= config["datetime_threshold"]:
            return ColumnType.DATETIME

        # 2. 尝试数值检测
        num = pd.to_numeric(str_series, errors="coerce")
        num_ratio = num.notna().mean()
        if num_ratio >= config["numeric_threshold"]:
            return ColumnType.NUMERIC

        # 3. 布尔检测
        unique_vals = set(str(v).strip().lower() for v in non_null.unique())
        for bp in BOOL_PATTERNS:
            if unique_vals.issubset(bp) or unique_vals == bp:
                return ColumnType.BOOLEAN
        # 特殊：0/1 且无其他值
        if unique_vals in ({'0', '1'},) and n > 2:
            return ColumnType.BOOLEAN

        # 4. 分类检测
        if non_null.nunique() / n < config["categorical_max_ratio"]:
            return ColumnType.CATEGORICAL

        return ColumnType.TEXT

    def _convert_column(
        self, series: pd.Series, col: str, col_type: ColumnType, config: dict
    ) -> tuple[pd.Series, list[ChangeRecord]]:
        changes: list[ChangeRecord] = []

        if col_type == ColumnType.NUMERIC:
            original = series.astype(str)
            new = pd.to_numeric(series, errors="coerce")
            for i in series.index:
                if pd.isna(new.loc[i]) and not pd.isna(series.loc[i]):
                    changes.append(self._make_record(
                        step_name=self.label, column=col, row_index=i,
                        original_value=series.loc[i], new_value="NaN (转换失败)",
                        reason="无法转换为数值",
                    ))
            return new, changes

        elif col_type == ColumnType.DATETIME:
            original = series.astype(str)
            new = pd.to_datetime(series, errors="coerce", )
            for i in series.index:
                if pd.isna(new.loc[i]) and not pd.isna(series.loc[i]):
                    changes.append(self._make_record(
                        step_name=self.label, column=col, row_index=i,
                        original_value=series.loc[i], new_value="NaT (转换失败)",
                        reason="无法转换为日期",
                    ))
            return new, changes

        elif col_type == ColumnType.BOOLEAN:
            mapping = {
                "true": True, "false": False, "yes": True, "no": False,
                "y": True, "n": False, "是": True, "否": False,
                "真": True, "假": False, "1": True, "0": False,
                "t": True, "f": False,
            }
            s = series.astype(str).str.strip().str.lower()
            new = s.map(mapping)
            new = new.astype("boolean")  # pandas nullable boolean
            return new, changes

        elif col_type == ColumnType.CATEGORICAL:
            return series.astype("category"), changes

        return series, changes

    def _build_profile(
        self, series: pd.Series, col: str, col_type: ColumnType
    ) -> ColumnProfile:
        profile = ColumnProfile(
            name=col,
            detected_type=col_type,
            dtype=str(series.dtype),
            count=len(series),
            missing_count=int(series.isna().sum()),
            unique_count=int(series.nunique(dropna=True)),
        )

        if col_type == ColumnType.NUMERIC:
            s = pd.to_numeric(series, errors="coerce")
            profile.mean = float(s.mean()) if not s.isna().all() else None
            profile.median = float(s.median()) if not s.isna().all() else None
            profile.std = float(s.std()) if not s.isna().all() else None
            profile.min_val = float(s.min()) if not s.isna().all() else None
            profile.max_val = float(s.max()) if not s.isna().all() else None
            from scipy.stats import skew
            clean = s.dropna()
            if len(clean) > 2:
                try:
                    profile.skewness = float(skew(clean))
                except Exception:
                    profile.skewness = None

        # Top 5 频次值
        try:
            top5 = series.value_counts(dropna=True).head(5)
            profile.top_values = [(str(k), int(v)) for k, v in top5.items()]
        except Exception:
            pass

        return profile
