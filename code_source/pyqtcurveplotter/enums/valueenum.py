#!/usr/bin/env python3

from enum import Enum

class UnitValue(Enum):
    """ 值的单位枚举
    """
    # 质量
    TON = "ton"
    KG = "kg"
    # 质量流量
    TON_PER_H = "ton/h"
    KG_PER_H = "kg/h"
    # 能量 h
    MWH = "MWh"
    KWH = "kWh"
    # 功率 P
    MW = "MW"
    KW = "kW"
    # 温度
    CELSIUS = "°C"
    KELVIN = "K"
    # 百分比
    PERCENT = "%"
