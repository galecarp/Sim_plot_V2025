#!/usr/bin/env python3

from typing import Tuple, Union, Optional
import polars as pl
from datetime import datetime, timedelta

@staticmethod
def get_timestamp_min_max(
    lf : pl.LazyFrame,
    str_name_col_timestamp: str,
    bol_return_hour : bool = False
) -> Tuple[datetime, datetime, Union[timedelta, float]]:
    """ 获取时间戳列的最小值和最大值, 以及时间范围
    Args:
        lf: 包含时间戳列的LazyFrame
        str_name_col_timestamp: 时间戳列的名称
        bol_return_hour: 是否以小时为单位返回时间范围, 默认False返回timedelta对象, 否则返回小时数(float)
    """
    tpl_ts_timestamp_min_max = (
        lf
        .select([
            pl.col(str_name_col_timestamp).min().alias('min'),
            pl.col(str_name_col_timestamp).max().alias('max')
        ])
        .collect()
    )
    # 提取最小和最大时间戳
    ts_timestamp_data_min : datetime = tpl_ts_timestamp_min_max['min'][0]
    ts_timestamp_data_max : datetime = tpl_ts_timestamp_min_max['max'][0]
    # 计算时间范围
    td_timedelta_data : timedelta = ts_timestamp_data_max - ts_timestamp_data_min
    range_time_data = td_timedelta_data
    if bol_return_hour:
        range_time_data = convert_timedelta_to_hour(td_timedelta_data)
    return ts_timestamp_data_min, ts_timestamp_data_max, range_time_data

@staticmethod
def convert_timedelta_to_hour(
    td: timedelta
) -> float:
    """ 将timedelta对象转换为小时数
    Args:
        td: timedelta对象
    Returns:
        float: 小时数
    """
    return td.total_seconds() / 3600.0

