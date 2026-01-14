#!/usr/bin/env python3

from typing import Optional
from dataclasses import dataclass, field
from PySide6.QtGui import QColor

from app.plotter.enums.modeenum import AlignmentMode, RangeMode
from app.plotter.enums.plotenum import SideAxis
from app.plotter.enums.valueenum import UnitValue


@dataclass
class AxisConfig:
    """单一一条Y轴配置"""
    str_name_axis: str                        # 此轴名字
    set_name_col: set[str] = field(default_factory=set)  # 绑定到此轴的列名集合
    side_axis: SideAxis = SideAxis.LEFT       # 此轴处于左侧还是右侧
    str_label: str = ""                       # 轴标签
    unit_value: UnitValue = UnitValue.MWH     # 轴数据使用的单位
    color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    
    # 范围设置
    mode_range: RangeMode = RangeMode.AUTO
    ## 范围上下限仅在 Manual模式下使用
    lb_range: float = 0.0
    ub_range: float = 100.0
    
    # Config of Alignment对齐设置
    mode_align: AlignmentMode = AlignmentMode.NONE
    str_name_axis_align: Optional[str] = None        # 对齐到哪个轴
    flt_align_src: float = 0.0       # src轴需要和target轴的对齐时, 本轴的对齐值
    flt_align_tgt: float = 0.0       # 对齐target轴, target轴的对齐值
    flt_ratio_scale: float = 1.0     # target轴每变化一个单位, src轴变化的单位数, 用于比例对齐
    
    # 内部状态
    bol_is_prim_axis: bool = False              # 是否为主轴
    viewbox: Optional[object] = None      # PyQtGraph ViewBox
    axisitem: Optional[object] = None    # PyQtGraph AxisItem
