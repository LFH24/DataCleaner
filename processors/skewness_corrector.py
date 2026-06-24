"""
⑯ 偏度校正 — Log / Box-Cox / Yeo-Johnson 变换
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import SKEW_THRESHOLD


class SkewnessCorrector(BaseProcessor):
    name = "skewness_corrector"
    label = "偏度校正"
    description = "对偏态数值列做Log/Box-Cox/Yeo-Johnson变换"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "yeo_johnson",       # "log" | "box_cox" | "yeo_johnson"
            "skew_threshold": SKEW_THRESHOLD,
            "only_if_skewed": True,        # 只校正偏度超过阈值的列
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        method = config["method"]

        numeric_cols = [
            c for c in self.get_numeric_columns(model)
            if c not in model.id_columns
        ]

        for col in numeric_cols:
            clean = df[col].dropna()
            if len(clean) < 10:
                continue

            skew_val = stats.skew(clean)
            if config["only_if_skewed"] and abs(skew_val) < config["skew_threshold"]:
                continue

            try:
                if method == "log":
                    min_val = clean.min()
                    offset = abs(min_val) + 1 if min_val <= 0 else 0
                    transformed = np.log(df[col] + offset)
                    note = f" (offset={offset})" if offset > 0 else ""
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"Log变换 (偏度={skew_val:.2f}{note})",
                    ))

                elif method == "box_cox":
                    min_val = clean.min()
                    if min_val <= 0:
                        # Box-Cox 要求所有值为正；加 offset 使其为正，不事后减去
                        offset = abs(min_val) + 1
                        shifted = clean + offset
                        transformed_arr, lam = stats.boxcox(shifted)
                        transformed = pd.Series(transformed_arr, index=clean.index)
                        transformed = transformed.reindex(df.index)
                        changes.append(self._make_record(
                            step_name=self.label, column=col,
                            reason=f"Box-Cox变换 (偏度={skew_val:.2f}, λ={lam:.4f}, offset={offset}) — 值域已平移",
                        ))
                    else:
                        transformed_arr, lam = stats.boxcox(clean)
                        transformed = pd.Series(transformed_arr, index=clean.index)
                        transformed = transformed.reindex(df.index)
                        changes.append(self._make_record(
                            step_name=self.label, column=col,
                            reason=f"Box-Cox变换 (偏度={skew_val:.2f}, λ={lam:.4f})",
                        ))

                elif method == "yeo_johnson":
                    transformed_arr, lam = stats.yeojohnson(clean)
                    transformed = pd.Series(transformed_arr, index=clean.index)
                    transformed = transformed.reindex(df.index)
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"Yeo-Johnson变换 (偏度={skew_val:.2f}, λ={lam:.4f})",
                    ))
                else:
                    continue

                df[col] = transformed

            except Exception as e:
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"变换失败: {e}",
                ))

        model.df = df
        self._add_changes(model, changes)
        return model
