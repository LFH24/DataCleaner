"""
⑦ 重复行处理 — 检测完全/部分重复行
"""
from __future__ import annotations

import pandas as pd
from core.datamodel import DataModel, ChangeRecord
from processors.base import BaseProcessor


class DuplicateHandler(BaseProcessor):
    name = "duplicate_handler"
    label = "重复行处理"
    description = "检测完全/部分重复行，可选标记、保留首次、保留末次、全部删除"
    has_config = True

    @staticmethod
    def default_config() -> dict:
        return {
            "action": "remove",          # "mark" | "remove" | "keep_first" | "keep_last"
            "subset": None,              # None = 全部列；list[str] = 指定列
            "keep": "first",             # "first" | "last" | False (全部删除)
        }

    def process(self, model: DataModel) -> DataModel:
        df = model.df.copy()
        changes: list[ChangeRecord] = []
        config = self.config
        action = config.get("action", "remove")

        subset = config.get("subset") or None
        if subset:
            subset = [c for c in subset if c in df.columns] or None

        # 检测重复
        duplicated_mask = df.duplicated(subset=subset, keep=False)
        dup_count = duplicated_mask.sum()

        if dup_count == 0:
            changes.append(self._make_record(
                step_name=self.label, reason="未检测到重复行"
            ))
            self._add_changes(model, changes)
            return model

        if action == "mark":
            df["_is_duplicate"] = duplicated_mask
            dup_rows = df.index[duplicated_mask].tolist()
            changes.append(self._make_record(
                step_name=self.label,
                reason=f"标记 {dup_count} 个重复行（新增列 _is_duplicate）",
            ))

        elif action in ("remove", "keep_first", "keep_last"):
            keep_map = {
                "remove": False,
                "keep_first": "first",
                "keep_last": "last",
            }
            keep = keep_map.get(action, "first")
            before = len(df)
            df = df.drop_duplicates(subset=subset, keep=keep)
            df = df.reset_index(drop=True)
            removed = before - len(df)
            changes.append(self._make_record(
                step_name=self.label,
                reason=f"删除 {removed} 个重复行（保留方式: {action}）",
            ))

        model.df = df
        self._add_changes(model, changes)
        return model
