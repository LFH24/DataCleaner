"""
⑬ 异常值检测 — IQR / Z-score / Isolation Forest
操作：标记（新增列）/ 截断（Winsorize）/ 删除行
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor
from config import IQR_MULTIPLIER, ZSCORE_THRESHOLD, IF_CONTAMINATION


class OutlierDetector(BaseProcessor):
    name = "outlier_detector"
    label = "异常值检测"
    description = "IQR/Z-score/IsolationForest三选一，可选标记/截断/删除"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "method": "iqr",                # "iqr" | "zscore" | "isolation_forest"
            "action": "flag",               # "flag" | "cap" | "remove"
            "iqr_multiplier": IQR_MULTIPLIER,
            "zscore_threshold": ZSCORE_THRESHOLD,
            "if_contamination": IF_CONTAMINATION,
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        method = config["method"]
        action = config["action"]

        numeric_cols = [
            c for c in self.get_numeric_columns(model)
            if pd.api.types.is_numeric_dtype(df[c])
        ]
        if not numeric_cols:
            self._add_changes(model, changes)
            return model

        outlier_mask = pd.DataFrame(False, index=df.index, columns=numeric_cols)

        # 1. 检测异常值
        if method == "iqr":
            outlier_mask = self._iqr_detect(df, numeric_cols, config)
        elif method == "zscore":
            outlier_mask = self._zscore_detect(df, numeric_cols, config)
        elif method == "isolation_forest":
            outlier_mask = self._if_detect(df, numeric_cols, config)

        total_outliers = outlier_mask.sum().sum()
        if total_outliers == 0:
            changes.append(self._make_record(
                step_name=self.label, reason="未检测到异常值"
            ))
            self._add_changes(model, changes)
            return model

        # 2. 处理异常值
        if action == "flag":
            for col in numeric_cols:
                flag_col = f"{col}_outlier"
                df[flag_col] = outlier_mask[col]
                n = outlier_mask[col].sum()
                if n > 0:
                    changes.append(self._make_record(
                        step_name=self.label, column=col,
                        reason=f"标记 {n} 个异常值（新增列 {flag_col}）",
                    ))

        elif action == "cap":
            for col in numeric_cols:
                mask = outlier_mask[col]
                if mask.any():
                    series = df[col]
                    lower = series.quantile(0.25) - config["iqr_multiplier"] * (series.quantile(0.75) - series.quantile(0.25))
                    upper = series.quantile(0.75) + config["iqr_multiplier"] * (series.quantile(0.75) - series.quantile(0.25))

                    for idx in df.index[mask]:
                        orig = df.loc[idx, col]
                        capped = max(lower, min(upper, orig))
                        if orig != capped:
                            changes.append(self._make_record(
                                step_name=self.label, column=col, row_index=idx,
                                original_value=orig, new_value=capped,
                                reason=f"截断异常值至 [{lower:.4f}, {upper:.4f}]",
                            ))
                            df.loc[idx, col] = capped

        elif action == "remove":
            any_outlier = outlier_mask.any(axis=1)
            before = len(df)
            df = df[~any_outlier].reset_index(drop=True)
            removed = before - len(df)
            changes.append(self._make_record(
                step_name=self.label,
                reason=f"删除 {removed} 个含异常值的行",
            ))

        model.df = df
        self._add_changes(model, changes)
        return model

    def _iqr_detect(self, df: pd.DataFrame, cols: list[str], config: dict) -> pd.DataFrame:
        mask = pd.DataFrame(False, index=df.index, columns=cols)
        mult = config["iqr_multiplier"]
        for col in cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - mult * iqr
            upper = q3 + mult * iqr
            mask[col] = (df[col] < lower) | (df[col] > upper)
        return mask

    def _zscore_detect(self, df: pd.DataFrame, cols: list[str], config: dict) -> pd.DataFrame:
        mask = pd.DataFrame(False, index=df.index, columns=cols)
        threshold = config["zscore_threshold"]
        for col in cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue
            z = np.abs(stats.zscore(series, nan_policy="omit"))
            col_mask = pd.Series(False, index=df.index)
            col_mask[series.index] = z > threshold
            mask[col] = col_mask
        return mask

    def _if_detect(self, df: pd.DataFrame, cols: list[str], config: dict) -> pd.DataFrame:
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            # 回退到 IQR
            return self._iqr_detect(df, cols, config)

        mask = pd.DataFrame(False, index=df.index, columns=cols)
        clean = df[cols].dropna()
        if len(clean) < 10:
            return mask

        clf = IsolationForest(
            contamination=config["if_contamination"],
            random_state=42,
            n_estimators=100,
        )
        preds = clf.fit_predict(clean)
        outlier_idx = clean.index[preds == -1]

        for col in cols:
            mask.loc[outlier_idx, col] = True

        return mask
