#!/usr/bin/env python3

from typing import Optional
from dataclasses import dataclass, field
from PySide6.QtGui import QColor


@dataclass
class CurveConfig:
    """曲线配置"""
    str_name_curve: str                       # 曲线名称（实际列名）
    idx_subplot: int                         # 所属子图索引
    str_name_axis: str = 'main'                 # 所属Y轴ID
    
    # 显示设置
    bol_show: bool = True
    color: QColor = field(default_factory=lambda: QColor(255, 0, 0))
    linestyle: str = 'solid'             # 'solid', 'dash', 'dot', 'dashdot'
    linewidth: int = 2
    bol_is_step: bool = False
    
    # 内部引用
    curveitem: Optional[object] = None   # PyQtGraph PlotCurveItem
    symbolitem: Optional[object] = None  # PyQtGraph ScatterPlotItem
