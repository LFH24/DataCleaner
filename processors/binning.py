"""
⑰ 分箱离散化 — 等宽 / 等频 / K-means 分箱
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import DEFAULT_BINS


class Binning(BaseProcessor):
    name = "binning"
    label = "分箱离散化"
    description = "等宽/等频/K-means分箱"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "equal_width",       # "equal_width" | "equal_freq" | "kmeans"
            "bins": DEFAULT_BINS,
            "labels": None,                # None=自动生成; list[str]=自定义标签
            "output_mode": "replace",      # "replace" | "new_column"
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        method = config["method"]
        n_bins = config["bins"]
        output_mode = config["output_mode"]

        numeric_cols = [
            c for c in self.get_numeric_columns(model)
            if c not in model.id_columns
        ]

        for col in numeric_cols:
            clean = df[col].dropna()
            if len(clean) < n_bins * 3:
                continue
            if clean.nunique() < n_bins:
                continue

            try:
                if method == "equal_width":
                    binned, edges = pd.cut(df[col], bins=n_bins, retbins=True, labels=False, duplicates="drop")
                    edge_str = ", ".join([f"{e:.2f}" for e in edges])
                    reason = f"等宽分箱 ({n_bins}箱, 边界: [{edge_str}])"

                elif method == "equal_freq":
                    binned, edges = pd.qcut(df[col].rank(method="first"), q=n_bins, retbins=True, labels=False, duplicates="drop")
                    edge_str = ", ".join([f"{e:.2f}" for e in edges])
                    reason = f"等频分箱 ({n_bins}箱)"

                elif method == "kmeans":
                    from sklearn.preprocessing import KBinsDiscretizer
                    kbd = KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy="kmeans", random_state=42)
                    binned = kbd.fit_transform(df[[col]].fillna(df[col].median())).flatten()
                    binned = pd.Series(binned, index=df.index, dtype=int)
                    reason = f"K-means分箱 ({n_bins}箱)"

                else:
                    continue

                new_col = f"{col}_bin"
                df[new_col] = binned.astype("Int64")  # nullable int

                if output_mode == "replace":
                    df = df.drop(columns=[col])

                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=reason,
                ))

            except Exception as e:
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"分箱失败: {e}",
                ))

        model.df = df
        self._add_changes(model, changes)
        return model
