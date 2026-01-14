#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

import copy
from typing import List, Dict, Any, Union
import numpy as np
import pandas as pd

""" 通用的字典处理方法
"""

@staticmethod
def _get_param_from_dict(
    dic_from:pd.DataFrame,
    str_name_param:str,
    bol_must_have:bool=True):
    """通用读取参数的方法, 读取对应的设置

    读取优先级为: 函数的输入, dic_const中定义的输入

    Args
    ----
    dic_from : dict
        要读取的字典
    str_name_param : str
        要提取参数的名字
    bol_must_have : boolean
        输入dic_const中, 找不到此参数时是否报错
    """
    val_param = None
    if \
        (not bol_must_have and str_name_param in dic_from)\
        or bol_must_have:
        val_param = dic_from[str_name_param]
    return val_param

@staticmethod
def _get_param_with_forced(
    dic_from:pd.DataFrame,
    str_name_param_in_config:str=None,
    val_param:Any=None,
    bol_must_have:bool=True):
    """通用读取方法, 当传入的参数为None时, 从config读取对应的参数值"""
    if val_param is None:
        if bol_must_have:
            val_param = dic_from[str_name_param_in_config]
        else:
            val_param = dic_from.get(str_name_param_in_config, None)
    return val_param

@staticmethod
def _update_key_from_other_dict(
    dic_update_to=None,
    dic_update_from=None,
    bol_create_new_key=False,
    bol_ignore_new_key=True,
    bol_replace_dict=False,
    **kwargs
):
    """把dic_update_from中的key-value更新到dic_update_to中"""
    # 复制来源字典
    dic_update_from = copy.deepcopy(dic_update_from)
    if bol_replace_dict:
        # 直接替换
        dic_update_to.clear()
        dic_update_to.update(dic_update_from)
    else:
        if dic_update_from is not None:
            for key_from, val_from in dic_update_from.items():
                if not bol_create_new_key and key_from not in dic_update_to:
                    if not bol_ignore_new_key:
                        raise ValueError(
                            f'输出字典中有要更新字典中不带有的新key, 输入key为{key_from}\n'+
                            '但设置bol_create_new_key为False, 不允许创建新的key\n' +
                            '目标字典为: {}'.format(dic_update_to)
                        )
                    else:
                        continue
                else:
                    # 更新已有的key
                    dic_update_to.update({key_from : val_from})
    return

@staticmethod
def _get_patched_config_with_default(
    dic_config_default:pd.DataFrame,
    **kwargs
):
    """ 从kwargs中读取参数, 并与dic_config_default中的默认值进行替换合并
    即: 如果kwargs中有对应的key, 则使用kwargs中的值, 否则使用dic_config_default中的值
    """
    dic_config_result = copy.deepcopy(dic_config_default)
    kwargs = copy.deepcopy(kwargs)
    for str_key in kwargs.keys():
        if str_key not in dic_config_default:
            continue
        else:
            # 读取参数, 并替换
            dic_config_result[str_key] = kwargs[str_key]
    return dic_config_result

@staticmethod
def _update_missing_key_from_other_dict(
    dic_update_to:Dict[str, Any]=None,
    dic_update_from:Dict[str, Any]=None,
    bol_ignore_missing_key_in_dic_from:bool=True,
    bol_deepcopy:bool=True,
):
    """比较to字典和from字典的key, 把to字典中的缺失的key, 从from字典中补充进来

    Args
    ----
    bol_ignore_missing_key_in_dic_from : bool
        是否忽略from字典中的缺失key, 如果为False时, 如果to字典含有 from字典中没有的key, 则会报错
    bol_deepcopy : bool
        是否在补充缺失值时, 对from字典中的值进行深拷贝, 默认为True

    """
    # 计算差集
    set_items_difference = set(dic_update_to.keys()) ^ set(dic_update_from.keys())
    # 分析所有的key
    for str_key_diff in set_items_difference:
        if str_key_diff in dic_update_to:
            # 如果to字典中有from字典没有的key
            if bol_ignore_missing_key_in_dic_from:
                continue
            else:
                raise ValueError(f"key {str_key_diff} 在 dic_update_to字典中存在, 但在 dic_update_from字典中不存在")
        else:
            # 差别的key, 从from字典中补充到to字典
            if bol_deepcopy:
                dic_update_to[str_key_diff] = copy.deepcopy(dic_update_from[str_key_diff])
            else:
                dic_update_to[str_key_diff] = dic_update_from[str_key_diff]
    return dic_update_to

@staticmethod
def _save_in_nested_dict(
    dic_to_access:Dict[str, Any],
    lst_key_hierarch:List[str]=None,
    str_key_save:str=None,
    val_key_save:Any=None,
    bol_create_nested:bool=False,
) -> Dict[str, Any]:
    """访问嵌套字典中的值, 

    Args
    ----
    dic_to_access : Dict[str, Any]
        要访问的字典
    lst_key_hierarch : List[str]
        要访问的key列表, 按照层级顺序排列
    str_key_save : str
        要保存的key
    val_key_save : Any
        要保存的值
    bol_create_nested : bool
        如果访问的层级key不存在时, 是否创建对应的key, 并赋值为空字典
    """
    if lst_key_hierarch is None:
        lst_key_hierarch = []
    # 逐级访问
    dic_to_access_cur = dic_to_access
    for str_key_level in lst_key_hierarch:
        # 检查当前层级key是否存在
        if str_key_level not in dic_to_access_cur:
            if bol_create_nested:
                dic_to_access_cur[str_key_level] = {}
            else:
                raise KeyError(f"在访问字典时, 层级key '{str_key_level}' 不存在, 请检查输入的层级key列表")
        # 跳转层级
        dic_to_access_cur = dic_to_access_cur[str_key_level]
    # 保存值
    if str_key_save is not None:
        dic_to_access_cur[str_key_save] = val_key_save
    return dic_to_access

# 定义可以被 * 导入的内容
__all__ = [
    '_get_param_from_dict',
    '_get_param_with_forced',
    '_update_key_from_other_dict',
    '_get_patched_config_with_default',
    '_update_missing_key_from_other_dict',
    '_save_in_nested_dict'
]
