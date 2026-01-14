#!/usr/bin/env python3

import numpy as np

def round_with_precision(arr_val, arr_target, flt_epsilon=1e-4):
    """ 测试向量值与目标值的差绝对值是否小于flt_epsilon, 如为True, 则把loc的值置为目标值, 否则保留arr_val
    """
    arr_diff_val_target = np.abs(arr_val - arr_target)
    bol_smaller_than_epsilon = arr_diff_val_target < flt_epsilon
    arr_val_return = arr_val.copy()
    arr_val_return[bol_smaller_than_epsilon] = arr_target[bol_smaller_than_epsilon]
    return arr_val_return

def ceil_with_precision_and_exceed(arr_val, arr_target, flt_epsilon=1e-4, val_exceed=np.nan):
    """ 测试向量值超过目标值, 且超过值小于flt_epsilon, 如为True, 则把loc的值置为目标值,
    如果当前值超过了target且超过量大于flt_epsilon, 则设置为val_exceed
    否则保留arr_val
    """
    abol_val_more_than_target =  arr_val > arr_target
    abol_residual_in_range = arr_val - arr_target < flt_epsilon
    arr_val_return = arr_val.copy()
    # 大于目标值且误差很小, 则置为目标值
    arr_val_return[abol_val_more_than_target & abol_residual_in_range] = arr_target[abol_val_more_than_target & abol_residual_in_range]
    # 大于目标值且误差很大, 则置为val_exceed
    arr_val_return[abol_val_more_than_target & ~abol_residual_in_range] = val_exceed
    return arr_val_return

def floor_with_precision_and_exceed(arr_val, arr_target, flt_epsilon=1e-4, val_exceed=np.nan):
    """ 测试向量值低于过目标值, 且超过值小于flt_epsilon, 如为True, 则把loc的值置为目标值,
    如果当前值小于了target且超过量大于flt_epsilon, 则设置为val_exceed
    否则保留arr_val
    """
    abol_val_less_than_target =  arr_val < arr_target
    abol_residual_in_range = arr_val - arr_target > -flt_epsilon
    arr_val_return = arr_val.copy()
    arr_val_return[abol_val_less_than_target & abol_residual_in_range] = arr_target[abol_val_less_than_target & abol_residual_in_range]
    arr_val_return[abol_val_less_than_target & ~abol_residual_in_range] = val_exceed
    return arr_val_return