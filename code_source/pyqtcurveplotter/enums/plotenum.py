#!/usr/bin/env python3

from enum import Enum

class SideAxis(Enum):
    """轴侧枚举
    """
    LEFT = "left"
    RIGHT = "right"

class IdxItemGridLayout(Enum):
    """ 网格布局枚举, 由PYQTGRAPH的QGraphicsGridLayout支持
    """
    LEFTAXIS = 0
    PLOTITEM = 1
    RIGHTAXIS = 2
    
    # 更多右侧轴
    for idx_axis in range(3, 10):
        vars()[f'RIGHTAXIS{idx_axis-2}'] = idx_axis

    