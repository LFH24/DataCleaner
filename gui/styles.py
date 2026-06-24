"""
全局样式表 (QSS)
"""
from __future__ import annotations

def get_font_family() -> str:
    """获取系统可用的中文字体"""
    from PySide6.QtGui import QFontDatabase
    candidates = [
        "Microsoft YaHei", "微软雅黑",
        "PingFang SC", "PingFang HK",
        "Noto Sans CJK SC", "Source Han Sans SC",
        "SimHei", "黑体",
        "SimSun", "宋体",
    ]
    available = set(QFontDatabase.families())
    for font in candidates:
        if font in available:
            return font
    return "sans-serif"


def get_stylesheet() -> str:
    font = get_font_family()
    return f"""
/* 全局 */
QWidget {{
    font-family: "{font}", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}}

/* 主窗口 */
QMainWindow {{
    background-color: #f5f5f5;
}}

/* 菜单栏 */
QMenuBar {{
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    padding: 2px;
}}

QMenuBar::item:selected {{
    background-color: #e3f2fd;
    border-radius: 4px;
}}

QMenu {{
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item:selected {{
    background-color: #e3f2fd;
    border-radius: 3px;
}}

/* 工具栏 */
QToolBar {{
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    padding: 4px;
    spacing: 4px;
}}

QToolButton {{
    padding: 6px 14px;
    border: 1px solid transparent;
    border-radius: 4px;
    background-color: transparent;
}}

QToolButton:hover {{
    background-color: #e3f2fd;
}}

QToolButton:pressed {{
    background-color: #bbdefb;
}}

/* 按钮 */
QPushButton {{
    padding: 8px 20px;
    border: 1px solid #ccc;
    border-radius: 6px;
    background-color: #ffffff;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: #e8e8e8;
    border-color: #aaa;
}}

QPushButton:pressed {{
    background-color: #ddd;
}}

QPushButton#runButton {{
    background-color: #1976d2;
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 30px;
}}

QPushButton#runButton:hover {{
    background-color: #1565c0;
}}

QPushButton#runButton:pressed {{
    background-color: #0d47a1;
}}

QPushButton#runButton:disabled {{
    background-color: #90caf9;
}}

/* 复选框 */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #999;
    border-radius: 3px;
    background-color: #ffffff;
}}

QCheckBox::indicator:checked {{
    background-color: #1976d2;
    border-color: #1976d2;
}}

QCheckBox::indicator:hover {{
    border-color: #1976d2;
}}

/* 分组框 */
QGroupBox {{
    font-weight: bold;
    margin-top: 12px;
    padding-top: 16px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background-color: #ffffff;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #333;
}}

/* 表格视图 */
QTableView {{
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    gridline-color: #eee;
    selection-background-color: #e3f2fd;
    selection-color: #333;
}}

QTableView::item {{
    padding: 4px 8px;
}}

QHeaderView::section {{
    background-color: #f0f0f0;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #ddd;
    font-weight: bold;
    color: #555;
}}

/* 滚动区 */
QScrollArea {{
    border: none;
    background: transparent;
}}

/* 分割器 */
QSplitter::handle {{
    background-color: #e0e0e0;
    width: 2px;
    margin: 0 2px;
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #ffffff;
}}

QTabBar::tab {{
    padding: 8px 18px;
    margin-right: 2px;
    border: 1px solid transparent;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    background-color: #f0f0f0;
}}

QTabBar::tab:selected {{
    background-color: #ffffff;
    border-color: #ddd;
    border-bottom: 2px solid #1976d2;
}}

QTabBar::tab:hover {{
    background-color: #e8e8e8;
}}

/* 状态栏 */
QStatusBar {{
    background-color: #fafafa;
    border-top: 1px solid #e0e0e0;
    color: #666;
}}

/* 文本标签 */
QLabel {{
    color: #333;
}}

QLabel#title {{
    font-size: 16px;
    font-weight: bold;
    color: #1976d2;
}}

/* 进度条 */
QProgressBar {{
    border: 1px solid #ddd;
    border-radius: 4px;
    text-align: center;
    height: 20px;
    background-color: #f0f0f0;
}}

QProgressBar::chunk {{
    background-color: #1976d2;
    border-radius: 3px;
}}

/* 对话框 */
QDialog {{
    background-color: #ffffff;
}}

QMessageBox {{
    background-color: #ffffff;
}}
"""
