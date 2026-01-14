#!/usr/bin/env python3

from typing import Tuple, List, Set, Dict, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QGroupBox, QCheckBox, QComboBox, QPushButton, QLabel, 
    QDoubleSpinBox, QScrollArea, QColorDialog, QFormLayout, 
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QLineEdit, QSpinBox, QFrame, QTabWidget, QDateTimeEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.plotter.widgets.axisconfigpanel import AxisConfigPanel
from app.plotter.graphconfigs.axisconfig import AxisConfig
from app.plotter.graphconfigs.curveconfig import CurveConfig
from app.plotter.widgets.curveconfigpanel import CurveConfigPanel
from app.plotter.widgets.ui_components import (
    SubplotUIComponents, XAxisUIComponents
)


class SidePanel(QWidget):
    """
    侧边栏配置面板
    """
    # 信号
    sig_config_changed = Signal()
    sig_xaxis_time_changed = Signal(float, float)
    
    def __init__(self,
        lst_name_col: List[str],
        n_subplot: int = 3,
        parent: Optional[QWidget] = None,
    ):
        """
        Args:
            lst_name_col: 数据列名列表（实际列名）
            n_subplot: 子图数量
            parent: 父组件
        """
        super().__init__(parent=parent)
        self._str_name = "SidePanel"
        self.lst_name_col = lst_name_col
        self.n_subplot = n_subplot
        # 常值
        self.str_name_axis_left = 'main'  # 主轴名称
        
        # 初始化轴配置管理器
        self._init_axisconfig_subplot()
        # 初始化曲线配置管理器
        self._init_curveconfig_subplot()
        # 初始化子图的已显示列存储
        self._init_added_cols_subplot()
        # 初始化UI组件容器
        self._init_ui_components()
        # 初始化侧边栏的标签页
        self.init_all_tabs()

    def _init_axisconfig_subplot(self):
        """初始化轴配置存储
        
        dic_axisconfig_subplot 结构:
            {
                idx_subplot : {
                    str_name_axis : AxisConfig,
                    ...
                },
                ...
            }
        """
        self.dic_axisconfig_subplot: Dict[int, Dict[str, AxisConfig]] = {
            idx_subplot : {}
            for idx_subplot in range(self.n_subplot)
        }
    
    def _init_curveconfig_subplot(self):
        """初始化曲线存储

        dic_curveconfig_subplot 结构:
            {
                idx_subplot : {
                    str_name_col_actual : CurveConfig,
                    ...
                },
                ...
            }
        """
        # 初始化空字典
        self.dic_curveconfig_subplot: Dict[int, Dict[str, CurveConfig]] = {
            idx_subplot : {}
            for idx_subplot in range(self.n_subplot)
        }

    def _init_added_cols_subplot(self):
        """初始化子图的已显示列存储
        dic_added_cols_subplot 结构:
            {
                idx_subplot : Set[str_name_col_actual],
                ...
            }
        """
        self.dic_added_cols_subplot : Dict[int, Set[str]] = {
            idx_subplot : set()
            for idx_subplot in range(self.n_subplot)
        }

    def _init_ui_components(self):
        """初始化UI组件容器
        
        为每个子图创建 SubplotUIComponents 实例
        同时创建全局的 XAxisUIComponents 实例
        """
        # 子图UI组件
        self.dic_ui_subplot: Dict[int, SubplotUIComponents] = {
            idx_subplot: SubplotUIComponents(idx_subplot=idx_subplot)
            for idx_subplot in range(self.n_subplot)
        }
        
        # 时间轴UI组件（全局共享）
        self.xaxis_ui = XAxisUIComponents()

    def init_all_tabs(self):
        """初始化子图的设置标签页
        """
        # 主布局
        layout_main = QVBoxLayout()
        # 标签页
        self.widget_tab = QTabWidget()
        str_name_widget_tab = f"{self._str_name}_tab_widget"
        self.widget_tab.setObjectName(str_name_widget_tab)
        
        # 1.通用设置
        tab_general = QWidget()
        self.widget_tab.addTab(tab_general,
            self.tr("通用设置", 'f_config_general'))

        # 2.时间设置标签页
        tab_time = self._create_xaxis_tab()
        self.widget_tab.addTab(tab_time,
            self.tr("时间设置", 'f_setting_time'))
        
        # 3.为每个子图创建单独的plot标签页
        for idx_subplot in range(self.n_subplot):
            tab_plot = self._create_plot_tab(idx_subplot)
            self.widget_tab.addTab(tab_plot,
                self.tr("子图{}", 'f_subplot').format(idx_subplot + 1))
        
        # 组织主布局
        layout_main.addWidget(self.widget_tab)
        self.setLayout(layout_main)
    
    def _create_xaxis_tab(self) -> QWidget:
        """创建xaxis用的时间设置标签页"""
        self.xaxis_ui.create_widgets(
            parent=self,
            name_prefix=f"{self._str_name}_xaxis",
            tr_func=self.tr
        ).connect_signals(
            on_time_changed=self.emit_xaxis_time_range,
            on_unit_changed=self._on_span_unit_changed
        )
        
        return self.xaxis_ui.get_main_widget()
    def _create_plot_tab(self, idx_subplot: int) -> QWidget:
        """创建子图配置标签页"""
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        
        # 创建子图UI组件
        subplot_ui.create_widgets(
            parent=self,
            name_prefix=f"{self._str_name}_subplot_{idx_subplot}",
            tr_func=self.tr,
            lst_name_col=self.lst_name_col
        ).connect_signals(
            on_add_axis=lambda: self.add_axis(idx_subplot),
            on_curve_double_clicked=lambda name: self.add_curve(idx_subplot, name)
        )
        
        # 添加默认左侧主轴配置面板
        self._add_axis_config_panel(
            idx_subplot=idx_subplot,
            str_name_axis=self.str_name_axis_left
        )
        
        return subplot_ui.get_main_widget()
    
    # 轴和曲线管理方法
    def add_axis(self, idx_subplot: int):
        """添加新轴"""
        # 生成轴ID
        lst_name_axis = list(self.dic_axisconfig_subplot[idx_subplot].keys())
        str_name_axis = f"axis_{len(lst_name_axis)}"
        
        # 创建轴配置
        axisconfig = AxisConfig(
            str_name_axis=str_name_axis,
            side_axis='right',
            label=f"轴 {len(lst_name_axis)}",
            color=QColor(100 + len(lst_name_axis) * 40, 100, 200)
        )
        
        self.dic_axisconfig_subplot[idx_subplot][str_name_axis] = axisconfig
        self._add_axis_config_panel(idx_subplot, str_name_axis)
        
        # 更新所有曲线的可用轴列表
        self._update_all_available_axes(idx_subplot)
        
        self.sig_config_changed.emit()
    
    def _add_axis_config_panel(self, idx_subplot: int, str_name_axis: str):
        """添加轴配置面板"""
        axisconfig = self.dic_axisconfig_subplot[idx_subplot][str_name_axis]
        
        panel = AxisConfigPanel(
            axis_config=axisconfig,
            dic_axisconfig=self.dic_axisconfig_subplot[idx_subplot]
        )
        panel.sig_config_changed.connect(self.sig_config_changed.emit)
        panel.sig_delete_requested.connect(lambda aid: self.remove_axis(idx_subplot, aid))
        
        # 使用yaxis_ui添加面板
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        add_separator = (str_name_axis != 'main')
        subplot_ui.yaxis_ui.add_axis_panel(str_name_axis, panel, add_separator)
        
        # 保存引用
        setattr(panel, '_axis_id', str_name_axis)
        setattr(panel, '_plot_idx', idx_subplot)
    
    def remove_axis(self, idx_subplot: int, str_name_axis: str):
        """移除轴"""
        if str_name_axis == 'main':
            return
        
        # 删除配置
        if str_name_axis in self.dic_axisconfig_subplot[idx_subplot]:
            del self.dic_axisconfig_subplot[idx_subplot][str_name_axis]
        
        # 使用yaxis_ui删除面板
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        subplot_ui.yaxis_ui.remove_axis_panel(str_name_axis)
        
        # 更新曲线的轴选择（将使用被删除轴的曲线改为主轴）
        for str_name_col, curve_config in self.dic_curveconfig_subplot[idx_subplot].items():
            if curve_config.str_name_axis == str_name_axis:
                curve_config.str_name_axis = 'main'
        
        self._update_all_available_axes(idx_subplot)
        self.sig_config_changed.emit()
    
    def add_curve(self, idx_subplot: int, str_name_col_actual: str):
        """添加曲线"""
        if not str_name_col_actual:
            return
        
        # 检查是否已添加
        if str_name_col_actual in self.dic_added_cols_subplot[idx_subplot]:
            print(f"子图{idx_subplot}已包含列 {str_name_col_actual}，无法重复添加")
            return
        
        # 创建曲线配置
        if str_name_col_actual not in self.dic_curveconfig_subplot[idx_subplot]:
            colors = [
                QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
                QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)
            ]
            color_idx = len(self.dic_curveconfig_subplot[idx_subplot]) % len(colors)
            
            curve_config = CurveConfig(
                str_name_curve=str_name_col_actual,
                idx_subplot=idx_subplot,
                color=colors[color_idx]
            )
            self.dic_curveconfig_subplot[idx_subplot][str_name_col_actual] = curve_config
        else:
            curve_config = self.dic_curveconfig_subplot[idx_subplot][str_name_col_actual]
        
        # 记录入子图正在显示的列集合
        self.dic_added_cols_subplot[idx_subplot].add(str_name_col_actual)
        
        # 创建UI组件
        widget = CurveConfigPanel(
            curve_config=curve_config,
            dic_axisconfig=self.dic_axisconfig_subplot[idx_subplot]
        )
        widget.sig_config_changed.connect(self.sig_config_changed.emit)
        widget.sig_delete_requested.connect(lambda name: self.remove_curve(idx_subplot, name))
        
        # 使用curve_ui添加面板
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        subplot_ui.curve_ui.add_curve_panel(widget)
        
        self.sig_config_changed.emit()
    
    def remove_curve(self, idx_subplot: int, str_name_col_actual: str):
        """移除曲线"""
        # 从集合中删除
        self.dic_added_cols_subplot[idx_subplot].discard(str_name_col_actual)
        
        # 使用curve_ui从UI删除
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        subplot_ui.curve_ui.remove_curve_panel(str_name_col_actual)
        
        self.sig_config_changed.emit()
    
    def _update_all_available_axes(self, idx_subplot: int):
        """更新所有组件的可用轴列表"""
        subplot_ui = self.dic_ui_subplot[idx_subplot]
        if not subplot_ui.curve_ui.layout_existing:
            return
            
        # 遍历所有曲线面板
        for i in range(subplot_ui.curve_ui.layout_existing.count()):
            widget = subplot_ui.curve_ui.layout_existing.itemAt(i).widget()
            if isinstance(widget, CurveConfigPanel):
                widget.refresh_available_axes()
    
    def _on_span_unit_changed(self, index: int):
        """时间段单位改变时的回调"""
        suffixes = [" hour", " day", " week", " month", " year"]
        if self.xaxis_ui.spin_span:
            self.xaxis_ui.spin_span.setSuffix(suffixes[index])
        self.emit_xaxis_time_range()
    
    def _get_span_in_seconds(self) -> float:
        """获取时间段长度（转换为秒）"""
        return self.xaxis_ui.get_span_in_seconds()
    
    def emit_xaxis_time_range(self):
        """回调, 文字输入框触发发射时间范围改变信号"""
        flt_start = self.xaxis_ui.get_start_timestamp()
        flt_duration = self.xaxis_ui.get_span_in_seconds()
        self.sig_xaxis_time_changed.emit(flt_start, flt_start + flt_duration)
    
    def update_time_range(self, start: float, end: float):
        """从外部更新时间范围"""
        self.xaxis_ui.set_time_range(start, end)
    
    def get_plot_axes(self, idx_subplot: int) -> Dict[str, AxisConfig]:
        """获取子图的轴配置"""
        return self.dic_axisconfig_subplot[idx_subplot]
    
    def get_plot_curves(self, idx_subplot: int) -> List[CurveConfig]:
        """获取子图的曲线配置"""
        return [
            c for c in self.dic_curveconfig_subplot[idx_subplot].values() 
            if hasattr(c, 'enabled') and c.enabled
        ]
