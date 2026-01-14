#!/usr/bin/env python3

import polars as pl

from typing import List, Dict, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QComboBox,
    QGroupBox, QRadioButton, QCheckBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QSplitter
import pyqtgraph as pg

from code_source.polars_toolkits.datetime_toolkits.utilpolarsdatetime import get_timestamp_min_max
from app.plotter.plotaxismanager import PlotAxisManager
from app.plotter.graphconfigs.axisconfig import AxisConfig
from app.plotter.graphconfigs.curveconfig import CurveConfig
from app.plotter.widgets.sidepanel import SidePanel
from app.plotter.translation import ColumnNameTranslator
    

class MultiCurvePlotterWidget(QMainWindow):
    """
    主窗口, 多Y轴时序数据可视化
    """
    
    def __init__(self,
        lf: pl.LazyFrame,
        str_name_col_timestamp: str = None,
        column_translator: Optional[ColumnNameTranslator] = None
    ):
        """
        Args:
            lf: Polars LazyFrame数据源
            str_name_col_timestamp: 时间列名称
            column_translator: 列名翻译器，如果为None则使用默认翻译器
        """
        # 父类初始化
        super(QMainWindow, self).__init__()
        # 初始化数据
        self.lf = lf
        
        # 初始化列名翻译器
        self.column_translator = column_translator or ColumnNameTranslator()
        
        # 时间列名称
        self._init_name_col_timestamp(lf, str_name_col_timestamp)
        
        # 计算时间范围（需要collect一小部分）
        self._init_time_range_data()
        
        # 轴管理器
        self._init_axismanager_subplot()
        # 初始化主界面
        self._init_layout_main()
        self.setup_plots()
        self.setup_connections()
        
        # 初始化数据
        self.update_all_plots()
        pass

    def _init_name_col_timestamp(self,
        lf : pl.LazyFrame,
        str_name_col_timestamp: Optional[str]
    ) -> str:
        """
        初始化lf的时间列名称
        """
        # 确定时间列
        if str_name_col_timestamp is None:
            # 假设第一列是时间
            self.str_name_col_timestamp = lf.collect_schema.columns[0]
        else:
            self.str_name_col_timestamp = str_name_col_timestamp
        return

    def _init_time_range_data(self):
        """
        提取数据的范围
        """
        self.ts_timestamp_data_min, self.ts_timestamp_data_max, self.time_range = get_timestamp_min_max(
            self.lf,
            self.str_name_col_timestamp,
            bol_return_hour=True
        )
        
        print(f"时间范围: {self.ts_timestamp_data_min:.2f} ~ {self.ts_timestamp_data_max:.2f} (共 {self.time_range:.2f})")
        return
    
    def _init_axismanager_subplot(self):
        """初始化子图的轴管理器
        """
        # 初始化所有的主y轴
        self.dic_axismanager_subplot: Dict[int, PlotAxisManager] = {}
        self.axis_managers = {}
        pass

    def get_display_name(self, actual_name: str) -> str:
        """
        获取列名的显示名称（翻译后的名称）
        
        Args:
            actual_name: 实际列名
            
        Returns:
            显示名称
        """
        return self.column_translator.get_display_name(actual_name)
    
    def get_actual_name(self, display_name: str) -> Optional[str]:
        """
        从显示名称获取实际列名
        
        Args:
            display_name: 显示名称
            
        Returns:
            实际列名
        """
        return self.column_translator.get_actual_name(display_name)

    def _init_layout_main(self):
        """
        初始化 窗口的主界面
        """
        # 窗口标题和尺寸（使用 tr() 进行翻译）
        self.setWindowTitle(self.tr("时序数据可视化 - 多Y轴支持", "f_title_window_main"))
        self.setGeometry(100, 100, 1600, 1000)
        
        # 主布局
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        boxlayout_central = QHBoxLayout(widget_central)
        
        # 分割窗口
        splitter_window = QSplitter(Qt.Orientation.Horizontal)
        
        # 获取所有数据列名（排除时间列）
        lst_name_col_data = [col for col in self.lf.collect_schema.names if col != self.str_name_col_timestamp]
        
        # 侧边栏（传递列名翻译回调函数）
        self.side_panel = SidePanel(
            lst_name_col=lst_name_col_data,
            n_subplot=3,
            func_get_display_name=self.get_display_name,
            func_get_actual_name=self.get_actual_name
        )
        self.side_panel.setMaximumWidth(500)
        self.side_panel.setMinimumWidth(300)
        splitter_window.addWidget(self.side_panel)
        
        # 图表区域
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # PyQtGraph 配置
        pg.setConfigOptions(antialias=True, useOpenGL=True)
        self.graphics_layout = pg.GraphicsLayoutWidget()
        plot_layout.addWidget(self.graphics_layout)
        
        splitter_window.addWidget(plot_widget)
        splitter_window.setStretchFactor(1, 1)
        
        boxlayout_central.addWidget(splitter_window)
    
    def setup_plots(self):
        """设置图表"""
        self.plots = []
        
        # 创建3个子图
        for i in range(3):
            plot = self.graphics_layout.addPlot(row=i, col=0)
            plot.setLabel('left', f'子图 {i+1}')
            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.addLegend()
            
            # 性能优化
            plot.setDownsampling(auto=True, mode='peak')
            plot.setClipToView(True)
            
            self.plots.append(plot)
            
            # 创建轴管理器
            self.axis_managers[i] = PlotAxisManager(plot)
        
        # 时间轴导航
        self.time_plot = self.graphics_layout.addPlot(row=3, col=0)
        self.time_plot.setLabel('left', '时间轴导航')
        self.time_plot.setLabel('bottom', '时间')
        self.time_plot.setMaximumHeight(150)
        
        # 区域选择器
        initial_range = min(self.time_range * 0.1, 1000)
        self.region = pg.LinearRegionItem(
            values=[self.ts_timestamp_data_min, self.ts_timestamp_data_min + initial_range],
            brush=pg.mkBrush(100, 100, 200, 50)
        )
        self.region.setZValue(10)
        self.time_plot.addItem(self.region)
        
        # 时间轴绘制降采样数据
        self._plot_time_navigator()
        
        # 链接主图X轴
        for i in range(1, 3):
            self.plots[i].setXLink(self.plots[0])
    
    def _plot_time_navigator(self):
        """绘制时间轴导航图"""
        # 获取数据列
        lst_name_col_data = [col for col in self.lf.collect_schema.names if col != self.str_name_col_timestamp]
        
        if len(lst_name_col_data) == 0:
            return
        
        # 降采样到5000点
        n_total = self.lf.select(pl.count()).collect()[0, 0]
        step = max(1, n_total // 5000)
        
        # 获取降采样数据
        nav_data = (self.lf
                   .select([
                       pl.col(self.str_name_col_timestamp),
                       pl.col(lst_name_col_data[0])
                   ])
                   .collect()
                   .gather_every(step))
        
        time_data = nav_data[self.str_name_col_timestamp].to_numpy()
        value_data = nav_data[lst_name_col_data[0]].to_numpy()
        
        self.time_plot.plot(time_data, value_data, pen=pg.mkPen('w', width=1))
    
    def setup_connections(self):
        """设置信号连接"""
        self.side_panel.configChanged.connect(self.on_config_changed)
        self.side_panel.timeRangeChanged.connect(self.on_sidebar_time_change)
        self.region.sigRegionChanged.connect(self.on_region_changed)
    
    @Slot()
    def on_config_changed(self):
        """配置改变"""
        # 更新所有子图
        self.update_all_plots()
    
    @Slot()
    def on_region_changed(self):
        """时间区域改变"""
        min_x, max_x = self.region.getRegion()
        
        # 更新主图范围
        for plot in self.plots:
            plot.setXRange(min_x, max_x, padding=0)
        
        # 更新侧边栏
        self.side_panel.update_time_range(min_x, max_x)
        
        # 更新数据
        self.update_all_plots()
    
    @Slot(float, float)
    def on_sidebar_time_change(self, start: float, end: float):
        """侧边栏时间改变"""
        self.region.setRegion([start, end])
    
    def update_all_plots(self):
        """更新所有子图"""
        for plot_idx in range(3):
            self.update_plot(plot_idx)
    
    def update_plot(self, plot_idx: int):
        """更新单个子图"""
        plot = self.plots[plot_idx]
        axis_manager = self.axis_managers[plot_idx]
        
        # 获取时间范围
        min_x, max_x = self.region.getRegion()
        
        # 获取配置
        axis_configs = self.side_panel.get_plot_axes(plot_idx)
        curve_configs = self.side_panel.get_plot_curves(plot_idx)
        
        # 更新轴配置
        self._update_axes(plot_idx, axis_configs)
        
        # 按轴分组曲线
        curves_by_axis = {}
        for curve_config in curve_configs:
            axis_id = curve_config.axis_id
            if axis_id not in curves_by_axis:
                curves_by_axis[axis_id] = []
            curves_by_axis[axis_id].append(curve_config)
        
        # 清除旧曲线
        for axis_id, vb in axis_manager.viewboxes.items():
            for item in vb.allChildren():
                if isinstance(item, pg.PlotCurveItem):
                    vb.removeItem(item)
        
        # 获取数据并绘制
        for axis_id, curves in curves_by_axis.items():
            vb = axis_manager.get_viewbox(axis_id)
            if not vb:
                continue
            
            for curve_config in curves:
                self._plot_curve(vb, curve_config, min_x, max_x)
        
        # 应用范围和对齐
        for axis_id in axis_configs.keys():
            axis_manager.apply_axis_range(axis_id)
        
        for axis_id in axis_configs.keys():
            axis_manager.apply_alignment(axis_id)
    
    def _update_axes(self, plot_idx: int, axis_configs: Dict[str, AxisConfig]):
        """更新子图的轴"""
        axis_manager = self.axis_managers[plot_idx]
        
        # 获取现有轴
        existing_axes = set(axis_manager.axes.keys())
        new_axes = set(axis_configs.keys())
        
        # 删除不再需要的轴
        for axis_id in existing_axes - new_axes:
            if axis_id != 'main':
                axis_manager.remove_axis(axis_id)
        
        # 添加新轴
        for axis_id in new_axes - existing_axes:
            if axis_id != 'main':
                axis_manager.add_axis(axis_configs[axis_id])
        
        # 更新现有轴的配置
        for axis_id, config in axis_configs.items():
            if axis_id in axis_manager.axes:
                axis_manager.axes[axis_id] = config
                # 更新轴标签（使用翻译后的名称）
                if config.axis_item:
                    str_label_display = self.get_display_name(config.label)
                    config.axis_item.setLabel(
                        str_label_display,
                        units=config.unit,
                        color=config.color
                    )
    
    def _plot_curve(
        self,
        viewbox: pg.ViewBox,
        curve_config: CurveConfig,
        min_x: float,
        max_x: float
    ):
        """绘制单条曲线"""
        # 从LazyFrame获取数据（延迟计算）
        curve_data = (self.lf
                     .filter(
                         (pl.col(self.str_name_col_timestamp) >= min_x) &
                         (pl.col(self.str_name_col_timestamp) <= max_x)
                     )
                     .select([
                         pl.col(self.str_name_col_timestamp),
                         pl.col(curve_config.curve_name)
                     ])
                     .collect())
        
        # 降采样
        max_points = 10000
        if len(curve_data) > max_points:
            step = len(curve_data) // max_points
            curve_data = curve_data.gather_every(step)
        
        time_data = curve_data[self.str_name_col_timestamp].to_numpy()
        value_data = curve_data[curve_config.curve_name].to_numpy()
        
        # 创建pen
        pen = self._create_pen(curve_config)
        
        # 获取显示名称用于图例
        str_curve_name_display = self.get_display_name(curve_config.curve_name)
        
        # 绘制（使用翻译后的显示名称）
        curve_item = pg.PlotCurveItem(
            time_data,
            value_data,
            pen=pen,
            name=str_curve_name_display,
            stepMode=curve_config.is_step
        )
        
        viewbox.addItem(curve_item)
        curve_config.curve_item = curve_item
    
    def _create_pen(self, curve_config: CurveConfig):
        """创建pen"""
        style_map = {
            'solid': Qt.PenStyle.SolidLine,
            'dash': Qt.PenStyle.DashLine,
            'dot': Qt.PenStyle.DotLine,
            'dashdot': Qt.PenStyle.DashDotLine
        }
        
        return pg.mkPen(
            color=curve_config.color,
            width=curve_config.line_width,
            style=style_map.get(curve_config.line_style, Qt.PenStyle.SolidLine)
        )
