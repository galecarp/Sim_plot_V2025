#!/usr/bin/env python3

from typing import List, Dict, Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QColorDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

from code_source.pyqtcurveplotter.graphconfigs.curveconfig import CurveConfig
from code_source.pyqtcurveplotter.graphconfigs.axisconfig import AxisConfig


class CurveConfigPanel(QWidget):
    """
    曲线配置面板
    
    用于配置单条曲线的显示属性（Y轴、颜色、线型等）
    """
    sig_delete_requested = pyqtSignal(str)  # 发射曲线名称
    sig_config_changed = pyqtSignal()
    
    def __init__(self, 
        curve_config: CurveConfig,
        dic_axisconfig: Dict[str, AxisConfig],
        func_get_display_name: Optional[Callable[[str], str]] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Args:
            curve_config: 曲线配置对象
            dic_axisconfig: Y轴配置字典的引用 (动态获取可用轴列表)
            func_get_display_name: 获取显示名称的回调函数
            parent: 父组件
        """
        super().__init__(parent)
        self.curve_config = curve_config
        self.dic_axisconfig = dic_axisconfig  # 保存字典引用
        self.func_get_display_name = func_get_display_name or (lambda x: x)
        
        self._init_ui()
        pass
    
    def _get_lst_axis_avail(self) -> List[str]:
        """
        动态获取当前可用的Y轴列表
        """
        return list(self.dic_axisconfig.keys())
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 第一行: 曲线名称 + 删除按钮
        hbox_header = QHBoxLayout()
        
        # 显示曲线名称（带图标）
        str_display_name = self.func_get_display_name(self.curve_config.str_name_curve)
        label_name = QLabel(f"📈 {str_display_name}")
        label_name.setStyleSheet("font-weight: bold; font-size: 11pt;")
        hbox_header.addWidget(label_name)
        
        hbox_header.addStretch()
        
        # 删除按钮
        btn_delete = QPushButton("×")
        btn_delete.setMaximumWidth(30)
        btn_delete.setStyleSheet("color: red; font-weight: bold; font-size: 14pt;")
        btn_delete.setToolTip("删除此曲线")
        btn_delete.clicked.connect(
            lambda: self.sig_delete_requested.emit(self.curve_config.str_name_curve)
        )
        hbox_header.addWidget(btn_delete)
        
        layout.addLayout(hbox_header)
        
        # 配置项表单
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 5, 10, 5)
        
        # Y轴选择
        self.combo_axis = QComboBox()
        lst_name_axis_available = self._get_available_axes()  # 动态获取
        self.combo_axis.addItems(lst_name_axis_available)
        # 设置当前选中的轴
        if self.curve_config.str_name_axis in lst_name_axis_available:
            idx = lst_name_axis_available.index(self.curve_config.str_name_axis)
            self.combo_axis.setCurrentIndex(idx)
        # 连接信号
        self.combo_axis.currentTextChanged.connect(self._on_axis_changed)
        form_layout.addRow("Y轴:", self.combo_axis)
        
        # 颜色选择
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(25)
        self.btn_color.setStyleSheet(
            f"background-color: {self.curve_config.color.name()}; "
            f"border: 1px solid #888;"
        )
        self.btn_color.clicked.connect(self._select_color)
        form_layout.addRow("颜色:", self.btn_color)
        
        # 线型选择
        self.combo_linestyle = QComboBox()
        self.combo_linestyle.addItems(["-", "--", "-.", ":"])
        # 设置当前线型
        if hasattr(self.curve_config, 'linestyle'):
            linestyle_map = {'-': 0, '--': 1, '-.': 2, ':': 3}
            idx = linestyle_map.get(self.curve_config.linestyle, 0)
            self.combo_linestyle.setCurrentIndex(idx)
        self.combo_linestyle.currentTextChanged.connect(self._on_linestyle_changed)
        form_layout.addRow("线型:", self.combo_linestyle)
        
        layout.addLayout(form_layout)
        
        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        self.setLayout(layout)
    
    def _on_axis_changed(self, str_name_axis: str):
        """Y轴改变时的回调"""
        self.curve_config.str_name_axis = str_name_axis
        self.sig_config_changed.emit()
    
    def _on_linestyle_changed(self, linestyle: str):
        """线型改变时的回调"""
        self.curve_config.linestyle = linestyle
        self.sig_config_changed.emit()
    
    def _select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(
            self.curve_config.color, 
            self, 
            "选择曲线颜色"
        )
        if color.isValid():
            self.curve_config.color = color
            self.btn_color.setStyleSheet(
                f"background-color: {color.name()}; "
                f"border: 1px solid #888;"
            )
            self.sig_config_changed.emit()
    
    def refresh_available_axes(self):
        """
        刷新可用轴列表
        
        当添加/删除Y轴时调用此方法更新下拉框选项
        通过 dic_axisconfig 动态获取最新的轴列表
        """
        current_axis = self.combo_axis.currentText()
        lst_name_axis_available = self._get_available_axes()  # 动态获取
        
        self.combo_axis.blockSignals(True)
        self.combo_axis.clear()
        self.combo_axis.addItems(lst_name_axis_available)
        
        # 恢复之前的选择
        if current_axis in lst_name_axis_available:
            idx = lst_name_axis_available.index(current_axis)
            self.combo_axis.setCurrentIndex(idx)
        else:
            # 如果之前的轴被删除了，默认选择主轴（第一个）
            if lst_name_axis_available:
                self.combo_axis.setCurrentIndex(0)
                self.curve_config.str_name_axis = lst_name_axis_available[0]
        
        self.combo_axis.blockSignals(False)

