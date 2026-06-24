"""
⑮ 特征缩放 — Standard / MinMax / Robust 缩放，跳过 ID 列
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor


class FeatureScaler(BaseProcessor):
    name = "feature_scaler"
    label = "特征缩放"
    description = "Standard/MinMax/Robust缩放，跳过ID列"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "standard",        # "standard" | "minmax" | "robust"
            "feature_range": (0, 1),     # MinMax 专用
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        method = config["method"]

        numeric_cols = [
            c for c in self.get_numeric_columns(model)
            if c not in model.id_columns and pd.api.types.is_numeric_dtype(df[c])
        ]
        if not numeric_cols:
            self._add_changes(model, changes)
            return model

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 2:
                continue

            if method == "standard":
                mean_val = series.mean()
                std_val = series.std()
                if std_val == 0 or pd.isna(std_val):
                    continue
                df[col] = (df[col] - mean_val) / std_val
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"StandardScaler: μ={mean_val:.4f}, σ={std_val:.4f}",
                ))

            elif method == "minmax":
                min_val = series.min()
                max_val = series.max()
                if max_val == min_val:
                    continue
                fmin, fmax = config.get("feature_range", (0, 1))
                df[col] = fmin + (df[col] - min_val) * (fmax - fmin) / (max_val - min_val)
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"MinMaxScaler: [{min_val:.4f}, {max_val:.4f}] → [{fmin}, {fmax}]",
                ))

            elif method == "robust":
                median_val = series.median()
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                df[col] = (df[col] - median_val) / iqr
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"RobustScaler: median={median_val:.4f}, IQR={iqr:.4f}",
                ))

        model.df = df
        self._add_changes(model, changes)
        return model
