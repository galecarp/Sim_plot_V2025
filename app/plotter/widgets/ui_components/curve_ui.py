#!/usr/bin/env python3

"""曲线管理 UI 组件"""
from typing import Optional, List, Callable, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QGroupBox, QLabel

from .base import BaseUIComponents

if TYPE_CHECKING:
    from app.plotter.widgets.curveconfigpanel import CurveConfigPanel

from app.plotter.widgets.curveconfigpanel import CurveConfigPanel


class CurveUIComponents(BaseUIComponents):
    """
    曲线管理相关的 UI 组件容器
    
    管理曲线配置面板的布局和交互组件：
    - 候选曲线选择器
    - 已有曲线容器
    - 曲线配置面板的添加/移除
    
    Attributes:
        container_existing: 已有曲线的容器 Widget
        layout_existing: 已有曲线容器的布局
        selector_candidate: 候选曲线的列表选择器
        groupbox: 曲线管理的分组框
    """
    
    def __init__(self):
        self.container: Optional[QWidget] = None
        self.layout: Optional[QVBoxLayout] = None
        self.selector_candidate: Optional[QListWidget] = None
        self.groupbox: Optional[QGroupBox] = None
        pass
    
    def create_widgets(self,
        parent: Optional[QWidget] = None,
        str_prefix_name: str = "curve",
        func_tr: Optional[Callable[[str, str], str]] = None,
        **kwargs
    ) -> 'CurveUIComponents':
        """
        创建曲线管理UI组件
        
        Args:
            parent: 父widget
            name_prefix: 组件名称前缀
            tr_func: 翻译函数
            **kwargs: 支持以下参数:
                - lst_name_col: 可用的列名列表
            
        Returns:
            self，支持链式调用
        """
        func_tr = func_tr or (lambda text, ctx='': text)
        lst_name_col = kwargs.get('lst_name_col', [])
        
        # 创建分组框
        self.groupbox = QGroupBox(func_tr("曲线管理", 'f_curve_manager'), parent)
        self.groupbox.setObjectName(f"{str_prefix_name}_groupbox")
        boxlayout_manager = QVBoxLayout()
        
        # 1. 创建候选曲线选择器
        label_candidate = QLabel(func_tr("-- 可添加曲线 --", 'f_add_curve_candidate'))
        self.selector_candidate = QListWidget()
        self.selector_candidate.setMaximumHeight(150)
        self.selector_candidate.setObjectName(f"{str_prefix_name}_selector")
        
        # 添加列名
        for str_name_col in lst_name_col:
            self.selector_candidate.addItem(str_name_col)
        
        boxlayout_manager.addWidget(label_candidate)
        boxlayout_manager.addWidget(self.selector_candidate)
        
        # 2. 创建已有曲线容器
        label = QLabel(func_tr("-- 已有曲线 --", 'f_curves_existing'))
        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.container.setLayout(self.layout)
        
        boxlayout_manager.addWidget(label)
        boxlayout_manager.addWidget(self.container)
        
        self.groupbox.setLayout(boxlayout_manager)
        return self
    
    def connect_signals(self, **callbacks) -> 'CurveUIComponents':
        """
        连接信号到回调函数
        
        Args:
            **callbacks: 支持以下回调:
                - on_curve_double_clicked: 双击候选曲线时的回调，参数为曲线名称
                
        Returns:
            self, 支持链式调用
        """
        if on_double_clicked := callbacks.get('on_curve_double_clicked'):
            if self.selector_candidate:
                self.selector_candidate.itemDoubleClicked.connect(
                    lambda item: on_double_clicked(item.text())
                )
        
        return self
    
    def get_main_widget(self) -> Optional[QWidget]:
        """获取主widget（分组框）"""
        return self.groupbox
    
    def add_curve_to_panel(self, panel: 'CurveConfigPanel') -> bool:
        """
        添加曲线配置面板到容器
        
        Args:
            panel: 曲线配置面板实例
            
        Returns:
            是否成功添加
        """
        if not self.layout:
            return False
        self.layout.addWidget(panel)
        return True
    
    def remove_curve_in_panel(self, str_name_col: str) -> bool:
        """
        移除指定曲线的配置面板
        
        Args:
            str_name_col: 曲线名称（实际列名）
            
        Returns:
            是否成功移除
        """
        if not self.layout:
            return False
            
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if self._is_target_panel(widget, str_name_col):
                self.layout.removeWidget(widget)
                widget.deleteLater()
                return True
        return False
    
    def find_curve_in_panel(self, str_name_col: str) -> Optional['CurveConfigPanel']:
        """
        查找指定曲线的配置面板
        
        Args:
            str_name_col: 曲线名称
            
        Returns:
            找到的面板实例，未找到返回 None
        """
        if not self.layout:
            return None
            
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if self._is_panel_for_curve(widget, str_name_col):
                return widget
        return None
    
    def clear_curves_in_panel(self):
        """清空所有曲线配置面板"""
        if not self.layout:
            return
            
        while self.layout.count():
            item = self.layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
        return
    
    @staticmethod
    def _is_panel_for_curve(widget, str_name_col: str) -> bool:
        """
        检查 widget 是否是目标曲线面板
        """
        return (
            isinstance(widget, CurveConfigPanel) and 
                widget.curve_config.str_name_curve == str_name_col)
