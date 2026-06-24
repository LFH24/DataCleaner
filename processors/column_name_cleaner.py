"""
② 列名规范化 — 去除列名空白、替换特殊字符、统一格式
"""
from __future__ import annotations

import re
import pandas as pd
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor


class ColumnNameCleaner(BaseProcessor):
    name = "column_name_cleaner"
    label = "列名规范化"
    description = "去除列名空白、替换特殊字符为下划线、统一下划线格式"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "strip": True,
            "case": "none",              # "none" | "lower" | "upper" | "camel"
            "replace_special": True,     # 替换特殊字符为 _
            "collapse_underscores": True, # 合并连续下划线
            "prefix_digit_columns": True, # 数字开头的列名加前缀 col_
        }

    # 需要替换为下划线的字符模式
    SPECIAL_CHARS_PATTERN = re.compile(r'[\s\-\.\(\)\[\]\{\}（）、，。；：！？《》【】／＼＂＇｜＋＝＊＆＾％＄＃＠！～、]')

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        rename_map = {}
        for col in df.columns:
            new_name = str(col)

            if config.get("strip"):
                new_name = new_name.strip()

            if config.get("replace_special"):
                new_name = self.SPECIAL_CHARS_PATTERN.sub('_', new_name)

            if config.get("collapse_underscores"):
                new_name = re.sub(r'_+', '_', new_name)
                new_name = new_name.strip('_')

            if config.get("case") == "lower":
                new_name = new_name.lower()
            elif config.get("case") == "upper":
                new_name = new_name.upper()

            if config.get("prefix_digit_columns") and new_name and new_name[0].isdigit():
                new_name = f"col_{new_name}"

            # 空列名处理
            if not new_name:
                new_name = f"col_{list(df.columns).index(col)}"

            if new_name != col:
                # 处理重名
                if new_name in rename_map.values():
                    base = new_name
                    counter = 1
                    while f"{base}_{counter}" in rename_map.values():
                        counter += 1
                    new_name = f"{base}_{counter}"

                rename_map[col] = new_name
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    original_value=col,
                    new_value=new_name,
                    reason="列名规范化",
                ))

        if rename_map:
            df = df.rename(columns=rename_map)
            # 更新 column_types 中的键名
            if model.column_types:
                model.column_types = {
                    rename_map.get(k, k): v for k, v in model.column_types.items()
                }
            # 更新 id_columns
            if model.id_columns:
                model.id_columns = {rename_map.get(c, c) for c in model.id_columns}

        model.df = df
        self._add_changes(model, changes)
        return model
