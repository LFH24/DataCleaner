"""
处理报告生成器 — 文本格式 & JSON 格式
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from core.datamodel import DataModel, ChangeRecord


def generate_text_report(model: DataModel) -> str:
    """生成纯文本处理报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("  自动化数据预处理 — 处理报告")
    lines.append("=" * 60)
    lines.append(f"  处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  数据维度: {model.rows} 行 × {model.cols} 列")
    lines.append(f"  总缺失值: {model.df.isna().sum().sum()}")
    lines.append("")

    if model.metadata:
        lines.append("--- 文件信息 ---")
        for k, v in model.metadata.items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    # 按步骤汇总变更
    if not model.change_log:
        lines.append("✅ 未检测到需要处理的问题，数据无需变更。")
        return "\n".join(lines)

    # 分组统计
    from collections import Counter
    step_counter = Counter(c.step_name for c in model.change_log)

    lines.append("--- 处理摘要 ---")
    for step, count in step_counter.items():
        lines.append(f"  [{step}] 共 {count} 处变更")
    lines.append(f"  总计: {len(model.change_log)} 处变更")
    lines.append("")

    # 详细变更（按步骤分组）
    lines.append("--- 详细变更 ---")
    current_step = None
    for record in model.change_log:
        if record.step_name != current_step:
            current_step = record.step_name
            lines.append(f"\n  [{current_step}]")
        loc = f"列「{record.column}」" if record.column else ""
        if record.row_index is not None:
            loc += f" 第{record.row_index}行"
        lines.append(f"    {loc}: {record.original_value} → {record.new_value}")
        if record.reason:
            lines.append(f"      原因: {record.reason}")

    # 列摘要
    lines.append("")
    lines.append("--- 处理后的列状态 ---")
    for profile in model.profiles:
        lines.append(
            f"  {profile.name}: 类型={profile.detected_type.value}, "
            f"非空={profile.count - profile.missing_count}/{profile.count}, "
            f"缺失率={profile.missing_ratio:.1%}"
        )

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def generate_json_report(model: DataModel) -> dict:
    """生成 JSON 格式处理报告"""
    return {
        "timestamp": datetime.now().isoformat(),
        "shape": {"rows": model.rows, "cols": model.cols},
        "total_missing": int(model.df.isna().sum().sum()),
        "metadata": model.metadata,
        "summary": {
            "total_changes": len(model.change_log),
            "steps": list(set(c.step_name for c in model.change_log)),
        },
        "changes": [
            {
                "step": c.step_name,
                "column": c.column,
                "row": c.row_index,
                "original": str(c.original_value),
                "new": str(c.new_value),
                "reason": c.reason,
            }
            for c in model.change_log
        ],
        "columns": [
            {
                "name": p.name,
                "type": p.detected_type.value,
                "count": p.count,
                "missing": p.missing_count,
                "missing_ratio": p.missing_ratio,
                "unique": p.unique_count,
                "mean": p.mean,
                "median": p.median,
                "std": p.std,
                "min": str(p.min_val) if p.min_val is not None else None,
                "max": str(p.max_val) if p.max_val is not None else None,
            }
            for p in model.profiles
        ],
    }
