"""
④ 文本规范化 — 统一大小写、移除特殊字符、规范化空白
"""
from __future__ import annotations

import re
import unicodedata
import pandas as pd
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor


class TextStandardizer(BaseProcessor):
    name = "text_standardizer"
    label = "文本规范化"
    description = "统一大小写、移除特殊字符、规范化空白、去除重音符号"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "case": "none",                  # "none" | "lower" | "upper" | "title"
            "remove_accents": True,           # 去除重音符号
            "remove_special_chars": False,    # 移除特殊字符
            "collapse_whitespace": True,      # 合并连续空白
            "remove_urls": False,             # 移除URL
            "remove_emails": False,           # 移除Email
            "remove_numbers": False,          # 移除数字
            "remove_punctuation": False,      # 移除标点
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        text_cols = self.get_text_columns(model)

        for col in text_cols:
            series = df[col].copy()
            original = series.copy()

            def _clean(val):
                if not isinstance(val, str):
                    return val
                s = val

                if config.get("remove_accents"):
                    s = unicodedata.normalize('NFKD', s)
                    s = ''.join(c for c in s if not unicodedata.combining(c))

                if config.get("case") == "lower":
                    s = s.lower()
                elif config.get("case") == "upper":
                    s = s.upper()
                elif config.get("case") == "title":
                    s = s.title()

                if config.get("remove_urls"):
                    s = re.sub(r'https?://\S+|www\.\S+', '', s)

                if config.get("remove_emails"):
                    s = re.sub(r'\S+@\S+\.\S+', '', s)

                if config.get("remove_numbers"):
                    s = re.sub(r'\d+', '', s)

                if config.get("remove_punctuation"):
                    s = re.sub(r'[^\w\s]', '', s)

                if config.get("remove_special_chars"):
                    s = re.sub(r'[^\w\s一-鿿]', '', s)

                if config.get("collapse_whitespace"):
                    s = re.sub(r'\s+', ' ', s).strip()

                return s

            series = series.apply(_clean)
            mask = original != series

            for idx in df.index[mask]:
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    row_index=idx,
                    original_value=original.loc[idx],
                    new_value=series.loc[idx],
                    reason="文本规范化",
                ))

            if mask.any():
                df[col] = series

        model.df = df
        self._add_changes(model, changes)
        return model
