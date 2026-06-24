"""
⑪ 百分号/千分号统一 — "50%" → 0.5, "5‰" → 0.005
"""
from __future__ import annotations

import re
import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor


PERCENT_PATTERN = re.compile(r'^\s*([+-]?\d*\.?\d+)\s*[%％]\s*$')
PERMILLE_PATTERN = re.compile(r'^\s*([+-]?\d*\.?\d+)\s*[‰‱]\s*$')


class PercentageUnifier(BaseProcessor):
    name = "percentage_unifier"
    label = "百分号/千分号统一"
    description = "统一%和‰表示（50%转为0.5或保留50.0）"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "mode": "ratio",           # "ratio" → 50%变0.5; "percent" → 保留50.0去掉%
            "handle_percent": True,
            "handle_permille": True,
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].copy()
            new_series = series.copy()
            col_changes = 0

            for idx in series.index:
                val = series.loc[idx]
                if not isinstance(val, str):
                    continue
                s = val.strip()

                # 百分号
                if config["handle_percent"]:
                    pm = PERCENT_PATTERN.match(s)
                    if pm:
                        num = float(pm.group(1))
                        new_val = num / 100.0 if config["mode"] == "ratio" else num
                        changes.append(self._make_record(
                            step_name=self.label, column=col, row_index=idx,
                            original_value=val, new_value=new_val,
                            reason=f"百分号统一: {val} → {new_val}",
                        ))
                        new_series.loc[idx] = new_val
                        col_changes += 1
                        continue

                # 千分号
                if config["handle_permille"]:
                    pmm = PERMILLE_PATTERN.match(s)
                    if pmm:
                        num = float(pmm.group(1))
                        new_val = num / 1000.0 if config["mode"] == "ratio" else num / 10.0
                        changes.append(self._make_record(
                            step_name=self.label, column=col, row_index=idx,
                            original_value=val, new_value=new_val,
                            reason=f"千分号统一: {val} → {new_val}",
                        ))
                        new_series.loc[idx] = new_val
                        col_changes += 1

            if col_changes > 0:
                # 转换为数值类型
                df[col] = pd.to_numeric(new_series, errors="coerce")

        model.df = df
        self._add_changes(model, changes)
        return model
