"""
① 编码规范化 — 去除空白、全角转半角、Unicode 标准化、替换智能引号
"""
from __future__ import annotations

import unicodedata
import re
import pandas as pd
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import FULLWIDTH_TO_HALFWIDTH


class EncodingNormalizer(BaseProcessor):
    name = "encoding_normalizer"
    label = "编码规范化"
    description = "去除首尾空白、全角转半角、Unicode标准化、替换智能引号"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "trim_whitespace": True,
            "normalize_fullwidth": True,
            "unicode_normalize": "NFKC",
            "replace_smart_quotes": True,
            "collapse_whitespace": True,
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        # 只处理对象列
        obj_cols = df.select_dtypes(include=["object"]).columns

        for col in obj_cols:
            series = df[col].copy()
            original = series.copy()

            # 1. 去除首尾空白
            if config.get("trim_whitespace"):
                series = series.apply(lambda x: x.strip() if isinstance(x, str) else x)

            # 2. 全角 → 半角
            if config.get("normalize_fullwidth"):
                series = series.apply(
                    lambda x: x.translate(FULLWIDTH_TO_HALFWIDTH) if isinstance(x, str) else x
                )

            # 3. Unicode 标准化
            if config.get("unicode_normalize"):
                nf = config["unicode_normalize"]
                series = series.apply(
                    lambda x: unicodedata.normalize(nf, x) if isinstance(x, str) else x
                )

            # 4. 替换智能引号
            if config.get("replace_smart_quotes"):
                smart_quotes = {
                    '‘': "'", '’': "'",
                    '“': '"', '”': '"',
                    '–': '-', '—': '--',
                    '…': '...', ' ': ' ',
                }
                trans = str.maketrans(smart_quotes)
                series = series.apply(
                    lambda x: x.translate(trans) if isinstance(x, str) else x
                )

            # 5. 合并多个空白为一个
            if config.get("collapse_whitespace"):
                series = series.apply(
                    lambda x: re.sub(r'\s+', ' ', x) if isinstance(x, str) else x
                )

            # 记录变更
            mask = original != series
            for idx in df.index[mask]:
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    row_index=idx,
                    original_value=original.loc[idx],
                    new_value=series.loc[idx],
                    reason="编码/空白规范化",
                ))

            df[col] = series

        model.df = df
        self._add_changes(model, changes)
        return model
