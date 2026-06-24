# 自动化数据预处理工具

一个带图形界面的桌面端数据清洗工具，支持 CSV、Excel 等多种格式，**所有处理步骤均可自由勾选**，处理完成后生成详细报告。

## ✨ 功能概览

### 🔤 文本与格式清洗
- **编码规范化** — 去除空白、全角转半角、Unicode 标准化、替换智能引号
- **列名规范化** — 统一列名格式，替换特殊字符，合并多余下划线

### 🔍 类型与结构识别
- **类型检测与转换** — 自动识别每列为数值/分类/日期/布尔/文本，并转换数据类型
- **ID 列识别** — 自动识别主键列（自增序列、UUID 等），后续特征工程自动跳过

### 🧹 值级别清洗
- **文本规范化** — 统一大小写、去除特殊字符、去除重音符号
- **日期时间标准化** — 识别 `2024年1月1日`、`2024/01/01`、`01-01-2024` 等各种格式，统一为 ISO 标准
- **值映射替换** — 自定义查找替换（如 `N/A` → 缺失值），支持精确匹配和正则
- **重复行处理** — 检测重复行，可选标记/保留首次/保留末次/全部删除
- **常数列删除** — 自动删除只有单一值或方差为零的无用列

### 🔢 数值清洗
- **单位剥离** — 从 `"100kg"`、`"500万元"` 中提取单位，值转纯数值，列名追加单位后缀
- **百分号/千分号统一** — `"50%"` → `0.5`，`"5‰"` → `0.005`
- **小数位数统一** — 按列智能检测合适小数位，或手动指定

### ⚠️ 异常与缺失
- **异常值检测** — 支持 IQR / Z-score / Isolation Forest 三种方法，可选标记/截断/删除
- **缺失值处理** — 智能选择均值/中位数/众数/前后填充/插值/删除，可逐列覆写策略

### 🔄 特征工程
- **特征缩放** — Standard / MinMax / Robust 缩放，自动跳过 ID 列
- **偏度校正** — Log / Box-Cox / Yeo-Johnson 变换
- **分箱离散化** — 等宽 / 等频 / K-means 三种分箱方法
- **分类编码** — One-Hot / Label / Ordinal 编码

### 📊 数据质量报告
- **相关性分析** — Pearson/Spearman 相关系数 + VIF 多重共线性检测
- **数据画像** — 每列完整统计（类型、缺失率、均值、中位数、标准差、极值、Top5 频次值）

---

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 点击右侧 [Releases](https://github.com/LFH24/DataCleaner/releases) 下载 `DataCleaner.exe`
2. 双击运行，首次启动会弹出**免责声明弹窗**，阅读后勾选确认即可进入主界面
3. 拖放数据文件到窗口，勾选需要的处理步骤，点击「▶ 开始处理」

### 方式二：Python 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/LFH24/DataCleaner.git
cd DataCleaner

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 GUI
python main.py

# 或使用命令行模式
python cli.py 你的数据.csv -o 处理后.csv --report 报告.txt
```

### 方式三：一键启动脚本

双击仓库根目录的 `一键启动.bat`

---

## 📖 使用说明

### GUI 模式

1. **加载数据** — 拖放 CSV/XLSX/JSON 等文件到窗口，或点击「📂 打开」
2. **配置步骤** — 左侧面板勾选/取消处理步骤，点击 `⚙` 调整参数
3. **运行处理** — 点击「▶ 开始处理」，进度条实时显示
4. **查看结果** — 切换到「📝 处理日志」标签页查看每处变更详情
5. **导出数据** — 点击「💾 导出」，支持 CSV / Excel / JSON / TSV 格式

### CLI 模式

```bash
# 基本用法
python cli.py data.csv -o cleaned.csv

# 跳过某些步骤
python cli.py data.csv --skip outlier_detector missing_handler

# 手动启用特征工程步骤
python cli.py data.csv --enable feature_scaler categorical_encoder

# 指定异常值检测方法
python cli.py data.csv --outlier-method zscore --outlier-action remove

# 指定缺失值策略
python cli.py data.csv --missing-strategy median

# 固定小数位数
python cli.py data.csv --decimal-places 3

# 生成处理报告
python cli.py data.csv --report report.txt --report-format json
```

---

## 🛡️ 免责声明

- 本工具会**直接修改**您的数据，处理前请务必备份原始文件
- 自动处理可能存在误判，请务必检查处理报告
- 特征工程类操作（缩放、编码、分箱等）会**不可逆地改变**数据结构
- 本工具为**纯离线工具**，数据不会上传至任何服务器

---

## 📋 支持的格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| CSV | `.csv` | 逗号分隔值，自动检测编码 |
| TSV | `.tsv` | 制表符分隔值 |
| Excel | `.xlsx` `.xls` | 支持多 sheet（默认第一个） |
| JSON | `.json` | 支持 records 格式 |
| Parquet | `.parquet` | 列式存储格式 |
| Stata | `.dta` | 统计软件格式 |

---

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | PySide6 |
| 数据处理 | pandas / numpy / openpyxl |
| 统计工具 | scipy（IQR / Z-score / 偏度 / Box-Cox） |
| 机器学习 | scikit-learn（Isolation Forest / 缩放 / 编码 / K-means） |
| 编码检测 | chardet |
| 打包 | PyInstaller（单文件 exe） |

---

## 📦 项目结构

```
├── main.py                    # 程序入口
├── cli.py                     # 命令行接口
├── config.py                  # 全局配置 + 中文文案 + 单位词库
│
├── core/                      # 核心逻辑层
│   ├── datamodel.py           # 数据模型 + 变更日志
│   ├── pipeline.py            # 流水线编排器
│   ├── io_handler.py          # 文件读写 + 编码检测
│   └── report.py              # 处理报告生成
│
├── processors/                # 20个处理步骤
│   ├── encoding_normalizer.py # 编码规范化
│   ├── column_name_cleaner.py # 列名规范化
│   ├── type_detector.py       # 类型检测与转换
│   ├── id_column_detector.py  # ID列识别
│   ├── text_standardizer.py   # 文本规范化
│   ├── datetime_standardizer.py # 日期时间标准化
│   ├── value_replacer.py      # 值映射替换
│   ├── duplicate_handler.py   # 重复行处理
│   ├── constant_remover.py    # 常数列删除
│   ├── unit_detector.py       # 单位剥离
│   ├── percentage_unifier.py  # 百分号/千分号统一
│   ├── decimal_unifier.py     # 小数位数统一
│   ├── outlier_detector.py    # 异常值检测
│   ├── missing_handler.py     # 缺失值处理
│   ├── feature_scaler.py      # 特征缩放
│   ├── skewness_corrector.py  # 偏度校正
│   ├── binning.py             # 分箱离散化
│   ├── categorical_encoder.py # 分类编码
│   ├── correlation_analyzer.py # 相关性分析
│   └── profiler.py            # 数据画像
│
└── gui/                       # 图形界面
    ├── app.py                 # 应用启动
    ├── disclaimer_dialog.py   # 免责声明弹窗
    ├── drop_area.py           # 拖放区域
    ├── main_window.py         # 主窗口
    ├── pipeline_config.py     # 步骤配置面板
    ├── workers.py             # 后台线程
    └── styles.py              # 全局样式
```

---

## ⚠️ 注意事项

- Python 版本要求：**3.10+**
- exe 首次启动可能较慢（约 5-10 秒），因为需要解压运行环境
- 处理大文件（>10万行）时建议关闭不必要的处理步骤以提高速度
- 若遇到 `vcruntime140.dll` 缺失错误，请安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

---

## 📄 许可证

本项目仅用于学习和个人用途。
