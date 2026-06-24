"""
⑥ 值映射替换 — 自定义查找替换，预设常见 NA 值映射
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import DEFAULT_NA_VALUES


class ValueReplacer(BaseProcessor):
    name = "value_replacer"
    label = "值映射替换"
    description = "自定义查找替换（如 N/A→NaN），支持精确匹配和正则"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "replace_na": True,                    # 启用预设 NA 值替换
            "na_values": DEFAULT_NA_VALUES.copy(),  # 预设 NA 值列表
            "custom_rules": [],                     # [(find, replace, is_regex, columns)]
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        # 1. 预设 NA 值替换
        if config.get("replace_na") and config.get("na_values"):
            na_values = config["na_values"]
            obj_cols = df.select_dtypes(include=["object"]).columns

            for col in obj_cols:
                for na_val in na_values:
                    if na_val == "":
                        # 空字符串：trim 后为空也算
                        mask = (df[col].fillna("").astype(str).str.strip() == "")
                    else:
                        mask = df[col].fillna("").astype(str).str.strip() == na_val

                    if mask.any():
                        for idx in df.index[mask]:
                            changes.append(self._make_record(
                                step_name=self.label,
                                column=col,
                                row_index=idx,
                                original_value=df.loc[idx, col],
                                new_value="NaN (缺失值)",
                                reason=f"匹配预设NA值: '{na_val}'",
                            ))
                        df.loc[mask, col] = np.nan

        # 2. 自定义替换规则
        custom_rules = config.get("custom_rules", [])
        for rule in custom_rules:
            find, replace, is_regex, target_cols = rule[0], rule[1], rule[2], rule[3]
            apply_cols = target_cols if target_cols else df.columns

            for col in apply_cols:
                if col not in df.columns:
                    continue
                if is_regex:
                    try:
                        pattern = re.compile(find)
                        series = df[col].fillna("").astype(str)
                        mask = series.str.match(pattern, na=False)
                    except re.error:
                        continue
                else:
                    mask = df[col].astype(str).str.strip() == find

                if mask.any():
                    for idx in df.index[mask]:
                        changes.append(self._make_record(
                            step_name=self.label,
                            column=col,
                            row_index=idx,
                            original_value=df.loc[idx, col],
                            new_value=replace,
                            reason=f"自定义替换: '{find}' → '{replace}'",
                        ))
                    df.loc[mask, col] = replace

        model.df = df
        self._add_changes(model, changes)
        return model
