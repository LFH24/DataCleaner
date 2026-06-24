"""
⑨ ID 列识别 — 检测高基数列，标记为 ID 列供后续特征工程跳过
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import ID_COL_UNIQUE_RATIO


# ID 列常见命名模式
ID_NAME_PATTERNS = [
    "id", "ID", "Id", "iD",
    "编号", "序号", "代码",
    "code", "Code", "CODE",
    "uuid", "UUID", "Uuid",
    "guid", "GUID",
    "key", "KEY", "Key",
    "serial", "SERIAL",
    "no", "NO", "No", "号",
]

# 自增序列检测：相邻差值几乎恒为 1


class IdColumnDetector(BaseProcessor):
    name = "id_column_detector"
    label = "ID列识别"
    description = "检测高基数列（每行唯一值、自增序列等），标记为ID列供后续跳过"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "unique_ratio_threshold": ID_COL_UNIQUE_RATIO,
            "check_name_pattern": True,
            "check_sequential": True,
            "check_uuid": True,
        }

    def process(self, model: DataModel) -> DataModel:
        changes: list[ChangeRecord] = []
        config = self.config
        id_columns: set[str] = set()

        for col in model.df.columns:
            col_name = str(col).lower().strip()
            series = model.df[col].dropna()
            n = len(model.df)
            reasons = []

            # 1. 列名模式匹配
            if config.get("check_name_pattern"):
                for pat in ID_NAME_PATTERNS:
                    if pat.lower() in col_name:
                        reasons.append(f"列名含ID关键词: '{pat}'")
                        break

            # 2. 高唯一值比例
            if len(series) > 0 and series.nunique() / n >= config.get("unique_ratio_threshold", 0.9):
                reasons.append(f"唯一值比例={series.nunique() / n:.1%}")

            # 3. 自增序列检测
            if config.get("check_sequential") and pd.api.types.is_numeric_dtype(series):
                clean = pd.to_numeric(series, errors="coerce").dropna()
                if len(clean) > 2:
                    diffs = clean.sort_values().diff().dropna()
                    if len(diffs) > 0:
                        mode_diff = diffs.mode()
                        if len(mode_diff) > 0 and mode_diff.iloc[0] > 0:
                            const_ratio = (diffs == mode_diff.iloc[0]).mean()
                            if const_ratio > 0.8:
                                reasons.append(f"疑似自增序列 (步长={mode_diff.iloc[0]:.0f})")

            # 4. UUID 检测
            if config.get("check_uuid") and len(series) > 0:
                import re
                sample = series.astype(str).iloc[:min(20, len(series))]
                uuid_pattern = re.compile(
                    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                )
                if sample.apply(lambda x: bool(uuid_pattern.match(str(x)))).mean() > 0.5:
                    reasons.append("疑似UUID")

            if reasons:
                id_columns.add(col)
                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    reason="; ".join(reasons),
                ))

        model.id_columns = id_columns
        self._add_changes(model, changes)
        return model
