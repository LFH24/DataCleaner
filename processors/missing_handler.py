"""
⑭ 缺失值处理 — 智能选择均值/中位数/众数/插值/删除
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ColumnType, ChangeRecord
from processors.base import BaseProcessor
from config import (
    MISSING_RATIO_DROP_COL, MISSING_RATIO_DROP_ROW,
    SKEW_THRESHOLD,
)


class MissingHandler(BaseProcessor):
    name = "missing_handler"
    label = "缺失值处理"
    description = "智能选择均值/中位数/众数/插值/删除，可逐列覆写"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "strategy": "auto",              # "auto" | "mean" | "median" | "mode" | "drop_rows" | "drop_cols" | "ffill" | "bfill" | "interpolate"
            "drop_col_threshold": MISSING_RATIO_DROP_COL,
            "drop_row_threshold": MISSING_RATIO_DROP_ROW,
            "skew_threshold": SKEW_THRESHOLD,
            "column_overrides": {},           # {col_name: strategy} 逐列覆写
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        for col in df.columns:
            series = df[col]
            missing_count = series.isna().sum()
            if missing_count == 0:
                continue

            missing_ratio = missing_count / len(df)

            # 检查逐列覆写
            if col in config.get("column_overrides", {}):
                strategy = config["column_overrides"][col]
            elif config["strategy"] == "auto":
                strategy = self._auto_strategy(model, col, missing_ratio)
            else:
                strategy = config["strategy"]

            changes.append(self._make_record(
                step_name=self.label, column=col,
                reason=f"缺失 {missing_count}/{len(df)} ({missing_ratio:.1%})，策略: {strategy}",
            ))

            # 执行策略
            if strategy == "drop_cols" or (strategy == "auto" and missing_ratio > config["drop_col_threshold"]):
                df = df.drop(columns=[col])
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"删除列（缺失率 {missing_ratio:.1%} > 阈值 {config['drop_col_threshold']:.0%}）",
                ))

            elif strategy == "drop_rows":
                before = len(df)
                df = df[df[col].notna()].reset_index(drop=True)
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"删除 {before - len(df)} 行含缺失值",
                ))

            elif strategy == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].mean()
                    df[col] = df[col].fillna(fill_val)
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"均值填充: {fill_val:.4f}",
                    ))

            elif strategy == "median":
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].median()
                    df[col] = df[col].fillna(fill_val)
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"中位数填充: {fill_val}",
                    ))

            elif strategy == "mode":
                mode_vals = df[col].mode()
                fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else "缺失"
                df[col] = df[col].fillna(fill_val)
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"众数填充: {fill_val}",
                ))

            elif strategy == "ffill":
                df[col] = df[col].ffill()
                changes.append(self._make_record(
                    step_name=self.label, column=col, reason="前向填充",
                ))

            elif strategy == "bfill":
                df[col] = df[col].bfill()
                changes.append(self._make_record(
                    step_name=self.label, column=col, reason="后向填充",
                ))

            elif strategy == "interpolate":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].interpolate(method="linear")
                    changes.append(self._make_record(
                        step_name=self.label, column=col, reason="线性插值填充",
                    ))

        model.df = df
        self._add_changes(model, changes)
        return model

    def _auto_strategy(self, model: DataModel, col: str, missing_ratio: float) -> str:
        """自动选择缺失值策略"""
        config = self.config

        if missing_ratio > config["drop_col_threshold"]:
            return "drop_cols"
        if missing_ratio > config["drop_row_threshold"]:
            return "drop_rows"

        col_type = model.column_types.get(col)

        if col_type == ColumnType.NUMERIC:
            profile = next((p for p in model.profiles if p.name == col), None)
            if profile and profile.skewness is not None and abs(profile.skewness) > config["skew_threshold"]:
                return "median"
            return "mean"

        elif col_type in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN):
            return "mode"

        elif col_type == ColumnType.DATETIME:
            return "ffill"

        else:
            return "mode"
