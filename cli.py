#!/usr/bin/env python3
"""
命令行接口 — 自动化数据预处理
"""
from __future__ import annotations

import argparse
import sys
from core.io_handler import load_file, save_file
from core.datamodel import DataModel
from core.pipeline import ProcessingPipeline, PROCESSOR_REGISTRY


def main():
    parser = argparse.ArgumentParser(
        description="自动化数据预处理工具 — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py data.csv -o cleaned.csv
  python cli.py data.xlsx -o cleaned.xlsx --skip outlier_detector missing_handler
  python cli.py data.csv --outlier-method zscore --missing-strategy median
  python cli.py data.csv --decimal-places 3 --report report.txt
        """,
    )

    parser.add_argument("input", help="输入文件路径 (.csv, .xlsx, .json, .tsv)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--encoding", "-e", default="auto", help="输入编码 (默认自动检测)")
    parser.add_argument(
        "--skip", nargs="*", default=[],
        help="跳过的处理步骤名称",
    )
    parser.add_argument(
        "--enable", nargs="*", default=None,
        help="手动启用的步骤（覆盖默认关闭的步骤）",
    )
    parser.add_argument("--outlier-method", choices=["iqr", "zscore", "isolation_forest"], default="iqr")
    parser.add_argument("--outlier-action", choices=["flag", "cap", "remove"], default="flag")
    parser.add_argument("--missing-strategy", choices=["auto", "mean", "median", "mode", "drop_rows"], default="auto")
    parser.add_argument("--decimal-places", type=int, default=None)
    parser.add_argument("--percentage-mode", choices=["ratio", "percent"], default="ratio")
    parser.add_argument("--scaler-method", choices=["standard", "minmax", "robust"], default="standard")
    parser.add_argument("--report", "-r", help="处理报告输出路径")
    parser.add_argument("--report-format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    # 构建启禁步骤
    enabled_steps = {}
    for cls in PROCESSOR_REGISTRY:
        name = cls.name
        enabled_steps[name] = cls.enabled  # 默认值

    for skip_name in args.skip:
        if skip_name in enabled_steps:
            enabled_steps[skip_name] = False

    if args.enable:
        for enable_name in args.enable:
            if enable_name in enabled_steps:
                enabled_steps[enable_name] = True

    # 步骤配置
    step_configs = {}

    if "outlier_detector" in enabled_steps and enabled_steps["outlier_detector"]:
        from processors.outlier_detector import OutlierDetector
        cfg = OutlierDetector.default_config()
        cfg["method"] = args.outlier_method
        cfg["action"] = args.outlier_action
        step_configs["outlier_detector"] = cfg

    if "missing_handler" in enabled_steps and enabled_steps["missing_handler"]:
        from processors.missing_handler import MissingHandler
        cfg = MissingHandler.default_config()
        cfg["strategy"] = args.missing_strategy
        step_configs["missing_handler"] = cfg

    if "decimal_unifier" in enabled_steps and enabled_steps["decimal_unifier"] and args.decimal_places is not None:
        from processors.decimal_unifier import DecimalUnifier
        cfg = DecimalUnifier.default_config()
        cfg["mode"] = "fixed"
        cfg["fixed_places"] = args.decimal_places
        step_configs["decimal_unifier"] = cfg

    if "percentage_unifier" in enabled_steps and enabled_steps["percentage_unifier"]:
        from processors.percentage_unifier import PercentageUnifier
        cfg = PercentageUnifier.default_config()
        cfg["mode"] = args.percentage_mode
        step_configs["percentage_unifier"] = cfg

    if "feature_scaler" in enabled_steps and enabled_steps["feature_scaler"]:
        from processors.feature_scaler import FeatureScaler
        cfg = FeatureScaler.default_config()
        cfg["method"] = args.scaler_method
        step_configs["feature_scaler"] = cfg

    # 加载
    print(f"[LOAD] 加载: {args.input}")
    df, metadata = load_file(args.input, encoding=args.encoding)
    print(f"   维度: {df.shape[0]} 行 x {df.shape[1]} 列")
    model = DataModel(df=df, metadata=metadata)

    # 运行流水线
    def progress(i, label):
        print(f"  [{i+1:02d}] {label}...")

    pipeline = ProcessingPipeline(
        enabled_steps=enabled_steps,
        step_configs=step_configs,
        progress_callback=progress,
    )
    model = pipeline.run(model)

    # 输出
    if args.output:
        save_file(model.df, args.output)
        print(f"[OK] 已保存: {args.output}")

    # 报告
    if args.report:
        if args.report_format == "json":
            import json
            report = pipeline.get_report_json(model)
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        else:
            report = pipeline.get_report(model)
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report)
        print(f"[REPORT] 处理报告已保存: {args.report}")
    else:
        # 默认打印摘要
        print(f"\n[DONE] 处理完成: {len(model.change_log)} 处变更")
        if model.change_log:
            from collections import Counter
            steps = Counter(c.step_name for c in model.change_log)
            for step, count in steps.items():
                print(f"  [{step}]: {count} 处变更")

    return 0


if __name__ == "__main__":
    sys.exit(main())
