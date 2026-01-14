#!/usr/bin/env python3

from enum import Enum

class AlignmentMode(Enum):
    """对齐模式枚举"""
    NONE = "none"
    ZERO = "zero"
    VALUE = "value"
    VALUESCALE = "valuescale"


class RangeMode(Enum):
    """范围模式枚举"""
    AUTO = "auto"
    MANUAL = "manual"


class SideAxis(Enum):
    """轴侧枚举"""
    LEFT = "left"
    RIGHT = "right"
