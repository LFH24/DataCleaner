"""
⑫ 小数位数统一 — 按列自动检测合适小数位，或手动指定
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import DECIMAL_MAX, DECIMAL_MIN, DECIMAL_PERCENTILE


class DecimalUnifier(BaseProcessor):
    name = "decimal_unifier"
    label = "小数位数统一"
    description = "按列自动检测合适小数位，或手动指定"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "mode": "auto",
            "fixed_places": 2,
            "method": "round",
            "auto_percentile": DECIMAL_PERCENTILE,
            "decimal_min": DECIMAL_MIN,
            "decimal_max": DECIMAL_MAX,
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        numeric_cols = self.get_numeric_columns(model)

        for col in numeric_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            clean = series.dropna()
            if len(clean) == 0:
                continue

            # 跳过纯整数列（所有值的小数部分接近0，使用容差避免浮点误差）
            try:
                if np.allclose(clean % 1, 0, atol=1e-12):
                    continue
            except Exception:
                continue

            if config["mode"] == "auto":
                places = self._auto_detect(clean, config)
            else:
                places = config["fixed_places"]

            if places is None or places == 0:
                if config["mode"] == "auto":
                    continue  # 整数列自动跳过

            if config["method"] == "round":
                new_series = series.round(places)
            elif config["method"] == "floor":
                factor = 10 ** places
                new_series = (series * factor).apply(np.floor) / factor
            elif config["method"] == "ceil":
                factor = 10 ** places
                new_series = (series * factor).apply(np.ceil) / factor
            else:
                new_series = series.round(places)

            mask = (series.notna() & new_series.notna()) & (series != new_series)
            changed = mask.sum()
            if changed > 0:
                df[col] = new_series
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    reason=f"统一为 {places} 位小数，影响 {changed} 个值",
                ))

        model.df = df
        self._add_changes(model, changes)
        return model

    def _auto_detect(self, series: pd.Series, config: dict) -> int:
        decimal_counts = []
        for val in series:
            s = f"{val:.10f}".rstrip('0')
            if '.' in s:
                decimal_counts.append(len(s.split('.')[1]))
            else:
                decimal_counts.append(0)

        if not decimal_counts:
            return 2

        arr = np.array(decimal_counts)
        detected = int(np.percentile(arr, config.get("auto_percentile", 90)))
        return max(config.get("decimal_min", 0), min(detected, config.get("decimal_max", 6)))
