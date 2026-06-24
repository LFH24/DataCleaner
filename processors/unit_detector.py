"""
⑩ 单位检测剥离 — 从 "100kg", "500万元" 等值中提取单位，值转数值，列名追加单位后缀
"""
from __future__ import annotations

import re
import pandas as pd
import numpy as np
from collections import Counter
from core.datamodel import DataModel, ColumnType, ChangeRecord
from processors.base import BaseProcessor
from config import UNIT_REGISTRY, UNIT_MATCH_RATIO


class UnitDetector(BaseProcessor):
    name = "unit_detector"
    label = "单位剥离"
    description = "从数值中提取单位（如100kg），值转数值，列名追加单位后缀"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "match_ratio": UNIT_MATCH_RATIO,
            "strip_commas": True,            # 去除千分位逗号
            "handle_ranges": True,           # 处理范围值 "100-200kg" → 均值 150
            "unit_categories": None,         # None = 使用全部词库; list[str] = 指定类别
        }

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._unit_pattern: re.Pattern | None = None
        self._build_pattern()

    def _build_pattern(self):
        """构建正则模式"""
        categories = self.config.get("unit_categories")
        units = []
        if categories:
            for cat in categories:
                if cat in UNIT_REGISTRY:
                    units.extend(UNIT_REGISTRY[cat])
        else:
            for cat_units in UNIT_REGISTRY.values():
                units.extend(cat_units)

        # 按长度降序排序（优先匹配更长的单位，如 "万元" 优先于 "元"）
        units.sort(key=len, reverse=True)
        # 转义正则特殊字符
        escaped_units = [re.escape(u) for u in units]
        self._unit_pattern = re.compile(
            r'^\s*([+-]?\d[\d,]*\.?\d*)\s*(' + '|'.join(escaped_units) + r')\s*$'
        )
        self._range_pattern = re.compile(
            r'^\s*([+-]?\d[\d,]*\.?\d*)\s*[-~～]\s*([+-]?\d[\d,]*\.?\d*)\s*(' + '|'.join(escaped_units) + r')\s*$'
        )

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        rename_map = {}

        for col in df.columns:
            # 跳过已经是纯数值的列
            if pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].copy()
            non_null = series.dropna()
            if len(non_null) == 0:
                continue

            str_series = non_null.astype(str).str.strip()

            # 先用 pd.to_numeric 判断当前是否有大量无法转换的值
            num_convertible = pd.to_numeric(str_series, errors="coerce").notna().mean()

            if num_convertible > 0.9:
                # 已经大部分是数值，无需剥离单位
                continue

            # 尝试匹配单位模式
            units_found: list[str] = []
            matched_count = 0

            for val in str_series:
                m = self._unit_pattern.match(val) if self._unit_pattern else None
                if m:
                    units_found.append(m.group(2))
                    matched_count += 1

            if len(str_series) == 0:
                continue

            match_ratio = matched_count / len(str_series)

            if match_ratio >= config["match_ratio"]:
                # 找最常见的单位
                unit_counter = Counter(units_found)
                modal_unit = unit_counter.most_common(1)[0][0]

                # 剥离单位
                def _strip_unit(val):
                    if pd.isna(val):
                        return np.nan
                    s = str(val).strip()
                    m = self._unit_pattern.match(s) if self._unit_pattern else None
                    if m:
                        num_str = m.group(1).replace(",", "")
                        return float(num_str)
                    # 尝试范围值
                    if config.get("handle_ranges"):
                        rm = self._range_pattern.match(s) if self._range_pattern else None
                        if rm:
                            n1 = float(rm.group(1).replace(",", ""))
                            n2 = float(rm.group(2).replace(",", ""))
                            return (n1 + n2) / 2.0
                    return np.nan

                new_series = df[col].apply(_strip_unit)
                df[col] = new_series

                # 列重命名
                new_name = f"{col}({modal_unit})"
                if not col.endswith(f"({modal_unit})"):
                    rename_map[col] = new_name

                changes.append(self._make_record(
                    step_name=self.label,
                    column=col,
                    reason=f"剥离单位 '{modal_unit}'（匹配率 {match_ratio:.1%}），列重命名为 {new_name}",
                ))

        if rename_map:
            df = df.rename(columns=rename_map)
            if model.column_types:
                model.column_types = {
                    rename_map.get(k, k): v for k, v in model.column_types.items()
                }
            if model.id_columns:
                model.id_columns = {rename_map.get(c, c) for c in model.id_columns}

        model.df = df
        self._add_changes(model, changes)
        return model
