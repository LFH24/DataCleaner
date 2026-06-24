"""
⑱ 分类编码 — One-Hot / Label / Ordinal 编码，跳过 ID 列
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import ONEHOT_MAX_CATEGORIES


class CategoricalEncoder(BaseProcessor):
    name = "categorical_encoder"
    label = "分类编码"
    description = "One-Hot/Label/Ordinal编码，跳过ID列"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "auto",                    # "auto" | "onehot" | "label" | "ordinal"
            "onehot_max_categories": ONEHOT_MAX_CATEGORIES,
            "ordinal_order": {},                 # {col: [ordered_values]}
            "drop_first": True,                  # One-Hot 时丢弃虚拟变量陷阱第一列，避免多重共线性
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        # 目标列：分类列 + 低基数列，排除 ID 列和已是数值的列
        categorical_cols = self.get_categorical_columns(model)
        # 也处理 object 类型的低基数列
        for col in df.select_dtypes(include=["object", "category"]).columns:
            if col in model.id_columns:
                continue
            if col not in categorical_cols:
                if df[col].nunique() <= config["onehot_max_categories"]:
                    categorical_cols.append(col)

        for col in categorical_cols:
            unique_n = df[col].nunique(dropna=True)

            method = config["method"]
            if method == "auto":
                method = "onehot" if unique_n <= config["onehot_max_categories"] else "label"

            try:
                if method == "onehot":
                    if unique_n > config["onehot_max_categories"]:
                        changes.append(self._make_record(
                            step_name=self.label, column=col,
                            reason=f"跳过One-Hot（{unique_n}类 > 上限{config['onehot_max_categories']}）",
                        ))
                        continue

                    dummies = pd.get_dummies(
                        df[col],
                        prefix=col,
                        drop_first=config["drop_first"],
                        dummy_na=False,
                    )
                    # 将 dummy 列插入原位置
                    col_idx = df.columns.get_loc(col)
                    for i, dcol in enumerate(dummies.columns):
                        df.insert(col_idx + i + 1, dcol, dummies[dcol])
                    df = df.drop(columns=[col])
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"One-Hot编码: {unique_n}类 → {len(dummies.columns)}列"
                               f"{' (drop_first=True)' if config['drop_first'] else ''}",
                    ))

                elif method == "label":
                    from sklearn.preprocessing import LabelEncoder
                    le = LabelEncoder()
                    mask = df[col].notna()
                    df.loc[mask, col] = le.fit_transform(df.loc[mask, col].astype(str))
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"Label编码: {unique_n}类 → 0~{unique_n - 1}",
                    ))

                elif method == "ordinal":
                    order = config.get("ordinal_order", {}).get(col)
                    if order:
                        mapping = {v: i for i, v in enumerate(order)}
                        df[col] = df[col].map(mapping)
                    else:
                        df[col] = df[col].astype("category").cat.codes
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"Ordinal编码: {unique_n}类",
                    ))

            except Exception as e:
                changes.append(self._make_record(
                    step_name=self.label, column=col,
                    reason=f"编码失败: {e}",
                ))

        model.df = df
        self._add_changes(model, changes)
        return model
