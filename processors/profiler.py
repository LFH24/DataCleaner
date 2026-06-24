"""
⑳ 数据画像 — 最终统计输出
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ColumnType, ColumnProfile, ChangeRecord
from processors.base import BaseProcessor


class Profiler(BaseProcessor):
    name = "profiler"
    label = "数据画像"
    description = "每列统计：类型、非空数、缺失率、均值、中位数、标准差、极值、Top5频次"
    has_config = False

    def process(self, model: DataModel) -> DataModel:
        # 完全重建 profiles（反映所有处理后的最终状态）
        profiles: list[ColumnProfile] = []

        for col in model.df.columns:
            series = model.df[col]
            col_type = model.column_types.get(col, ColumnType.TEXT)

            profile = ColumnProfile(
                name=col,
                detected_type=col_type,
                dtype=str(series.dtype),
                count=len(series),
                missing_count=int(series.isna().sum()),
                unique_count=int(series.nunique(dropna=True)),
            )

            # 数值统计
            if pd.api.types.is_numeric_dtype(series):
                clean = pd.to_numeric(series, errors="coerce").dropna()
                if len(clean) > 0:
                    profile.mean = float(clean.mean())
                    profile.median = float(clean.median())
                    profile.std = float(clean.std())
                    profile.min_val = float(clean.min())
                    profile.max_val = float(clean.max())
                    from scipy.stats import skew
                    try:
                        if len(clean) > 2:
                            profile.skewness = float(skew(clean))
                    except Exception:
                        pass

            # 非数值的极值
            elif pd.api.types.is_datetime64_any_dtype(series):
                clean = series.dropna()
                if len(clean) > 0:
                    profile.min_val = str(clean.min())
                    profile.max_val = str(clean.max())
            else:
                clean = series.dropna()
                if len(clean) > 0:
                    try:
                        profile.min_val = str(clean.min())
                        profile.max_val = str(clean.max())
                    except Exception:
                        pass

            # Top 5
            try:
                top5 = series.value_counts(dropna=True).head(5)
                profile.top_values = [(str(k), int(v)) for k, v in top5.items()]
            except Exception:
                pass

            profiles.append(profile)

        model.profiles = profiles

        # 汇总
        total_missing = model.df.isna().sum().sum()
        model.change_log.append(ChangeRecord(
            step_name=self.label,
            reason=f"数据画像完成: {model.rows}行×{model.cols}列, 总缺失值={total_missing}",
        ))

        return model
