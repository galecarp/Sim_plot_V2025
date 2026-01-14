#!/usr/bin/env python3

from sklearn.base import BaseEstimator, TransformerMixin

import pandas as pd
import numpy as np

import copy

import re

from code_source.preprocessing.preprocessing_GTG.generalgtgtransformer import GeneralGTGTransformer

class SplitPowerGTGTransformer(BaseEstimator, TransformerMixin, GeneralGTGTransformer):
    """把原始GTG的GT数据的功率与能量数据, 生成一些额外的功率能量数据, 方便之后使用

    *功能:
        * 1.对于每一个时间片, 生成燃机输出电功率
            * 时间片开始时间的 GT电功率: 'flt_power_{GTG,GT,elec-output,start,slice}',
            * 时间片结束时间的 GT电功率: 'flt_power_{GTG,GT,elec-output,end,slice}',
        * 2.对于每一个时间片, 生成燃机空转燃料功率浪费
            * 时间片开始时间的 GT燃料浪费功率: 'flt_power_{GTG,GT,waste-consume,start,slice}',
            * 时间片结束时间的 GT燃料功率: 'flt_power_{GTG,GT,waste-consume,end,slice}',
        * 3.对于每一个时间片, 生成燃机所在的运行模式mode下, 燃机空转下的下限功率和上限功率
            * 燃机空转下的上限功率: 'flt_power_{GTG,GT,waste-consume,UB,slice}',
            * 燃机空转下的下限功率: 'flt_power_{GTG,GT,waste-consume,LB,slice}',
        * 4.对一每一个timeblock, 生成燃机在该timeblock内的总能量
            * 燃机在timeblock内的总输出电能: 'flt_Energy_{GTG,GT,elec-output,timeblock}',
            * 燃机在timeblock内的总空转浪费燃料能量: 'flt_Energy_{GTG,GT,waste-consume,timeblock}',

    """
    def __init__(self,
        dic_config=None,
        dic_config_all_variables_2D_nan=None,
        dic_config_map_name_variables=None,
        **kwargs
    ) -> None:
        super().__init__(
            dic_config=dic_config,
            dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            dic_config_map_name_variables=dic_config_map_name_variables,
            **kwargs)
        self._init_dic_config(dic_config)
        pass

    def _init_dic_config(self, dic_config=None, **kwargs):
        super()._init_dic_config(dic_config=dic_config, **kwargs)
        dic_config_default = {
            'flt_timeinterval_timeblock_max': 0.25,
            'flt_power_GTG_nominal' : 700 * 0.2,
            'flt_energy_difference_allowed' : 0.1,
            'str_key_map_power_GT_waste_LB_slice' : 'flt_power_waste_LB',
            'str_key_map_power_GT_waste_UB_slice' : 'flt_power_waste_UB',
            'dic_map_state_to_power_waste' : {
                # 把燃机的运行模式序号 映射到 燃机空转时的功率浪费
                # 按目前的程序定死, (无关燃机额定功率的设计)燃机空转消耗, 峰值为 0.046kg/h 的氢流量
                # 0.046 kg/s * 33.33 kWh/kg * 3600s/h * 1MWh/1000kWh  =  MWh/h
                # 单位 MWh / h = MW
                0 : {
                    'flt_power_waste_LB' : 0,
                    'flt_power_waste_UB' : 0,
                },
                1 : {
                    'flt_power_waste_LB' : 0,
                    'flt_power_waste_UB' : 0.046*33.33*3.6,
                },
                2 : {
                    'flt_power_waste_LB' : 0.046*33.33*3.6,
                    'flt_power_waste_UB' : 0.046*33.33*3.6,
                }
            },
        }
        # 替换默认配置
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config_default,
            bol_create_new_key=False,
            bol_replace_dict=True,
        )
        # 更新用户输入的配置
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config,
            bol_create_new_key=False,
            bol_replace_dict=False,
        )
        pass

    # 计算燃机线性爬坡的函数
    def _cal_values_Trapezoid_with_percent(self,
        val_LB, val_UB, percent_last, percent_this
            
    ):
        """ 计算梯形启动结束时的数值大小, 考虑时间启动和终的百分比, 对应最左端LB和最右端UB的数值
        * 功率 和 时间 形成一个梯形
        * 为梯形是因为燃机在同一模式mode的上下爬坡速度为线性

        Args
        ----
        val_LB: 燃机所在模式mode的底部功率值, LB: Lower Bound
        val_UB: 燃机所在模式mode的顶部功率值, UB: Upper Bound
        percent_last: 上一个时间片slice的所在高度的百分比
        percent_this: 本时间片slice的所在高度的百分比
        """
        val_last_slice = val_LB * (1-percent_last) + val_UB * percent_last
        val_this_slice = val_LB * (1-percent_this) + val_UB * percent_this
        return val_last_slice, val_this_slice

    def _cal_area_Trapezoid_with_percent(self,
        val_LB, val_UB, percent_last, percent_this,
        flt_timeinterval_op_slice,
    ):
        """ 计算梯形启动结束之间的梯形面积大小, 考虑时间启动和终的百分比, 对应最左端LB和最右端UB的数值
        * 功率 和 时间 形成一个梯形
        * 为梯形是因为燃机在同一模式mode的上下爬坡速度为线性
        * 计算出来的面积是normalized, 
            * 即假设LB->UB总时间为1为基础的, 故最后面积需要乘以对应时间间隔, 才是真正的能量
            * 注意: 对应的时间间隔, 在爬坡和下坡的时间间隔是不一样的, 此值由上层函数传入

        Args
        ----
        val_LB : float
            燃机所在模式mode的底部功率值, LB: Lower Bound
        val_UB : float
            燃机所在模式mode的顶部功率值, UB: Upper Bound
        percent_last : float
            上一个时间片slice的所在高度的百分比
        percent_this : float
            本时间片slice的所在高度的百分比
        flt_timeinterval_op_slice : float
            本时间片slice的时间间隔
        """
        area = -0.5 * val_LB * (percent_last + percent_this) +\
            val_LB +\
            0.5 * val_UB * (percent_last + percent_this)
        area *= flt_timeinterval_op_slice
        return area

    def _check_GTG_energy_log_with_integral(self,
        bol_is_GTG_elec_or_waste,
        arr_energy_GT_integral_slice,
        arr_energy_GT_recorded_slice,
        arr_ts_timestamp_GTG_slice,
        flt_energy_difference_allowed=None,
        dic_text_energy_elec_output_or_waste={
            False : 'GT空转浪费能量',
            True : 'GT输出电能量'
        },
        **kwargs
    ):
        """ 验证功率和能量计算结果是否耦合, 即功率在时间上的积分是否等于能量

        Args
        ----
        bol_is_GTG_elec_or_waste : bool
            调用此模块的上层函数是在计算电输出还是浪费燃料, 电输出为True, 浪费燃料为False
        arr_index_bol_GT: np.array
            用于选择GTG数据的bool索引, 选择GTG数据中的GT输出电能量的时间片
        arr_energy_GT_integral_slice : np.array
            积分计算出来的能量
        arr_energy_GT_recorded_slice: np.array
            数据log中得到的能量
        arr_ts_timestamp_GTG_slice : np.array
            时间片的时间戳
        flt_energy_difference_allowed: float
            允许的能量误差范围, 由全局dic_config传入
        """

        arr_flt_energy_difference = np.abs(
            arr_energy_GT_integral_slice - arr_energy_GT_recorded_slice)
        if arr_flt_energy_difference.max() > flt_energy_difference_allowed:
            # 超越了允许的误差范围
            arr_index_difference_exceed = np.where(arr_flt_energy_difference>flt_energy_difference_allowed)
            arr_ts_timestamp_difference_exceed = arr_ts_timestamp_GTG_slice[arr_index_difference_exceed]
            str_text_energy_elec_output_or_waste = dic_text_energy_elec_output_or_waste.get(bol_is_GTG_elec_or_waste)
            df_show_error = pd.DataFrame(
                data=np.stack([
                    arr_energy_GT_integral_slice,
                    arr_energy_GT_recorded_slice
                ], axis=1),
                columns=[
                    'slice通过时间积分计算的{str_text_energy_elec_output_or_waste}',
                    'slice原始log数据的记录能量值'],
                index=arr_ts_timestamp_difference_exceed,
            )
            df_show_error = df_show_error.index.rename('slice的起始时间戳', inplace=True)
            raise ValueError(
                f'按功率在slice时间上积分计算的{str_text_energy_elec_output_or_waste} 和 原始log数据的记录能量值不一致\n'+\
                f'{df_show_error}')
        return

    def _get_power_LB_and_UB_GT(self,
        df_GTG,
        bol_is_GTG_elec_or_waste,
        arr_index_bol_GT,
        flt_power_GTG_nominal=None,
        str_key_map_power_GT_waste_LB_slice=None,
        str_key_map_power_GT_waste_UB_slice=None,
        dic_map_state_to_power_waste=None,
        str_key_flt_power_LB_normalized_slice=None,
        str_key_flt_power_UB_normalized_slice=None,
        str_key_int_indexmode_GTG_slice=None,
        **kwargs
    ):
        """得到燃机所在mode的 功率下限LB和 功率上限UB

        * 分为 电输出 和 浪费燃料 两种情况, 按照bol_is_GTG_elec_or_waste的值选择
        """
        if bol_is_GTG_elec_or_waste:
            # 1. 电输出功率的情况
            arr_flt_power_GT_LB_slice = \
                df_GTG.loc[arr_index_bol_GT, str_key_flt_power_LB_normalized_slice].values * flt_power_GTG_nominal
            arr_flt_power_GT_UB_slice = \
                df_GTG.loc[arr_index_bol_GT, str_key_flt_power_UB_normalized_slice].values * flt_power_GTG_nominal
        else:
            # 2. 浪费燃料的情况
            func_1d_LB = np.vectorize(
                lambda x : np.float64(dic_map_state_to_power_waste.get(int(x)).get(str_key_map_power_GT_waste_LB_slice)))
            func_1d_UB = np.vectorize(
                lambda x : np.float64(dic_map_state_to_power_waste.get(int(x)).get(str_key_map_power_GT_waste_UB_slice)))
            arr_flt_power_GT_LB_slice = func_1d_LB(
                df_GTG.loc[arr_index_bol_GT, str_key_int_indexmode_GTG_slice].values)
            arr_flt_power_GT_UB_slice = func_1d_UB(
                df_GTG.loc[arr_index_bol_GT, str_key_int_indexmode_GTG_slice].values)
        return arr_flt_power_GT_LB_slice, arr_flt_power_GT_UB_slice

    def _update_dataframe(self,
        df_GTG,
        arr_index_bol_GT,
        dic_update_content=None,
        **kwargs
    ):
        """更新dataframe的数据, 生成新的列

        Args
        ----
        df_GTG: pd.DataFrame
            输入的GTG数据
        arr_index_bol_GT: np.array
            用于选择GTG数据的bool索引, 更变只在选择的GTG数据中进行
        dic_update_content: dict
            更新的内容, key是列名, value是列的内容
        """
        for str_name_col, val_col in dic_update_content.items():
            if str_name_col not in df_GTG.columns:
                # 如果列名不存在, 则创建新的列
                df_GTG[str_name_col] = None
            df_GTG.loc[arr_index_bol_GT, str_name_col] = val_col
        return
    
    def _update_dataframe_with_power_energy_GTG(self,
        df_GTG,
        bol_is_GTG_elec_or_waste,
        arr_index_bol_GT,
        arr_flt_power_GT_LB_slice,
        arr_flt_power_GT_UB_slice,
        arr_power_GT_start_slice,
        arr_power_GT_end_slice,
        arr_energy_GT_slice,
        str_key_flt_power_GT_elec_output_LB_slice=None,
        str_key_flt_power_GT_elec_output_UB_slice=None,
        str_key_flt_power_GT_waste_LB_slice=None,
        str_key_flt_power_GT_waste_UB_slice=None,
        str_key_flt_power_GT_elec_output_start_slice=None,
        str_key_flt_power_GT_elec_output_end_slice=None,
        str_key_flt_power_GT_waste_start_slice=None,
        str_key_flt_power_GT_waste_end_slice=None,
        str_key_flt_energy_GT_elec_output_slice=None,
        str_key_flt_energy_GT_waste_slice=None,
        **kwargs
    ):
        """ 更新dataframe的数据, 生成新的列, 用于GTG的功率和能量数据
        * 分为
            * 燃机空转浪费 功率 起始, 结束 以及 整个slice的积分能量
            * 燃机电能输出 功率 起始, 结束 以及 整个slice的积分能量
        """

        if bol_is_GTG_elec_or_waste:
            # 1. 电输出功率的情况
            dic_update_content = {
                str_key_flt_power_GT_elec_output_LB_slice : arr_flt_power_GT_LB_slice,
                str_key_flt_power_GT_elec_output_UB_slice : arr_flt_power_GT_UB_slice,
                str_key_flt_power_GT_elec_output_start_slice : arr_power_GT_start_slice,
                str_key_flt_power_GT_elec_output_end_slice : arr_power_GT_end_slice,
                str_key_flt_energy_GT_elec_output_slice : arr_energy_GT_slice
            }
        else:
            # 2. 浪费燃料的情况
            dic_update_content = {
                str_key_flt_power_GT_waste_LB_slice : arr_flt_power_GT_LB_slice,
                str_key_flt_power_GT_waste_UB_slice : arr_flt_power_GT_UB_slice,
                str_key_flt_power_GT_waste_start_slice : arr_power_GT_start_slice,
                str_key_flt_power_GT_waste_end_slice : arr_power_GT_end_slice,
                str_key_flt_energy_GT_waste_slice : arr_energy_GT_slice
            }
        # 更新数据
        self._update_dataframe(
            df_GTG=df_GTG,
            arr_index_bol_GT=arr_index_bol_GT,
            dic_update_content=dic_update_content,
        )
        return
    
    def _calculate_energy_integral_GTG_slice(self,
        arr_flt_power_GT_LB_slice,
        arr_flt_power_GT_UB_slice,
        arr_flt_percent_ramp_height_last_slice,
        arr_flt_percent_ramp_height_this_slice,                         
        arr_flt_timeinterval_op_slice,          
        **kwargs
    ):
        """ 按照 计算燃机当前模式下, H2燃料分别的 切片的能量积分值
        """       
        # 计算切片的能量积分值向量
        arr_energy_GT_slice = self._cal_area_Trapezoid_with_percent(
            arr_flt_power_GT_LB_slice, arr_flt_power_GT_UB_slice,
            arr_flt_percent_ramp_height_last_slice, arr_flt_percent_ramp_height_this_slice,
            arr_flt_timeinterval_op_slice,
        )
        return arr_energy_GT_slice


    def _calculate_power_energy_GT_slice(self,
        df_GTG,
        bol_is_GTG_elec_or_waste,
        arr_index_bol_GT,
        **kwargs
    ):
        """ 计算输入dataframe的 燃机空转浪费功率/燃机电能输出 起始, 结束 以及 整个slice的积分能量
        * 注意, 在为燃机空转浪费功率时, 因为H2与NH3浪费能量数值差不多, 所以统一使用H2作为数值来源

        Args
        ----
        df_GTG: pd.DataFrame
            输入的GTG数据
        bol_is_GTG_elec_or_waste : bool
            选择是电输出还是浪费燃料, 电输出为True, 浪费燃料为False
        arr_index_bol_GT: np.array
            用于选择GTG数据的bool索引, 选择GTG数据中的 燃机空转浪费功率/燃机电能输出 的时间片
        
        """
        
        # 提取时间片的百分比
        str_key_flt_percent_ramp_height_last_slice = kwargs.get('str_key_flt_percent_ramp_height_last_slice')
        str_key_flt_percent_ramp_height_this_slice = kwargs.get('str_key_flt_percent_ramp_height_this_slice')
        arr_flt_percent_ramp_height_last_slice = df_GTG.loc[
            arr_index_bol_GT, str_key_flt_percent_ramp_height_last_slice].values
        arr_flt_percent_ramp_height_this_slice = df_GTG.loc[
            arr_index_bol_GT, str_key_flt_percent_ramp_height_this_slice].values
        # 计算燃机当前运行模式mode下, 底部浪费功率值 和 顶部功率值
        arr_flt_power_GT_LB_slice, arr_flt_power_GT_UB_slice =\
            self._get_power_LB_and_UB_GT(
                df_GTG=df_GTG,
                bol_is_GTG_elec_or_waste=bol_is_GTG_elec_or_waste,
                arr_index_bol_GT=arr_index_bol_GT,
                **kwargs
            )

        # 计算燃机当前模式下, H2燃料分别的 切片起始时间的功率值 和 切片结束时间的功率值
        arr_power_GT_start_slice, arr_power_GT_end_slice = self._cal_values_Trapezoid_with_percent(
            arr_flt_power_GT_LB_slice, arr_flt_power_GT_UB_slice,
            arr_flt_percent_ramp_height_last_slice, arr_flt_percent_ramp_height_this_slice
        )
        # 计算燃机当前模式下, H2燃料分别的 切片的能量积分值
        str_key_flt_timeinterval_op_slice = kwargs.get('str_key_flt_timeinterval_op_slice')
        arr_flt_timeinterval_op_slice = df_GTG.loc[
            arr_index_bol_GT, str_key_flt_timeinterval_op_slice].values
        arr_energy_GT_integral_slice = self._calculate_energy_integral_GTG_slice(
            arr_flt_power_GT_LB_slice=arr_flt_power_GT_LB_slice,
            arr_flt_power_GT_UB_slice=arr_flt_power_GT_UB_slice,
            arr_flt_percent_ramp_height_last_slice=arr_flt_percent_ramp_height_last_slice,
            arr_flt_percent_ramp_height_this_slice=arr_flt_percent_ramp_height_this_slice,                    
            arr_flt_timeinterval_op_slice=arr_flt_timeinterval_op_slice,      
        )

        # 验证功率和能量计算结果是否耦合, 即功率在时间上的积分是否等于能量
        str_key_ts_timestamp_GTG_slice = kwargs.get('str_key_ts_timestamp_GTG_slice')
        str_key_flt_energy_GTG_elec_or_waste_slice = kwargs.get('str_key_flt_energy_GTG_elec_or_waste_slice')
        arr_ts_timestamp_GTG_slice = df_GTG.loc[
            arr_index_bol_GT, str_key_ts_timestamp_GTG_slice].values
        arr_energy_GT_recorded_slice = df_GTG.loc[
            arr_index_bol_GT, str_key_flt_energy_GTG_elec_or_waste_slice].values
        self._check_GTG_energy_log_with_integral(
            bol_is_GTG_elec_or_waste=bol_is_GTG_elec_or_waste,
            arr_energy_GT_integral_slice=arr_energy_GT_integral_slice,
            arr_energy_GT_recorded_slice=arr_energy_GT_recorded_slice,
            arr_ts_timestamp_GTG_slice=arr_ts_timestamp_GTG_slice,
            **kwargs
        )
        
        # 存储waste功率计算结果进入新的列
        self._update_dataframe_with_power_energy_GTG(
            df_GTG=df_GTG,
            bol_is_GTG_elec_or_waste=bol_is_GTG_elec_or_waste,
            arr_index_bol_GT=arr_index_bol_GT,
            arr_flt_power_GT_LB_slice=arr_flt_power_GT_LB_slice,
            arr_flt_power_GT_UB_slice=arr_flt_power_GT_UB_slice,
            arr_power_GT_start_slice=arr_power_GT_start_slice,
            arr_power_GT_end_slice=arr_power_GT_end_slice,
            arr_energy_GT_slice=arr_energy_GT_integral_slice,
            **kwargs
        )
        return
    
    def split_power_energy_GTG(self,
        df_GTG,
        flt_power_GTG_nominal=None,
        str_key_map_power_GT_waste_LB_slice=None,
        str_key_map_power_GT_waste_UB_slice=None,
        dic_map_state_to_power_waste=None,
        flt_energy_difference_allowed=None,
        str_key_ts_timestamp_GTG_slice=None,
        str_key_bol_ramp_up_GTG_slice=None,
        str_key_flt_power_GT_elec_output_LB_slice=None,
        str_key_flt_power_GT_elec_output_UB_slice=None,
        str_key_flt_power_GT_waste_LB_slice=None,
        str_key_flt_power_GT_waste_UB_slice=None,
        str_key_flt_power_GT_elec_output_start_slice=None,
        str_key_flt_power_GT_elec_output_end_slice=None,
        str_key_flt_power_GT_waste_start_slice=None,
        str_key_flt_power_GT_waste_end_slice=None,
        str_key_flt_energy_GT_elec_output_slice=None,
        str_key_flt_energy_GT_waste_slice=None,
        str_key_bol_GTG_elec_slice=None,
        str_key_int_indexmode_GTG_slice=None,
        str_key_flt_percent_ramp_height_last_slice=None,
        str_key_flt_percent_ramp_height_this_slice=None,
        str_key_flt_timeinterval_op_slice=None,
        str_key_flt_energy_GTG_elec_or_waste_slice=None,
        str_key_flt_power_LB_normalized_slice=None,
        str_key_flt_power_UB_normalized_slice=None,
        str_key_flt_timeinterval_ramp_up_nominal_slice=None,
        str_key_flt_timeinterval_ramp_down_nominal_slice=None,
        **kwargs
    ):
        """ 把原始数据中的合在一起的GTG的功率与能量数据, 生成一些额外的功率能量数据, 方便之后使用
        问题: 原始数据中, Gt的输出能量的数据 包含 电输出功率 和 空转时废燃料耗能
        """
        # 参数名读取
        str_key_ts_timestamp_GTG_slice = self.get_dic_key(
            'str_key_ts_timestamp_GTG_slice', name_forced=str_key_ts_timestamp_GTG_slice)
        str_key_bol_ramp_up_GTG_slice = self.get_dic_key(
            'str_key_bol_ramp_up_GTG_slice', name_forced=str_key_bol_ramp_up_GTG_slice)
        str_key_flt_power_GT_elec_output_LB_slice = self.get_dic_key(
            'str_key_flt_power_GT_elec_output_LB_slice', name_forced=str_key_flt_power_GT_elec_output_LB_slice)
        str_key_flt_power_GT_elec_output_UB_slice = self.get_dic_key(
            'str_key_flt_power_GT_elec_output_UB_slice', name_forced=str_key_flt_power_GT_elec_output_UB_slice)
        str_key_flt_power_GT_waste_LB_slice = self.get_dic_key(
            'str_key_flt_power_GT_waste_LB_slice', name_forced=str_key_flt_power_GT_waste_LB_slice)
        str_key_flt_power_GT_waste_UB_slice = self.get_dic_key(
            'str_key_flt_power_GT_waste_UB_slice', name_forced=str_key_flt_power_GT_waste_UB_slice)
        str_key_flt_power_GT_elec_output_start_slice = self.get_dic_key(
            'str_key_flt_power_GT_elec_output_start_slice', name_forced=str_key_flt_power_GT_elec_output_start_slice)
        str_key_flt_power_GT_elec_output_end_slice = self.get_dic_key(
            'str_key_flt_power_GT_elec_output_end_slice', name_forced=str_key_flt_power_GT_elec_output_end_slice)
        str_key_flt_power_GT_waste_start_slice = self.get_dic_key(
            'str_key_flt_power_GT_waste_start_slice', name_forced=str_key_flt_power_GT_waste_start_slice)
        str_key_flt_power_GT_waste_end_slice = self.get_dic_key(
            'str_key_flt_power_GT_waste_end_slice', name_forced=str_key_flt_power_GT_waste_end_slice)
        str_key_flt_energy_GT_elec_output_slice = self.get_dic_key(
            'str_key_flt_energy_GT_elec_output_slice', name_forced=str_key_flt_energy_GT_elec_output_slice)
        str_key_flt_energy_GT_waste_slice = self.get_dic_key(
            'str_key_flt_energy_GT_waste_slice', name_forced=str_key_flt_energy_GT_waste_slice)
        str_key_bol_GTG_elec_slice = self.get_dic_key(
            'str_key_bol_GTG_elec_slice', name_forced=str_key_bol_GTG_elec_slice)
        str_key_int_indexmode_GTG_slice = self.get_dic_key(
            'str_key_int_indexmode_GTG_slice', name_forced=str_key_int_indexmode_GTG_slice)
        str_key_flt_percent_ramp_height_last_slice = self.get_dic_key(
            'str_key_flt_percent_ramp_height_last_slice', name_forced=str_key_flt_percent_ramp_height_last_slice) 
        str_key_flt_percent_ramp_height_this_slice = self.get_dic_key(
            'str_key_flt_percent_ramp_height_this_slice', name_forced=str_key_flt_percent_ramp_height_this_slice)
        str_key_flt_timeinterval_op_slice = self.get_dic_key(
            'str_key_flt_timeinterval_op_slice', name_forced=str_key_flt_timeinterval_op_slice)
        str_key_flt_energy_GTG_elec_or_waste_slice = self.get_dic_key(
            'str_key_flt_energy_GTG_elec_or_waste_slice', name_forced=str_key_flt_energy_GTG_elec_or_waste_slice)
        str_key_flt_power_LB_normalized_slice = self.get_dic_key(
            'str_key_flt_power_LB_normalized_slice', name_forced=str_key_flt_power_LB_normalized_slice)
        str_key_flt_power_UB_normalized_slice = self.get_dic_key(
            'str_key_flt_power_UB_normalized_slice', name_forced=str_key_flt_power_UB_normalized_slice)
        str_key_flt_timeinterval_ramp_up_nominal_slice = self.get_dic_key(
            'str_key_flt_timeinterval_ramp_up_nominal_slice', name_forced=str_key_flt_timeinterval_ramp_up_nominal_slice)
        str_key_flt_timeinterval_ramp_down_nominal_slice = self.get_dic_key(
            'str_key_flt_timeinterval_ramp_down_nominal_slice', name_forced=str_key_flt_timeinterval_ramp_down_nominal_slice)

        # config的参数读取
        flt_power_GTG_nominal = self._get_param_with_forced(
            name_param_in_config='flt_power_GTG_nominal', val_param=flt_power_GTG_nominal)
        str_key_map_power_GT_waste_LB_slice = self._get_param_with_forced(
            name_param_in_config='str_key_map_power_GT_waste_LB_slice', val_param=str_key_map_power_GT_waste_LB_slice)
        str_key_map_power_GT_waste_UB_slice = self._get_param_with_forced(
            name_param_in_config='str_key_map_power_GT_waste_UB_slice', val_param=str_key_map_power_GT_waste_UB_slice)
        dic_map_state_to_power_waste = self._get_param_with_forced(
            name_param_in_config='dic_map_state_to_power_waste', val_param=dic_map_state_to_power_waste)
        flt_energy_difference_allowed = self._get_param_with_forced(
            name_param_in_config='flt_energy_difference_allowed', val_param=flt_energy_difference_allowed)

        # 计算燃机输出电功率 与 浪费燃料的时间index
        arr_index_bol_GT_elec_output = df_GTG[str_key_bol_GTG_elec_slice] == 1
        arr_index_bol_GT_waste = df_GTG[str_key_bol_GTG_elec_slice] == 0

        # 参数字典
        dic_params_func = {
            'flt_power_GTG_nominal' : flt_power_GTG_nominal,
            'str_key_map_power_GT_waste_LB_slice' : str_key_map_power_GT_waste_LB_slice,
            'str_key_map_power_GT_waste_UB_slice' : str_key_map_power_GT_waste_UB_slice,
            'dic_map_state_to_power_waste' : dic_map_state_to_power_waste,
            'flt_energy_difference_allowed' : flt_energy_difference_allowed,
            'str_key_ts_timestamp_GTG_slice' : str_key_ts_timestamp_GTG_slice,
            'str_key_bol_ramp_up_GTG_slice' : str_key_bol_ramp_up_GTG_slice,
            'str_key_flt_power_GT_elec_output_LB_slice' : str_key_flt_power_GT_elec_output_LB_slice,
            'str_key_flt_power_GT_elec_output_UB_slice' : str_key_flt_power_GT_elec_output_UB_slice,
            'str_key_flt_power_GT_waste_LB_slice' : str_key_flt_power_GT_waste_LB_slice,
            'str_key_flt_power_GT_waste_UB_slice' : str_key_flt_power_GT_waste_UB_slice,
            'str_key_flt_power_GT_elec_output_start_slice' : str_key_flt_power_GT_elec_output_start_slice,
            'str_key_flt_power_GT_elec_output_end_slice' : str_key_flt_power_GT_elec_output_end_slice,
            'str_key_flt_power_GT_waste_start_slice' : str_key_flt_power_GT_waste_start_slice,
            'str_key_flt_power_GT_waste_end_slice' : str_key_flt_power_GT_waste_end_slice,
            'str_key_flt_energy_GT_elec_output_slice' : str_key_flt_energy_GT_elec_output_slice,
            'str_key_flt_energy_GT_waste_slice' : str_key_flt_energy_GT_waste_slice,
            'str_key_int_indexmode_GTG_slice' : str_key_int_indexmode_GTG_slice,
            'str_key_flt_percent_ramp_height_last_slice' : str_key_flt_percent_ramp_height_last_slice,
            'str_key_flt_percent_ramp_height_this_slice' : str_key_flt_percent_ramp_height_this_slice,
            'str_key_flt_timeinterval_op_slice' : str_key_flt_timeinterval_op_slice,
            'str_key_flt_energy_GTG_elec_or_waste_slice' : str_key_flt_energy_GTG_elec_or_waste_slice,
            'str_key_flt_power_LB_normalized_slice' : str_key_flt_power_LB_normalized_slice,
            'str_key_flt_power_UB_normalized_slice' : str_key_flt_power_UB_normalized_slice,
            'str_key_flt_timeinterval_ramp_up_nominal_slice' : str_key_flt_timeinterval_ramp_up_nominal_slice,
            'str_key_flt_timeinterval_ramp_down_nominal_slice' : str_key_flt_timeinterval_ramp_down_nominal_slice,
        }

        # 重新计算GT: 电输出
        self._calculate_power_energy_GT_slice(
            df_GTG=df_GTG,
            bol_is_GTG_elec_or_waste=True,
            arr_index_bol_GT=arr_index_bol_GT_elec_output,
            **dic_params_func
        )

        # 重新计算GT: 燃料浪费
        self._calculate_power_energy_GT_slice(
            df_GTG=df_GTG,
            bol_is_GTG_elec_or_waste=False,
            arr_index_bol_GT=arr_index_bol_GT_waste,
            **dic_params_func
        )
        return

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_GTG = X.copy(deep=True)
        self.split_power_energy_GTG(df_GTG=df_GTG)
        return df_GTG
