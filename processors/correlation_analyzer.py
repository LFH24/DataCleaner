"""
⑲ 相关性分析 — Pearson/Spearman 相关系数，高相关告警，VIF
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import CORRELATION_THRESHOLD, VIF_THRESHOLD


class CorrelationAnalyzer(BaseProcessor):
    name = "correlation_analyzer"
    label = "相关性分析"
    description = "Pearson/Spearman相关系数，高相关告警，VIF共线性检测"
    enabled = False
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "pearson",               # "pearson" | "spearman"
            "correlation_threshold": CORRELATION_THRESHOLD,
            "compute_vif": True,
            "vif_threshold": VIF_THRESHOLD,
        }

    def process(self, model: DataModel) -> DataModel:
        changes: list[ChangeRecord] = []
        config = self.config

        numeric_cols = [
            c for c in self.get_numeric_columns(model)
            if c not in model.id_columns
        ]
        if len(numeric_cols) < 2:
            changes.append(self._make_record(
                step_name=self.label, reason="数值列不足，跳过相关性分析"
            ))
            self._add_changes(model, changes)
            return model

        # 确保是数值类型
        clean_df = model.df[numeric_cols].apply(pd.to_numeric, errors="coerce")

        # 1. 相关矩阵
        corr_matrix = clean_df.corr(method=config["method"])

        # 高相关对
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                val = corr_matrix.iloc[i, j]
                if abs(val) >= config["correlation_threshold"]:
                    high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], val))

        if high_corr_pairs:
            for c1, c2, val in high_corr_pairs:
                changes.append(self._make_record(
                    step_name=self.label,
                    column=f"{c1} ↔ {c2}",
                    original_value=round(val, 4),
                    reason=f"高{'正' if val > 0 else '负'}相关 (r={val:.4f})，建议检查是否需要删除其一",
                ))

        # 2. VIF
        if config["compute_vif"] and len(numeric_cols) > 2:
            try:
                vif_data = self._compute_vif(clean_df)
                high_vif = vif_data[vif_data["VIF"] > config["vif_threshold"]]
                for _, row in high_vif.iterrows():
                    changes.append(self._make_record(
                        step_name=self.label,
                        column=row["Feature"],
                        original_value=round(row["VIF"], 2),
                        reason=f"VIF={row['VIF']:.1f} > {config['vif_threshold']}，存在严重多重共线性",
                    ))
            except Exception as e:
                changes.append(self._make_record(
                    step_name=self.label, reason=f"VIF计算失败: {e}"
                ))

        if not changes:
            changes.append(self._make_record(
                step_name=self.label, reason="未检测到高相关性或严重多重共线性"
            ))

        self._add_changes(model, changes)
        return model

    def _compute_vif(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算方差膨胀因子"""
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        df_clean = df.dropna()
        vif = pd.DataFrame({
            "Feature": df_clean.columns,
            "VIF": [variance_inflation_factor(df_clean.values, i) for i in range(df_clean.shape[1])],
        })
        return vif.sort_values("VIF", ascending=False)
