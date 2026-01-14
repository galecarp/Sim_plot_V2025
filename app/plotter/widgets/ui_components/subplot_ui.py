#!/usr/bin/env python3

"""子图 UI 组件容器"""
from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QScrollArea, QGroupBox, QVBoxLayout

from .base import BaseUIComponents
from .curve_ui import CurveUIComponents
from .yaxis_ui import YAxisUIComponents


class SubplotUIComponents(BaseUIComponents):
    """
    单个子图的所有 UI 组件容器
    
    作为子图 UI 的顶层容器，聚合了：
    - 曲线管理 UI
    - Y轴管理 UI
    - 子图级别的容器组件
    
    Attributes:
        idx_subplot: 子图索引
        curve_ui: 曲线管理 UI 组件
        yaxis_ui: Y轴管理 UI 组件
        tab_widget: 标签页 Widget
        scroll_area: 滚动区域
        groupbox_yaxis: Y轴管理分组框
        groupbox_curve: 曲线管理分组框
    """
    
    def __init__(self, idx_subplot: int):
        self.idx_subplot = idx_subplot
        
        # 组件级别的 UI 管理
        self.curve_ui = CurveUIComponents()
        self.yaxis_ui = YAxisUIComponents()
        
        # 子图级别的容器
        self.tab_widget: Optional[QWidget] = None
        self.scroll_area: Optional[QScrollArea] = None
        self.groupbox_yaxis: Optional[QGroupBox] = None
        self.groupbox_curve: Optional[QGroupBox] = None
    
    def create_widgets(self,
                      parent: Optional[QWidget] = None,
                      name_prefix: str = "subplot",
                      tr_func: Optional[Callable[[str, str], str]] = None,
                      **kwargs) -> 'SubplotUIComponents':
        """
        创建子图UI组件
        
        Args:
            parent: 父widget
            name_prefix: 组件名称前缀
            tr_func: 翻译函数
            **kwargs: 支持以下参数:
                - lst_name_col: 可用的列名列表
                
        Returns:
            self，支持链式调用
        """
        tr = tr_func or (lambda text, ctx='': text)
        lst_name_col = kwargs.get('lst_name_col', [])
        
        # 创建主标签页widget
        self.tab_widget = QWidget(parent)
        self.tab_widget.setObjectName(f"{name_prefix}_tab")
        layout_main = QVBoxLayout()
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        widget_scroll = QWidget()
        layout_scroll = QVBoxLayout()
        
        # 创建Y轴管理UI
        self.yaxis_ui.create_widgets(
            parent=widget_scroll,
            name_prefix=f"{name_prefix}_yaxis",
            tr_func=tr
        )
        self.groupbox_yaxis = self.yaxis_ui.groupbox
        layout_scroll.addWidget(self.yaxis_ui.get_main_widget())
        
        # 创建曲线管理UI
        self.curve_ui.create_widgets(
            parent=widget_scroll,
            name_prefix=f"{name_prefix}_curve",
            tr_func=tr,
            lst_name_col=lst_name_col
        )
        self.groupbox_curve = self.curve_ui.groupbox
        layout_scroll.addWidget(self.curve_ui.get_main_widget())
        
        # 添加伸缩空间
        layout_scroll.addStretch()
        
        # 组装滚动区域
        widget_scroll.setLayout(layout_scroll)
        self.scroll_area.setWidget(widget_scroll)
        layout_main.addWidget(self.scroll_area)
        self.tab_widget.setLayout(layout_main)
        
        return self
    
    def connect_signals(self, **callbacks) -> 'SubplotUIComponents':
        """
        连接信号到回调函数
        
        Args:
            **callbacks: 支持以下回调:
                - on_add_axis: 添加Y轴时的回调
                - on_curve_double_clicked: 双击曲线时的回调
                
        Returns:
            self，支持链式调用
        """
        # 连接Y轴相关信号
        if on_add_axis := callbacks.get('on_add_axis'):
            self.yaxis_ui.connect_signals(on_add_axis=on_add_axis)
        
        # 连接曲线相关信号
        if on_curve_double_clicked := callbacks.get('on_curve_double_clicked'):
            self.curve_ui.connect_signals(on_curve_double_clicked=on_curve_double_clicked)
        
        return self
    
    def get_main_widget(self) -> Optional[QWidget]:
        """获取主widget（标签页widget）"""
        return self.tab_widget
    
    def clear_all(self):
        """清空所有 UI 组件"""
        self.curve_ui.clear_all_panels()
        self.yaxis_ui.clear_all_panels()
