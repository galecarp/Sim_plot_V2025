#!/usr/bin/env python3
"""
静态翻译基类

使用 Qt 的标准翻译机制，在应用启动时加载翻译文件
不支持运行时动态切换语言
"""

from typing import Optional, List
from PySide6.QtCore import QObject


class StaticTranslationMixin:
    """
    静态翻译 Mixin 类
    
    使用 Qt 的 .tr() 方法进行翻译，翻译文件在应用启动时加载
    不提供运行时语言切换功能
    
    使用方法：
    
    ```python
    class MyWidget(QWidget, StaticTranslationMixin):
        def __init__(self):
            super().__init__()
            self.init_ui()
            
        def init_ui(self):
            # 使用 tr() 方法，Qt 会自动从加载的翻译文件中查找
            label = QLabel(self.tr("标签文本", "context_name"))
            button = QPushButton(self.tr("按钮", "context_name"))
    ```
    
    翻译文件生成：
    1. 使用 pylupdate 生成 .ts 文件：
       pylupdate6 app/plotter/**/*.py -ts app/plotter/i18n/plotter_zh_CN.ts
    
    2. 使用 Qt Linguist 翻译 .ts 文件
    
    3. 使用 lrelease 编译成 .qm 文件：
       lrelease app/plotter/i18n/plotter_zh_CN.ts
    
    4. 在应用启动时加载翻译文件（在 __main__.py 中）：
       translator = QTranslator()
       translator.load("app/plotter/i18n/plotter_zh_CN.qm")
       app.installTranslator(translator)
    """
    
    def tr(self, text: str, disambiguation: Optional[str] = None, n: int = -1) -> str:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本（通常是英文或中文原文）
            disambiguation: 消歧义上下文，用于区分相同文本在不同场景的翻译
            n: 用于复数形式的数字（在某些语言中）
            
        Returns:
            翻译后的文本
        """
        # 调用 QObject.tr() 或 QWidget.tr() 进行翻译
        # 如果是 QWidget 的子类，会自动使用 QWidget 的 tr
        # 如果是 QObject 的子类，会使用 QObject 的 tr
        if isinstance(self, QObject):
            if disambiguation:
                return QObject.tr(self, text, disambiguation, n)
            else:
                return QObject.tr(self, text, None, n)
        else:
            # 如果不是 QObject，直接返回原文本
            return text


class ColumnNameTranslator:
    """
    列名翻译器（静态版本）
    
    使用 Qt 的翻译机制翻译数据列名
    列名翻译也写在 .ts/.qm 文件中
    """
    
    def __init__(self, context: str = "ColumnNames"):
        """
        Args:
            context: 翻译上下文，用于在 .ts 文件中组织列名翻译
        """
        self.context = context
    
    def translate(self, column_name: str) -> str:
        """
        翻译列名
        
        Args:
            column_name: 实际的列名（英文或拼音）
            
        Returns:
            翻译后的列名（如果找不到翻译则返回原列名）
        """
        # 使用 QCoreApplication.translate 进行翻译
        from PySide6.QtCore import QCoreApplication
        translated = QCoreApplication.translate(self.context, column_name)
        return translated if translated != column_name else column_name
    
    def get_display_name(self, actual_name: str) -> str:
        """
        获取列名的显示名称（翻译后的名称）
        
        Args:
            actual_name: 实际列名
            
        Returns:
            显示名称
        """
        return self.translate(actual_name)
    
    def get_actual_name(self, display_name: str) -> Optional[str]:
        """
        从显示名称获取实际列名
        
        注意：这是反向查找，在静态翻译模式下较难实现
        建议始终使用实际列名作为内部标识
        
        Args:
            display_name: 显示名称
            
        Returns:
            实际列名（如果找不到返回 display_name 本身）
        """
        # 简化实现：直接返回 display_name
        # 如果需要反向查找，需要维护一个映射表
        return display_name
