"""
文件读写 + 编码自动检测
"""
from __future__ import annotations

import os
import json
from typing import Optional
import pandas as pd

from config import DEFAULT_ENCODING


def detect_encoding(file_path: str, sample_size: int = 100_000) -> str:
    """自动检测文件编码"""
    try:
        import chardet
        with open(file_path, "rb") as f:
            raw = f.read(sample_size)
        result = chardet.detect(raw)
        encoding = result.get("encoding", "utf-8")
        confidence = result.get("confidence", 0)
        if confidence < 0.7:
            # 低置信度时尝试常见编码
            for enc in ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]:
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        f.read(sample_size)
                    return enc
                except (UnicodeDecodeError, UnicodeError):
                    continue
        return encoding or "utf-8"
    except ImportError:
        # chardet 不可用时尝试常见编码
        for enc in ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(sample_size)
                return enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        return "utf-8"


def get_file_info(file_path: str) -> dict:
    """获取文件基本信息"""
    return {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_size": os.path.getsize(file_path),
        "extension": os.path.splitext(file_path)[1].lower(),
    }


def load_file(
    file_path: str,
    encoding: str = DEFAULT_ENCODING,
    sheet_name: Optional[str] = None,  # 0 = first sheet for xlsx
) -> tuple[pd.DataFrame, dict]:
    """
    加载数据文件，返回 (DataFrame, metadata)。
    支持 .csv, .xlsx, .xls, .json, .tsv
    """
    ext = os.path.splitext(file_path)[1].lower()
    metadata = get_file_info(file_path)

    if ext == ".csv":
        if encoding == "auto":
            encoding = detect_encoding(file_path)
        df = pd.read_csv(file_path, encoding=encoding, encoding_errors="replace")
        metadata["encoding"] = encoding

    elif ext == ".tsv":
        if encoding == "auto":
            encoding = detect_encoding(file_path)
        df = pd.read_csv(file_path, sep="\t", encoding=encoding, encoding_errors="replace")
        metadata["encoding"] = encoding

    elif ext in (".xlsx", ".xls"):
        sheet = sheet_name if sheet_name is not None else 0
        df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl" if ext == ".xlsx" else "xlrd")
        metadata["sheet"] = str(sheet)

    elif ext == ".json":
        df = pd.read_json(file_path)

    elif ext == ".parquet":
        df = pd.read_parquet(file_path)

    elif ext in (".dta", ".dat"):
        df = pd.read_stata(file_path)

    else:
        # 尝试 CSV
        if encoding == "auto":
            encoding = detect_encoding(file_path)
        try:
            df = pd.read_csv(file_path, encoding=encoding, encoding_errors="replace")
        except Exception:
            raise ValueError(f"不支持的文件格式: {ext}")

    metadata["encoding"] = encoding if encoding != "auto" else detect_encoding(file_path)
    metadata["rows"] = df.shape[0]
    metadata["cols"] = df.shape[1]
    metadata["columns"] = list(df.columns)

    return df, metadata


def save_file(
    df: pd.DataFrame,
    file_path: str,
    encoding: str = "utf-8",
) -> dict:
    """保存 DataFrame 到文件，返回元数据"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df.to_csv(file_path, index=False, encoding=encoding)
    elif ext == ".tsv":
        df.to_csv(file_path, sep="\t", index=False, encoding=encoding)
    elif ext == ".xlsx":
        df.to_excel(file_path, index=False, engine="openpyxl")
    elif ext == ".json":
        df.to_json(file_path, orient="records", force_ascii=False, indent=2)
    else:
        df.to_csv(file_path, index=False, encoding=encoding)

    return {"file_path": file_path, "rows": df.shape[0], "cols": df.shape[1]}
