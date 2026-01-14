#!/usr/bin/env python3

"""UI组件容器的抽象基类"""
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any
from PySide6.QtWidgets import QWidget


class BaseUIComponents(ABC):
    """
    UI组件容器的抽象基类
    
    定义所有UI组件类必须实现的接口规范：
    - create_widgets: 创建UI组件
    - connect_signals: 连接信号到回调
    - get_main_widget: 获取主widget
    """
    
    @abstractmethod
    def create_widgets(self, 
        parent: Optional[QWidget] = None,
        str_prefix_name: str = "",
        func_tr: Optional[Callable[[str, str], str]] = None,
        **kwargs
    ) -> 'BaseUIComponents':
        """
        创建所有UI widgets
        
        Args:
            parent: 父widget
            name_prefix: 组件名称前缀，用于设置objectName
            tr_func: 翻译函数，接受(text, context)返回翻译后的文本
            **kwargs: 其他特定参数
            
        Returns:
            self，支持链式调用
        """
        pass
    
    @abstractmethod
    def connect_signals(self, **callbacks) -> 'BaseUIComponents':
        """
        连接信号到回调函数
        
        Args:
            **callbacks: 信号名到回调函数的映射
                例如: on_clicked=handler_func
            
        Returns:
            self，支持链式调用
        """
        pass
    
    @abstractmethod
    def get_main_widget(self) -> Optional[QWidget]:
        """
        获取主要的widget（用于添加到父布局）
        
        Returns:
            主widget，如果未创建则返回None
        """
        pass
