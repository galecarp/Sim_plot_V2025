#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

import copy
from typing import List, Dict, Any, Union
import numpy as np
import pandas as pd

""" 通用的DataFrame处理方法
"""

@staticmethod
def _update_df_missing_col_from_other_dict(
    df_update_to:pd.DataFrame=None,
    index_update_to:Union[pd.Index, List[Any]]=None,
    dic_name_col_fillna:Dict[str, Any]=None,
    bol_ignore_missing_key_in_dic_from:bool=True,
):
    """输入index, 比较series和from字典的key, 把series中的缺失的col, 从from字典中补充进来

    Args
    ----
    df_update_to : pd.DataFrame
        要更新的DataFrame
    index_update_to : pd.Index
        要更新的DataFrame的index
    dic_name_col_fillna : Dict[str, Any]
        用于补充列名缺失值的字典, {列名 : 默认fillna值}
    bol_ignore_missing_key_in_dic_from : bool
        是否忽略from字典中的缺失key, 如果为False时, 如果to字典含有 from字典中没有的key, 则会报错
    """
    if index_update_to is not None:
        # 检查index的类型
        if not isinstance(index_update_to, pd.Index) or isinstance(index_update_to, list):
            index_update_to = pd.Index(index_update_to)
        # 检查index是否在df中
        if not index_update_to.isin(df_update_to.index).all():
            raise ValueError("index_update_to中有部分索引不在df_update_to的索引中, 不存在的索引有: {}".format(
                index_update_to[~index_update_to.isin(df_update_to.index)])
            )
        df_update_to_sliced = df_update_to.loc[index_update_to]
    else:
        index_update_to = df_update_to.index
        df_update_to_sliced = df_update_to
    # 计算列名的差集
    set_name_col_difference = set(df_update_to_sliced.columns) ^ set(dic_name_col_fillna.keys())
    # 分析所有的key
    for str_name_col_diff in set_name_col_difference:
        if str_name_col_diff in df_update_to_sliced:
            # 如果to字典中有from字典没有的key
            if bol_ignore_missing_key_in_dic_from:
                continue
            else:
                raise ValueError(f"列名 {str_name_col_diff} 在 df_update_to中, 但不在 dic_name_col_fillna中")
        else:
            # 补充列
            val_fillna = dic_name_col_fillna[str_name_col_diff]
            # 创建新的列
            if str_name_col_diff not in df_update_to.columns:
                df_update_to[str_name_col_diff] = val_fillna
            # 填充缺失值
            df_update_to.loc[index_update_to, str_name_col_diff] = dic_name_col_fillna[str_name_col_diff]
    return df_update_to

@staticmethod
def _create_empty_df(
    index:Union[pd.Index, List[str]]=None,
    columns:List[str]=None,
    len_index=None,
    len_columns=None,
    val_fill_default=np.nan,
    dtype_val_default=np.float64,
    **kwargs
):
    """ 创造空的DataFrame
    """
    # 分辨index输入
    if index is None and len_index is None:
        raise ValueError("错误: 未输入index的列表或长度")
    elif len_index is not None and not isinstance(len_index, int):
        raise ValueError("错误: len_index必须为整数, 输入的类型为: {}".format(type(len_index)))
    elif columns is not None and not isinstance(columns, list):
        raise ValueError("错误: columns必须为列表, 输入的类型为: {}".format(type(columns)))
    if index is not None:
        len_index = len(index)
    # 分辨columns 输入
    if columns is None and len_columns is None:
        raise ValueError("错误: 未输入columns的列表或长度")
    elif len_columns is not None and not isinstance(len_columns, int):
        raise ValueError("错误: len_columns必须为整数, 输入的类型为: {}".format(type(len_columns)))
    elif columns is not None and not isinstance(columns, list):
        raise ValueError("错误: columns必须为列表, 输入的类型为: {}".format(type(columns)))
    if columns is not None:
        len_columns = len(columns)
    # 建立numpy向量
    arr_new = np.empty(
        (len_index, len_columns),
        dtype=dtype_val_default)
    arr_new[:] = val_fill_default
    # 建立df
    df_new = pd.DataFrame(
        arr_new,
        index=index,
        columns=columns)
    return df_new

@staticmethod
def _update_columns_inplace(
    df_data: pd.DataFrame,
    lst_columns_new: List[str],
    val_fill_default: Any = pd.NA,
):
    """更新df的列, inplace操作"""
    # 检查df_data的columns是否有重复值
    if len(df_data.columns) != len(set(df_data.columns)):
        raise ValueError("输入的df_data的columns中有重复值, 请检查")
    # 检查columns中是否有重复值
    if len(lst_columns_new) != len(set(lst_columns_new)):
        raise ValueError("输入的lst_columns_new中有重复值, 请检查")
    # 扩展结构以包含新的列
    columns_all = df_data.columns.union(lst_columns_new)
    # columns索引差值
    set_name_col_difference = set(columns_all) - set(df_data.columns)
    for str_name_col_diff in set_name_col_difference:
        df_data[str_name_col_diff] = val_fill_default
    return df_data

@staticmethod
def _update_index_inplace(
    df_data: pd.DataFrame,
    index_new: List[str],
    val_fill_default: Any = pd.NA,
    bol_sort_index: bool = True,
    dtype_empty: Any = 'float64'
):
    """更新df的行, inplace操作"""
    # 检查df_data的index是否有重复值
    if len(df_data.index) != len(set(df_data.index)):
        raise ValueError("输入的df_data的index中有重复值, 请检查")
    # 检查index中是否有重复值
    if len(index_new) != len(set(index_new)):
        raise ValueError("输入的lst_index_new中有重复值, 请检查")
    # 扩展结构以包含新的列
    index_all = df_data.index.union(index_new)
    # index索引差值
    set_index_difference = set(index_all) - set(df_data.index)
    for str_index_diff in set_index_difference:
        df_data.loc[str_index_diff] = pd.Series(dtype=dtype_empty)
        df_data.loc[str_index_diff] = val_fill_default
    if bol_sort_index:
        df_data.sort_index(inplace=True)
    return df_data

@staticmethod
def _update_dtype_df_from_df(
    df_data_to: pd.DataFrame,
    df_data_from: pd.DataFrame,
    bol_raise_error: bool = True,
):
    """
    """
    for str_col in df_data_from.columns:
        if str_col in df_data_to.columns:
            dtype_from = df_data_from[str_col].dtype
            dtype_to = df_data_to[str_col].dtype
            if dtype_from != dtype_to:
                try:
                    df_data_to[str_col] = df_data_to[str_col].astype(dtype_from)
                except Exception as e:
                    if bol_raise_error:
                        raise ValueError(f"错误: 无法将列 {str_col} 从 dtype {dtype_to} 转换为 dtype {dtype_from}: {e}")
    return df_data_to

@staticmethod
def _update_df_from_df(
    df_data_to: pd.DataFrame,
    df_data_from: pd.DataFrame,
    val_fill_default: Any = pd.NA,
    bol_sort_index: bool = True,
):
    """提取df_data_from中的数据, 更新到df_data_to中"""
    # 扩展结构以包含新的行和列
    index_all = df_data_to.index.union(df_data_from.index)
    columns_all = df_data_to.columns.union(df_data_from.columns)
    
    # inplace 重新索引
    df_data_to = _update_columns_inplace(
        df_data=df_data_to,
        lst_columns_new=columns_all,
        val_fill_default=val_fill_default,
    )
    df_data_to = _update_index_inplace(
        df_data=df_data_to,
        index_new=index_all,
        val_fill_default=val_fill_default,
        bol_sort_index=bol_sort_index
    )

    # inplace 更新值
    df_data_to.update(df_data_from)

    # 更新column的dtype
    if bol_sort_index:
        df_data_to.sort_index(inplace=True)
    return df_data_to

@staticmethod
def _update_df_from_series(
    df_data_to: pd.DataFrame,
    series_data_from: pd.Series,
    index_series: pd.Index = None,
    val_fill_default:Any = pd.NA,
    bol_sort_index: bool = True,
):
    """提取series中的数据, 更新到df中"""
    # 确定目标行索引
    if index_series is None:
        index_series = series_data_from.name
    else:
        series_data_from.name = index_series
    # 扩展结构以包含新的行和列
    index_all = df_data_to.index.union([index_series])
    columns_all = df_data_to.columns.union(series_data_from.index)
    df_data_to = _update_index_inplace(
        df_data=df_data_to,
        index_new=[index_series],
        val_fill_default=val_fill_default,
        bol_sort_index=bol_sort_index
    )
    df_data_to = _update_columns_inplace(
        df_data=df_data_to,
        lst_columns_new=series_data_from.index.tolist(),
        val_fill_default=val_fill_default,
    )
    
    # 直接设置值（pandas会自动创建新行如果不存在）
    df_data_to.loc[index_series, series_data_from.index] = series_data_from.values
    if bol_sort_index:
        df_data_to.sort_index(inplace=True)
    return df_data_to

# 定义可以被 * 导入的内容
__all__ = [
    '_update_df_missing_col_from_other_dict',
    '_create_empty_df',
    '_update_df_from_df',
    '_update_df_from_series'

]
