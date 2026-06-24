"""
⑧ 常数列/低方差列删除
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import CONSTANT_UNIQUE_MAX, LOW_VARIANCE_THRESHOLD


class ConstantRemover(BaseProcessor):
    name = "constant_remover"
    label = "常数列删除"
    description = "删除唯一值极少或方差为零的列"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "max_unique_values": CONSTANT_UNIQUE_MAX,   # 最大唯一值数
            "remove_zero_variance": True,                # 删除方差为零的数值列
            "low_variance_threshold": LOW_VARIANCE_THRESHOLD,  # 低方差阈值
            "missing_dominant_ratio": 0.95,              # 缺失值占比 > 此值 → 删除
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        cols_to_drop: list[str] = []

        for col in df.columns:
            series = df[col]
            n = len(series)
            reasons = []

            # 1. 唯一值太少
            unique_count = series.nunique(dropna=True)
            if unique_count <= config["max_unique_values"]:
                reasons.append(f"唯一值仅 {unique_count} 个")
                if unique_count == 1:
                    reasons.append(f"所有值均为: {series.dropna().iloc[0] if not series.dropna().empty else '(空)'}")

            # 2. 数值列方差为零
            if config["remove_zero_variance"] and pd.api.types.is_numeric_dtype(series):
                try:
                    std = series.std()
                    if pd.isna(std) or std == 0:
                        reasons.append("方差为零")
                    elif std < config["low_variance_threshold"]:
                        reasons.append(f"方差极低 ({std:.6f})")
                except Exception:
                    pass

            # 3. 缺失值占绝大多数
            missing_ratio = series.isna().mean()
            if missing_ratio >= config["missing_dominant_ratio"]:
                reasons.append(f"缺失值占比 {missing_ratio:.1%}")

            if reasons:
                cols_to_drop.append(col)
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    reason="; ".join(reasons),
                ))

        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            # 清理元数据
            for col in cols_to_drop:
                model.column_types.pop(col, None)
                model.id_columns.discard(col)

            changes.append(self._make_record(
                step_name=self.label,
                reason=f"共删除 {len(cols_to_drop)} 列: {', '.join(cols_to_drop)}",
            ))

        model.df = df
        self._add_changes(model, changes)
        return model
