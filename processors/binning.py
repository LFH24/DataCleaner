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
            "kmeans_fill_strategy": "median",  # K-means 分箱前缺失值填充策略
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
                    # 记录缺失值数量并填充（填充值记录到变更日志）
                    missing_mask = df[col].isna()
                    missing_count = missing_mask.sum()
                    fill_val = df[col].median() if config.get("kmeans_fill_strategy") == "median" else df[col].mean()
                    filled_col = df[col].fillna(fill_val)

                    kbd = KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy="kmeans", random_state=42)
                    binned = kbd.fit_transform(filled_col.to_frame()).flatten()
                    binned = pd.Series(binned, index=df.index, dtype=int)
                    # 恢复缺失值（分箱结果中对应位置也置为缺失）
                    binned[missing_mask] = pd.NA
                    reason = f"K-means分箱 ({n_bins}箱"
                    if missing_count > 0:
                        reason += f", K-means分箱前以{fill_val}填充{missing_count}个缺失值"
                    reason += ")"

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
