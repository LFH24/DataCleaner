"""
全局配置 — 中文文案、默认阈值、单位词库、处理器元数据
"""
from __future__ import annotations

# ============================================================
# 应用程序元信息
# ============================================================
APP_NAME = "自动化数据预处理工具"
APP_VERSION = "1.0.0"
APP_AUTHOR = "DataPreprocessor"

# ============================================================
# 默认阈值
# ============================================================
DEFAULT_ENCODING = "auto"               # 编码检测
MISSING_RATIO_DROP_COL = 0.50            # 缺失率 > 此值 → 建议删除列
MISSING_RATIO_DROP_ROW = 0.30            # 缺失率 > 此值 → 建议删除行
SKEW_THRESHOLD = 1.0                     # |偏度| > 此值 → 用中位数而非均值
IQR_MULTIPLIER = 1.5                     # IQR 异常值倍数
ZSCORE_THRESHOLD = 3.0                   # Z-score 异常值阈值
IF_CONTAMINATION = 0.05                  # Isolation Forest 污染率
CORRELATION_THRESHOLD = 0.9              # 高相关性告警阈值
VIF_THRESHOLD = 10.0                     # VIF 多重共线性告警阈值
DECIMAL_MAX = 6                          # 小数位最大值
DECIMAL_MIN = 0                          # 小数位最小值
DECIMAL_PERCENTILE = 90                  # 自动检测小数位百分位
UNIT_MATCH_RATIO = 0.3                   # 单位匹配比例阈值
TYPE_DETECT_NUMERIC_RATIO = 0.9          # 类型检测数值比例
TYPE_DETECT_DATETIME_RATIO = 0.8         # 类型检测日期比例
CATEGORICAL_MAX_RATIO = 0.1              # 分类列最大唯一值比例
CONSTANT_UNIQUE_MAX = 1                  # 常数列最大唯一值数
ID_COL_UNIQUE_RATIO = 0.9                # ID 列唯一值比例阈值
LOW_VARIANCE_THRESHOLD = 0.0             # 低方差过滤阈值
DEFAULT_BINS = 5                         # 默认分箱数
ONEHOT_MAX_CATEGORIES = 10               # One-Hot 编码最大分类数
PREVIEW_ROWS_PER_PAGE = 100              # 预览每页行数

# ============================================================
# 预置值映射规则 (→ NaN)
# ============================================================
DEFAULT_NA_VALUES = [
    "N/A", "n/a", "NA", "na", "null", "NULL", "Null",
    "None", "none", "NONE", " ", "", ".", "-", "--",
    "未知", "无", "缺失", "空缺", "不详",
    "#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NUM!", "#NAME?",
]

# ============================================================
# 日期时间格式模式
# ============================================================
DATE_PATTERNS = [
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$",                    # 2024-01-01
    r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}$",                    # 01-01-2024
    r"^\d{4}年\d{1,2}月\d{1,2}日$",                       # 2024年1月1日
    r"^\d{4}\d{2}\d{2}$",                                  # 20240101
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}$",    # 2024-01-01 12:00
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}:\d{2}$",  # with seconds
    r"^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}$",
]

# ============================================================
# 单位词库（用于正则模式构建）
# ============================================================
UNIT_REGISTRY = {
    "重量": ["kg", "g", "mg", "t", "公斤", "千克", "斤", "两", "吨", "μg", "ng"],
    "长度": ["km", "m", "cm", "mm", "μm", "nm", "千米", "米", "厘米", "毫米", "微米", "纳米", "里", "公里"],
    "面积": ["km²", "m²", "cm²", "mm²", "公顷", "亩", "平方米", "平方千米", "平方公里"],
    "体积": ["L", "mL", "μL", "m³", "cm³", "升", "毫升", "立方米", "立方厘米", "加仑"],
    "时间": ["h", "min", "s", "ms", "小时", "分钟", "秒", "毫秒", "天", "周", "月", "年", "日"],
    "温度": ["°C", "°F", "K", "摄氏度", "华氏度"],
    "货币": ["元", "万元", "亿元", "美元", "欧元", "日元", "英镑", "港币", "澳元", "$", "€", "¥", "£", "￥"],
    "速度": ["km/h", "m/s", "kmh", "mph", "千米/小时", "米/秒", "节"],
    "百分比": ["%", "‰", "％", "‰"],
    "计数": ["个", "只", "条", "件", "台", "辆", "次", "人", "户", "家", "笔", "张", "本", "册", "套", "颗", "粒", "片", "支", "瓶", "盒", "包", "袋", "箱", "份"],
    "电力": ["V", "kV", "A", "mA", "W", "kW", "MW", "kWh", "MWh", "Ω", "伏", "安", "瓦", "千瓦", "度", "伏特", "安培"],
    "压强": ["Pa", "kPa", "MPa", "bar", "atm", "mmHg", "帕", "千帕", "兆帕", "巴"],
    "频率": ["Hz", "kHz", "MHz", "GHz", "赫兹", "千赫", "兆赫"],
    "数据": ["B", "KB", "MB", "GB", "TB", "PB", "bps", "Mbps", "Gbps", "字节"],
    "浓度": ["mol/L", "mmol/L", "μmol/L", "g/L", "mg/L", "μg/L", "mg/mL", "ppm", "ppb"],
    "能量": ["J", "kJ", "MJ", "cal", "kcal", "焦耳", "千焦", "卡", "千卡", "大卡"],
    "角度": ["°", "rad", "度", "弧度"],
}

# ============================================================
# 全角 → 半角转换映射
# ============================================================
def _build_fullwidth_map() -> dict[int, int]:
    """构建全角→半角字符映射表"""
    fw_map = {}
    # 全角数字 ０-９ → 半角 0-9
    for i in range(0xFF10, 0xFF1A):
        fw_map[i] = ord('0') + (i - 0xFF10)
    # 全角大写字母 Ａ-Ｚ → A-Z
    for i in range(0xFF21, 0xFF3B):
        fw_map[i] = ord('A') + (i - 0xFF21)
    # 全角小写字母 ａ-ｚ → a-z
    for i in range(0xFF41, 0xFF5B):
        fw_map[i] = ord('a') + (i - 0xFF41)
    # 全角空格 → 半角空格
    fw_map[0x3000] = ord(' ')
    # 全角符号
    symbol_map = {
        0xFF0C: ',', 0xFF0E: '.', 0xFF1A: ':', 0xFF1B: ';',
        0xFF01: '!', 0xFF1F: '?', 0xFF08: '(', 0xFF09: ')',
        0xFF3B: '[', 0xFF3D: ']', 0xFF5B: '{', 0xFF5D: '}',
        0xFF0B: '+', 0xFF0D: '-', 0xFF1D: '=', 0xFF0A: '*',
        0xFF0F: '/', 0xFF3C: '\\', 0xFF04: '$', 0xFF05: '%',
        0xFF03: '#', 0xFF20: '@', 0xFF06: '&', 0xFF3E: '^',
        0xFF5E: '~', 0xFF3F: '_', 0xFF5C: '|',
    }
    fw_map.update({k: ord(v) for k, v in symbol_map.items()})
    return fw_map

FULLWIDTH_TO_HALFWIDTH = _build_fullwidth_map()

# ============================================================
# 处理器元数据（用于 GUI 配置面板）
# ============================================================
PROCESSOR_META = [
    # (stage_key, stage_label, processor_key, processor_label, description, default_enabled, has_config)
    ("text_format", "🔤 文本与格式清洗", "encoding_normalizer", "编码规范化",
     "去除首尾空白、全角转半角、Unicode标准化、替换智能引号", True, True),
    ("text_format", "🔤 文本与格式清洗", "column_name_cleaner", "列名规范化",
     "去除列名空白、替换特殊字符为下划线、统一下划线格式", True, True),

    ("type_structure", "🔍 类型与结构识别", "type_detector", "类型检测与转换",
     "自动识别每列为数值/分类/日期/布尔/文本，并转换数据类型", True, True),
    ("type_structure", "🔍 类型与结构识别", "id_column_detector", "ID列识别",
     "检测高基数列（每行唯一值、自增序列等），标记为ID列供后续跳过", True, True),

    ("value_cleaning", "🧹 值级别清洗", "text_standardizer", "文本规范化",
     "统一大小写、移除特殊字符、规范化空白、去除重音符号", True, True),
    ("value_cleaning", "🧹 值级别清洗", "datetime_standardizer", "日期时间标准化",
     "自动识别多种日期格式，统一为ISO标准格式", True, True),
    ("value_cleaning", "🧹 值级别清洗", "value_replacer", "值映射替换",
     "自定义查找替换（如 N/A→NaN），支持精确匹配和正则", False, True),
    ("value_cleaning", "🧹 值级别清洗", "duplicate_handler", "重复行处理",
     "检测完全/部分重复行，可选标记、保留首次、保留末次、全部删除", True, True),
    ("value_cleaning", "🧹 值级别清洗", "constant_remover", "常数列删除",
     "删除唯一值极少或方差为零的列", True, True),

    ("numeric_cleaning", "🔢 数值清洗", "unit_detector", "单位剥离",
     "从数值中提取单位（如100kg），值转数值，列名追加单位后缀", True, True),
    ("numeric_cleaning", "🔢 数值清洗", "percentage_unifier", "百分号/千分号统一",
     "统一%和‰表示（50%转为0.5或保留50.0）", True, True),
    ("numeric_cleaning", "🔢 数值清洗", "decimal_unifier", "小数位数统一",
     "按列自动检测合适小数位，或手动指定", True, True),

    ("anomaly_missing", "⚠️ 异常与缺失", "outlier_detector", "异常值检测",
     "IQR/Z-score/IsolationForest三选一，可选标记/截断/删除", True, True),
    ("anomaly_missing", "⚠️ 异常与缺失", "missing_handler", "缺失值处理",
     "智能选择均值/中位数/众数/插值/删除，可逐列覆写", True, True),

    ("feature_engineering", "🔄 特征工程", "feature_scaler", "特征缩放",
     "Standard/MinMax/Robust缩放，跳过ID列", False, True),
    ("feature_engineering", "🔄 特征工程", "skewness_corrector", "偏度校正",
     "对偏态数值列做Log/Box-Cox/Yeo-Johnson变换", False, True),
    ("feature_engineering", "🔄 特征工程", "binning", "分箱离散化",
     "等宽/等频/K-means分箱", False, True),
    ("feature_engineering", "🔄 特征工程", "categorical_encoder", "分类编码",
     "One-Hot/Label/Ordinal编码，跳过ID列", False, True),

    ("quality_report", "📊 数据质量", "correlation_analyzer", "相关性分析",
     "Pearson/Spearman相关系数，高相关告警，VIF共线性检测", False, True),
    ("quality_report", "📊 数据质量", "profiler", "数据画像",
     "每列统计：类型、非空数、缺失率、均值、中位数、标准差、极值、Top5频次", True, False),
]

# ============================================================
# 免责声明文案
# ============================================================
DISCLAIMER_TITLE = "⚠️  免责声明与数据安全提醒"
DISCLAIMER_TEXT = """
<h3>使用本工具前，请仔细阅读以下条款：</h3>

<p><b>1. 数据备份提醒</b><br>
本工具会<b>直接修改</b>您的数据。在开始处理前，<b>请务必做好原始数据集的备份</b>。
建议将原始文件复制一份到安全位置后再进行操作。</p>

<p><b>2. 自动处理的局限性</b><br>
本工具使用统计方法自动检测和处理数据，可能存在<b>误判</b>
（例如将正常的极端值识别为异常值、对不适合的数据列应用自动填补策略等）。
请务必在处理完成后<b>仔细检查处理报告</b>，确认所有变更符合预期。</p>

<p><b>3. 不可逆操作警告</b><br>
部分处理操作（特征缩放、编码转换、分箱离散化等）会<b>不可逆地改变</b>数据的原始结构和值。
建议仅在确认需要这些操作时开启，或先在数据副本上试验。</p>

<p><b>4. 数据隐私保证</b><br>
本工具为<b>纯离线工具</b>，所有数据处理均在您的本地计算机上完成，
<b>不会将您的数据上传至任何服务器或第三方</b>。</p>

<p><b>5. 免责声明</b><br>
开发者对因使用本工具而导致的任何数据丢失、损坏或错误不承担责任。
使用本工具即表示您已理解并接受上述风险。</p>
"""
DISCLAIMER_CHECKBOX = "我已阅读并理解上述条款，已做好数据备份"
DISCLAIMER_AGREE = "同 意"
DISCLAIMER_EXIT = "退 出"

# ============================================================
# 导出格式
# ============================================================
EXPORT_FORMATS = {
    "csv": "CSV (逗号分隔)",
    "csv_tsv": "TSV (制表符分隔)",
    "xlsx": "Excel (.xlsx)",
    "json": "JSON",
}

# ============================================================
# 全角字符判断辅助
# ============================================================
def is_fullwidth(char: str) -> bool:
    """判断字符是否为全角"""
    cp = ord(char)
    return (0xFF01 <= cp <= 0xFF5E) or (0xFF61 <= cp <= 0xFF9F) or cp == 0x3000
