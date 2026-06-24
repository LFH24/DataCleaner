"""
⑤ 日期时间标准化 — 识别多种日期格式，统一为 ISO 标准
"""
from __future__ import annotations

import re
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.parser import parse as dateutil_parse
from core.datamodel import DataModel, ColumnType, ChangeRecord
from processors.base import BaseProcessor

# 手写中文日期匹配（dateutil 不支持中文）
CN_DATE_PATTERNS = [
    (re.compile(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'), "{:04d}-{:02d}-{:02d}"),
    (re.compile(r'(\d{4})\s*年\s*(\d{1,2})\s*月'), "{:04d}-{:02d}"),
]

# 常见数字日期格式
NUM_DATE_PATTERNS = [
    (re.compile(r'^(\d{4})(\d{2})(\d{2})$'), "{}-{}-{}"),     # 20240101
    (re.compile(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$'), "{}-{}-{} {}:{}:{}"),  # 20240101120000
]

# 非日期列的典型关键词
DATE_KEYWORDS = [
    "日期", "时间", "date", "time", "datetime", "timestamp",
    "创建", "修改", "更新", "注册", "生日", "出生", "入职", "离职",
    "开始", "结束", "截止", "有效期", "created", "updated", "modified",
    "birth", "start", "end", "deadline",
]


class DatetimeStandardizer(BaseProcessor):
    name = "datetime_standardizer"
    label = "日期时间标准化"
    description = "自动识别多种日期格式，统一为ISO标准格式"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "output_format": "date",             # "date" | "datetime" | "auto"
            "date_format": "%Y-%m-%d",
            "datetime_format": "%Y-%m-%d %H:%M:%S",
            "detect_by_name": True,              # 通过列名自动检测
            "detect_by_content": True,           # 通过内容自动检测
            "use_dateutil": True,                # 使用 dateutil 解析
            "current_year": datetime.now().year,  # 无年份日期（如 1月1日）补全年份
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config

        # 找到需要处理的列
        target_cols = []

        for col in df.columns:
            col_type = model.column_types.get(col)

            # 通过列名判断
            if config["detect_by_name"]:
                col_lower = col.lower()
                if any(kw in col_lower for kw in DATE_KEYWORDS):
                    target_cols.append(col)
                    continue

            # 通过已检测的类型判断
            if col_type == ColumnType.DATETIME:
                if col not in target_cols:
                    target_cols.append(col)
                continue

            # 通过内容判断
            if config["detect_by_content"] and col not in target_cols:
                if self._looks_like_date(df[col]):
                    target_cols.append(col)

        for col in target_cols:
            series = df[col].copy()
            original = series.astype(str)
            converted = self._parse_dates(series, config)

            if converted is not None:
                fmt = config["date_format"] if config["output_format"] == "date" else config["datetime_format"]
                formatted = converted.apply(
                    lambda x: x.strftime(fmt) if pd.notna(x) else x
                )

                df[col] = formatted

                for idx in df.index:
                    orig_val = original.loc[idx]
                    new_val = formatted.loc[idx]
                    if str(orig_val) != str(new_val):
                        changes.append(self._make_record(
                            step_name=self.label,
                            column=col,
                            row_index=idx,
                            original_value=orig_val,
                            new_value=new_val,
                            reason="日期时间标准化",
                        ))

        model.df = df
        self._add_changes(model, changes)
        return model

    def _looks_like_date(self, series: pd.Series) -> bool:
        """通过抽样检测是否像日期列"""
        sample = series.dropna().head(100).astype(str)
        if len(sample) == 0:
            return False

        # 手写中文日期
        cn_count = 0
        for pat, _ in CN_DATE_PATTERNS:
            cn_count += sample.apply(lambda x: bool(pat.search(str(x)))).sum()
        # 也检查无年份中文日期（如 "1月1日"）
        no_year_pat = re.compile(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日')
        cn_count += sample.apply(lambda x: bool(no_year_pat.search(str(x)))).sum()
        if cn_count / len(sample) > 0.5:
            return True

        # dateutil 尝试
        parsed_count = 0
        for val in sample:
            try:
                dateutil_parse(str(val), fuzzy=False)
                parsed_count += 1
            except Exception:
                pass
        return parsed_count / len(sample) > 0.3

    def _parse_dates(self, series: pd.Series, config: dict):
        """尝试解析日期列，返回 datetime Series 或 None"""
        current_year = config.get("current_year", datetime.now().year)

        # 无年份中文日期模式（运行时构建，使用当前配置的年份）
        no_year_date_pat = re.compile(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日')

        def _parse(val):
            if pd.isna(val):
                return pd.NaT
            s = str(val).strip()
            if not s:
                return pd.NaT

            # 1. 中文日期（含年份）
            for pat, out_fmt in CN_DATE_PATTERNS:
                m = pat.search(s)
                if m:
                    groups = m.groups()
                    try:
                        dt_str = out_fmt.format(*[int(g) for g in groups])
                        return pd.to_datetime(dt_str)
                    except Exception:
                        pass

            # 2. 中文日期（无年份，如 "1月1日"）— 使用配置的 current_year
            m = no_year_date_pat.search(s)
            if m:
                try:
                    month, day = int(m.group(1)), int(m.group(2))
                    dt_str = f"{current_year:04d}-{month:02d}-{day:02d}"
                    return pd.to_datetime(dt_str)
                except Exception:
                    pass

            # 3. 数字日期 (20240101)
            for pat, out_fmt in NUM_DATE_PATTERNS:
                m = pat.match(s)
                if m:
                    groups = m.groups()
                    try:
                        dt_str = out_fmt.format(*groups)
                        return pd.to_datetime(dt_str)
                    except Exception:
                        pass

            # 4. dateutil 宽松解析
            if config.get("use_dateutil", True):
                try:
                    return dateutil_parse(s, fuzzy=False, default=datetime(current_year, 1, 1))
                except Exception:
                    pass

            return pd.NaT

        result = series.apply(_parse)
        if result.notna().mean() > 0:
            return result
        return None
