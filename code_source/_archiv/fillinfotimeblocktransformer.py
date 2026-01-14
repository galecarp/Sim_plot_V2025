#!/usr/bin/env python3

from sklearn.base import BaseEstimator, TransformerMixin

import numpy as np
import pandas as pd
import copy


import re

from code_source.preprocessing.preprocessing_GTG.generalgtgtransformer import GeneralGTGTransformer

class ConvertTo2DimDictTransformer(BaseEstimator, TransformerMixin, GeneralGTGTransformer):
    """针对GTG的字典, 补充GTG字典中时间切片的信息, 并转化为一个以时间戳为key的二维字典

    *功能:
        * 1.对每一个timeblock转化字符串时间戳到TimeStamp
        * 2.对每一个timeblock, 找出燃机的相关动作
        * 2.对每一个timeblock, 把GTG字典中的燃机的每个切片时间, 补充完整, 使得其填满0.25小时

    前提条件是, 字典每一个状态中的数据都已经展平, 即经过了 FlattenDictTransformer
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
            'bol_key_sector_must_have': True,
            'str_format_timestamp' : r'%Y-%m-%d %H:%M:%S',
            'str_round_timestamp' : '1s',
            'flt_second_difference_allowed' : 1,
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

    def _update_missing_key_from_other_dict(self,
        dic_update_to,
        dic_update_from,
        bol_ignore_missing_key_in_dic_from = True
    ):
        """比较to字典和from字典的key, 把to字典中的缺失的key, 从from字典中补充进来

        Args
        ----
        bol_ignore_missing_key_in_dic_from : bool
            是否忽略from字典中的缺失key, 如果为False时, 如果to字典含有 from字典中没有的key, 则会报错
        """
        # 计算差集
        set_items_difference = set(dic_update_to.items()) ^ set(dic_update_from.items())
        # 分析所有的key
        for key_diff, val_diff in set_items_difference:
            if key_diff in dic_update_to:
                # 如果to字典中有from字典没有的key
                if bol_ignore_missing_key_in_dic_from:
                    continue
                else:
                    raise ValueError(f"key {key_diff} is in dic_update_to, but not in dic_update_from")
            else:
                # 差别的key, 从from字典中补充到to字典
                dic_update_to[key_diff] = dic_update_from[key_diff]
        return
    
    def _update_missing_key_from_nan_dict(self,
        dic_update_to,
        dic_config_all_variables_2D_nan,
        bol_ignore_missing_key_in_dic_from = True
    ):
        """从dic_config_all_variables_2D_nan中补全dic_update_to中的缺失的key已经值
        """
        dic_config_all_variables_2D_nan_with_mapped_name =\
            self.get_dic_config_all_variables_2D_nan_with_mapped_name(dic_config_all_variables_2D_nan)
        self._update_missing_key_from_other_dict(
            dic_update_to=dic_update_to,
            dic_update_from=dic_config_all_variables_2D_nan_with_mapped_name,
            bol_ignore_missing_key_in_dic_from=bol_ignore_missing_key_in_dic_from
        )
        return

    def _add_info_to_new_slice_in_dict_2d(self,
        dic_2d_save,
        ts_timestamp_slice,
        ts_timestamp_timeblock,
        bol_GT_idle,
        dic_general_info_timeblock,
        dic_GT_single_slice,
        str_key_bol_GTG_idle = None,
        str_key_ts_timestamp_GTG_slice = None,
        str_key_ts_timestamp_GTG_timeblock = None,
        dic_config_all_variables_2D_nan=None,
        ):
        """向2D化的字典中, 添加新的时间片并复制对应的信息进入2D字典中

        Args
        ----
        dic_2d_save : dict
            要存储保存结果的二维字典, 以时间戳为key
        ts_timestamp_slice : pd.Timestamp
            时间切片的时间戳
        ts_timestamp_timeblock : pd.Timestamp
            时间切片所属的timeblock的时间戳
        bol_GT_idle : bool
            燃机是否在停止, 为1为停止, 为0为运行. 
            停止状态即为燃机不开机, 即在运行模式-1下
        dic_general_info_timeblock : dict
            时间切片所属的timeblock的general info信息字典, 是整个timeblock中所有信息的总和
        dic_GT_single_slice : dict
            时间切片的原始信息字典

        """
        # 参数读取
        # str_key_bol_GTG_idle = self.get_dic_key(
        #     'str_key_bol_GTG_idle', name_forced=str_key_bol_GTG_idle)
        # str_key_ts_timestamp_GTG_slice = self.get_dic_key(
        #     'str_key_ts_timestamp_GTG_slice', name_forced=str_key_ts_timestamp_GTG_slice)
        # str_key_ts_timestamp_GTG_timeblock = self.get_dic_key(
        #     'str_key_ts_timestamp_GTG_timeblock', name_forced=str_key_ts_timestamp_GTG_timeblock)

        # 建立新的时间切片信息
        if ts_timestamp_slice not in dic_2d_save:
            dic_2d_save.update({ts_timestamp_slice : {}})
        dic_single_slice_in_2d = dic_2d_save.get(ts_timestamp_slice)
        # 添加slice多个新的信息
        dic_single_slice_in_2d.update(
            {
                # 添加slice时间戳信息进入新的字典中
                str_key_ts_timestamp_GTG_slice : ts_timestamp_slice,
                # 添加slice所属的timeblock时间戳信息进入新的字典中
                str_key_ts_timestamp_GTG_timeblock : ts_timestamp_timeblock,
                # 添加燃机是否在运行状态
                str_key_bol_GTG_idle : bol_GT_idle,
            }
        )
        # 添加slice所属的timeblock的general info信息进入新的字典中
        dic_single_slice_in_2d.update(
            dic_general_info_timeblock
        )
        # 添加原始数据中slice的原始信息进入新的字典中
        dic_single_slice_in_2d.update(
            dic_GT_single_slice
        )
        # 如仍然存在缺失的变量信息, 则从dic_config_values_2D_nan中提取补充
        self._update_missing_key_from_nan_dict(
            dic_update_to=dic_single_slice_in_2d,
            dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            bol_ignore_missing_key_in_dic_from=True
        )
        return

    def _add_nan_info_to_new_slice_in_dict_2d(self,
        dic_2d_save,
        ts_timestamp_slice,
        ts_timestamp_timeblock,
        str_key_ts_timestamp_GTG_slice=None,
        str_key_ts_timestamp_GTG_timeblock=None,
        dic_config_all_variables_2D_nan={},
        ):
        """向2D化的字典中, 添加新的时间片以及对应的nan信息
        """
        
        # 建立新的时间切片信息
        if ts_timestamp_slice not in dic_2d_save:
            dic_2d_save.update({ts_timestamp_slice : {}})
        dic_single_slice_in_2d = dic_2d_save.get(ts_timestamp_slice)
        # 添加slice的两个时间戳信息
        dic_single_slice_in_2d.update(
            {
                # 添加slice时间戳信息进入新的字典中
                str_key_ts_timestamp_GTG_slice : ts_timestamp_slice,
                # 添加slice所属的timeblock时间戳信息进入新的字典中
                str_key_ts_timestamp_GTG_timeblock : ts_timestamp_timeblock,
            }
        )
        # 如仍然存在缺失的变量信息, 则从dic_config_values_2D_nan中提取补充
        self._update_missing_key_from_nan_dict(
            dic_update_to=dic_single_slice_in_2d,
            dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            bol_ignore_missing_key_in_dic_from=True
        )
        return

    def _create_first_missing_slice_GTG(self,
        dic_2d_save,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        flt_time_residual_GTG_in_time_block,
        str_prefix_state_GTG=None,
        str_key_ts_timestamp_GTG_slice = None,
        str_key_ts_timestamp_GTG_timeblock = None,
        str_key_flt_percent_ramp_height_last_slice = None,
        str_key_flt_percent_ramp_height_this_slice = None,
        dic_config_all_variables_2D_nan=None,  
        str_round_timestamp=None,
        **kwargs
    ):
        """在一个timeblock下, 为燃机创建补充首个不开机的slice切片, 并记录到新的二维字典中

        * 因为原始log数据中, 如果一个timeblock内, 燃机开机时间并非在15分钟的整点, 则会导致燃机的时间切片不完整
        * 此种情况下, 首个slice的实际时间戳, 是晚于整个timeblock的时间戳的
        * 原始数据中没有给出燃机在此timeblock内的首次开机时间

        Args
        ----
        dic_GTG_single_time_block_new_save : dict
            要保存的燃机更新后的运行状态的字典, 所在层级为单个timeblock
        dic_GTG_single_time_block : dict
            要处理的燃机运行原始log数据字典, 所在层级为单个timeblock
        ts_time_stamp_block : pd.Timestamp
            timeblock的时间戳
        flt_time_residual_GTG_in_time_block : float
            按照原始运行log中的切片数据, 还缺少的时间, 单位为[h]
        """

        # 首个时间切片的时间戳 等于 timeblock的时间戳
        ts_timestamp_slice = ts_timestamp_block
        # 数据log中, 首个时间切片名字
        str_name_state_GTG_1st = str_prefix_state_GTG + str(0)
        # 计算燃机在记录的第一个时间切片中, 所在运行模式mode的高度变化, 即本slice结束后的高度 - 本slice开始的高度
        # 此delta值, 用于判断燃机的启动趋势: delta>0则为燃机启动趋势; delta<0则为燃机停机趋势; delta=0则为燃机维持趋势
        # 使用第一个切片的燃机运行趋势, 代表整个timeblock的燃机运行趋势
        flt_delta_Up_Factor =\
            dic_GTG_single_time_block.get(str_name_state_GTG_1st).get(str_key_flt_percent_ramp_height_this_slice) -\
            dic_GTG_single_time_block.get(str_name_state_GTG_1st).get(str_key_flt_percent_ramp_height_last_slice)
        if flt_delta_Up_Factor > 0 and flt_time_residual_GTG_in_time_block > 0:
            # 向2D化的字典中, 添加新的时间片以及对应的初始化nan信息
            self._add_nan_info_to_new_slice_in_dict_2d(
                dic_2d_save=dic_2d_save,
                ts_timestamp_slice=ts_timestamp_slice,
                ts_timestamp_timeblock=ts_timestamp_block,
                str_key_ts_timestamp_GTG_slice=str_key_ts_timestamp_GTG_slice,
                str_key_ts_timestamp_GTG_timeblock=str_key_ts_timestamp_GTG_timeblock,
                dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            )
            # 调整当前的切片的终结时间, 作为下一个切片的起始时间
            ts_timestamp_slice += pd.Timedelta(flt_time_residual_GTG_in_time_block, unit='H')
            if str_round_timestamp is not None:
                ts_timestamp_slice = ts_timestamp_slice.round(freq=str_round_timestamp)
        return ts_timestamp_slice
    
    def _fix_all_recorded_slice_GTG(self,
        dic_2d_save,
        ts_timestamp_slice,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        lst_name_key_state,
        str_key_general_info_timeblock=None,
        str_key_ts_timestamp_GTG_slice=None,
        str_key_ts_timestamp_GTG_timeblock = None,
        str_key_bol_GTG_idle = None,
        str_key_flt_timeinterval_op_slice = None,
        dic_config_all_variables_2D_nan=None,
        str_round_timestamp=None,
        **kwargs
    ):
        """遍历原始数据log下的每一个原始记录的timeblock中的每一个原始记录的的slice, 并补充完整信息, 以及记录到新的二维字典中
        """

        # 提取此general info字典
        dic_general_info_timeblock = dic_GTG_single_time_block.get(str_key_general_info_timeblock)

        # 遍历所有的slice
        for str_name_key_state in lst_name_key_state:
            # 遍历time blcok下的每一个时间切片
            dic_GT_single_slice = dic_GTG_single_time_block.get(str_name_key_state) 
            flt_time_execution_GTG_slice = dic_GT_single_slice.get(str_key_flt_timeinterval_op_slice)
            # 添加time block的所有信息 与 切片的所有信息

            self._add_info_to_new_slice_in_dict_2d(
                dic_2d_save=dic_2d_save,
                ts_timestamp_slice=ts_timestamp_slice,
                ts_timestamp_timeblock=ts_timestamp_block,
                bol_GT_idle=0,
                dic_general_info_timeblock=dic_general_info_timeblock,
                dic_GT_single_slice=dic_GT_single_slice,
                str_key_bol_GTG_idle = str_key_bol_GTG_idle,
                str_key_ts_timestamp_GTG_slice = str_key_ts_timestamp_GTG_slice,
                str_key_ts_timestamp_GTG_timeblock = str_key_ts_timestamp_GTG_timeblock,
                dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            )
            # 调整当前的切片的终结时间, 作为下一个切片的起始时间
            ts_timestamp_slice += pd.Timedelta(flt_time_execution_GTG_slice, unit='H')
            if str_round_timestamp is not None:
                ts_timestamp_slice = ts_timestamp_slice.round(freq=str_round_timestamp)
        return ts_timestamp_slice

    def _create_last_missing_slice_GTG(self,
        dic_2d_save,
        ts_timestamp_slice,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        lst_name_key_state,
        flt_time_residual_GTG_in_time_block,
        str_prefix_state_GTG=None,
        str_key_ts_timestamp_GTG_slice=None,
        str_key_ts_timestamp_GTG_timeblock=None,
        str_key_flt_percent_ramp_height_last_slice = None,
        str_key_flt_percent_ramp_height_this_slice = None,
        dic_config_all_variables_2D_nan=None,
        str_round_timestamp=None,
        **kwargs
    ):
        """在一个timeblock下, 为燃机创建补充timeblock最后一个不开机的slice切片, 并记录到新的二维字典中

        * 因为原始log数据中, 如果一个timeblock内, 燃机关机时间并非在15分钟的整点, 则会导致燃机的时间切片不完整
        * 此种情况下, 实际最后一个slice的实际时间戳, 是晚于整个timeblock所记录的最后一个slice的时间戳的
        * 原始数据中没有给出燃机在此timeblock内的最后一个时间切片

        Args
        ----
        dic_GTG_single_time_block_new_save : dict
            要保存的燃机更新后的运行状态的字典, 所在层级为单个timeblock
        dic_GTG_single_time_block : dict
            要处理的燃机运行原始log数据字典, 所在层级为单个timeblock
        ts_time_stamp_block : pd.Timestamp
            timeblock的时间戳
        flt_time_residual_GTG_in_time_block : float
            按照原始运行log中的切片数据, 还缺少的时间, 单位为[h]
        """
        
        # 数据log中, 最后一个切片名字
        str_name_key_last_recorded_state = lst_name_key_state[-1]
        str_name_key_new_last_state = str_prefix_state_GTG + str(len(lst_name_key_state))
        # 计算燃机在记录的最后一个时间切片中, 所在运行模式mode的高度变化, 即本slice结束后的高度 - 本slice开始的高度
        # 此delta值, 用于判断燃机的启动趋势: delta>0则为燃机启动趋势; delta<0则为燃机停机趋势; delta=0则为燃机维持趋势
        # 使用第一个切片的燃机运行趋势, 代表整个timeblock的燃机运行趋势
        flt_delta_Up_Factor =\
            dic_GTG_single_time_block.get(str_name_key_last_recorded_state).get(str_key_flt_percent_ramp_height_this_slice) -\
            dic_GTG_single_time_block.get(str_name_key_last_recorded_state).get(str_key_flt_percent_ramp_height_last_slice)
        if flt_delta_Up_Factor <= 0 and flt_time_residual_GTG_in_time_block > 0:
            # 停机/维持趋势 且 需要补时间
            self._add_nan_info_to_new_slice_in_dict_2d(
                dic_2d_save=dic_2d_save,
                ts_timestamp_slice=ts_timestamp_slice,
                ts_timestamp_timeblock=ts_timestamp_block,
                str_key_ts_timestamp_GTG_slice=str_key_ts_timestamp_GTG_slice,
                str_key_ts_timestamp_GTG_timeblock=str_key_ts_timestamp_GTG_timeblock,
                dic_config_all_variables_2D_nan=dic_config_all_variables_2D_nan,
            )
            # 调整当前的切片的终结时间, 作为下一个切片的起始时间
            ts_timestamp_slice += pd.Timedelta(flt_time_residual_GTG_in_time_block, unit='H')
            if str_round_timestamp is not None:
                ts_timestamp_slice = ts_timestamp_slice.round(freq=str_round_timestamp)
        return ts_timestamp_slice

    def _calculate_ramp_trend_GTG(self,
        dic_2d_save,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        lst_name_key_state,
        str_key_bol_ramp_up_GTG_slice=None,
        str_key_bol_ramp_up_GTG_timeblock=None,
        str_key_flt_percent_ramp_height_last_slice=None,
        str_key_flt_percent_ramp_height_this_slice=None,
        **kwargs
    ):
        """计算燃机在一个time block / 每个时间切片中, 燃机的运行趋势, 并存储在dict中为单独的boolean参数
        """
        # timeblock初始化
        bol_ramp_up_GTG_timeblock = None
        dic_ramp_trend_GTG_timeblock = {}
        # 对每一个时间切片计算其燃机的运行趋势
        for idx_state, str_name_key_recorded_state in enumerate(lst_name_key_state):
            dic_single_state_GTG = dic_GTG_single_time_block.get(str_name_key_recorded_state)
            flt_delta_Up_Factor_slice =\
                dic_single_state_GTG.get(str_key_flt_percent_ramp_height_this_slice) -\
                dic_single_state_GTG.get(str_key_flt_percent_ramp_height_last_slice)
            # 计算燃机在当前时间切片的运行趋势
            if flt_delta_Up_Factor_slice > 0:
                bol_ramp_up_GTG_slice = True
            elif flt_delta_Up_Factor_slice < 0:
                bol_ramp_up_GTG_slice = False
            else:
                # 当前切片的启动趋势与上一个切片的启动趋势一致; 首次不明趋势时被赋值None, 需要之后修正
                bol_ramp_up_GTG_slice = bol_ramp_up_GTG_timeblock
            # 检查一个timeblock中, 是否有两种不同的运行趋势
            if bol_ramp_up_GTG_timeblock is None:
                # 第一个时间切片不检查, 直接赋值
                bol_ramp_up_GTG_timeblock = bol_ramp_up_GTG_slice
            else:
                if bol_ramp_up_GTG_timeblock ^ bol_ramp_up_GTG_slice:
                    # 一个timeblock不允许出现两种不同的运行趋势
                    raise ValueError(
                        '燃机的运行趋势在一个time block中不一致\n'+\
                        'ts_timestamp_block: {}\n'.format(ts_timestamp_block)+\
                        '切片名字: {}\n'.format(str_name_key_recorded_state)+\
                        'bol_ramp_up_GTG_timeblock: {}\n'.format(bol_ramp_up_GTG_timeblock)+\
                        'bol_ramp_up_GTG_slice: {}\n'.format(bol_ramp_up_GTG_slice)
                    )
            # 暂时保存燃机的运行趋势
            dic_ramp_trend_GTG_timeblock.update({str_name_key_recorded_state : bol_ramp_up_GTG_slice})
        # 保存timeblock的整体运行趋势
        if bol_ramp_up_GTG_timeblock is None:
            if len(lst_name_key_state)==1:
                # 如果只有一个切片, 说明燃机在最大负荷处, 则直接赋值为上升趋势
                bol_ramp_up_GTG_timeblock = True
            else:
                raise ValueError(
                    '燃机的运行趋势在一个有燃机活动的time block中没有记录\n'+\
                    'ts_timestamp_block: {}\n'.format(ts_timestamp_block)+\
                    '最后一个切片名字: {}\n'.format(str_name_key_recorded_state)
        )
        dic_2d_save.update(
            {str_key_bol_ramp_up_GTG_timeblock : bol_ramp_up_GTG_timeblock})
        # 保存每一个时间切片的运行趋势
        for str_name_key_recorded_state, bol_ramp_up_GTG_slice in dic_ramp_trend_GTG_timeblock.items():
            dic_single_state_GTG = dic_GTG_single_time_block.get(str_name_key_recorded_state)
            if bol_ramp_up_GTG_slice is None:
                bol_ramp_up_GTG_slice = bol_ramp_up_GTG_timeblock
            dic_single_state_GTG.update({str_key_bol_ramp_up_GTG_slice : bol_ramp_up_GTG_slice})
        return
    
    def _calculate_ramp_trend_slice(self,
        dic_GTG_single_time_block,
        str_name_key_recorded_state,
        **kwargs
    ):
        """计算一个slice的燃机的运行趋势
        """
        str_key_GTG_flt_percent_ramp_height_this_slice = kwargs.get('str_key_GTG_flt_percent_ramp_height_this_slice')
        str_key_GTG_flt_percent_ramp_height_last_slice = kwargs.get('str_key_GTG_flt_percent_ramp_height_last_slice')
        dic_single_state_GTG = dic_GTG_single_time_block.get(str_name_key_recorded_state)
        flt_delta_Up_Factor_slice =\
            dic_single_state_GTG.get(str_key_GTG_flt_percent_ramp_height_this_slice) -\
            dic_single_state_GTG.get(str_key_GTG_flt_percent_ramp_height_last_slice)
        # 计算燃机在当前时间切片的运行趋势
        if flt_delta_Up_Factor_slice > 0:
            bol_ramp_up_GTG_slice = True
        elif flt_delta_Up_Factor_slice < 0:
            bol_ramp_up_GTG_slice = False
        else:
            # 当前切片的启动趋势不变时, 赋予None, 表示无法从当前slice判断燃机的运行趋势
            bol_ramp_up_GTG_slice = None
        return bol_ramp_up_GTG_slice
    
    def _fill_general_info_timeblock(self,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        lst_name_key_state,
        str_key_Gen_idle_timeblock,
        str_key_Gen_ts_timestamp_start_timeblock,
        str_key_Gen_ts_timestamp_end_timeblock,
        str_key_Gen_flt_timeinterval_op_timeblock,
        str_key_Gen_flt_Energy_changes_inlet_timeblock,
        str_key_Gen_flt_Energy_changes_internal_timeblock,
        str_key_Gen_flt_Energy_changes_outlet_timeblock,
        str_key_GTG_flt_energy_GT_elec_output_timeblock,
        str_key_GTG_flt_energy_GT_waste_timeblock,
        str_key_GTG_bol_ramp_up_GTG_timeblock,
        str_key_GTG_flt_eta_elec_normalized_timeblock,
        **kwargs
    ):
        """ 填充一个timeblock中的所有信息, 并返回为一个dic_general_info_timeblock的字典中
        """
        # 提取timeblock的参数名
        str_key_Gen_idle_timeblock = kwargs.get('str_key_Gen_idle_timeblock')
        str_key_Gen_ts_timestamp_start_timeblock = kwargs.get('str_key_Gen_ts_timestamp_start_timeblock')
        str_key_Gen_ts_timestamp_end_timeblock = kwargs.get('str_key_Gen_ts_timestamp_end_timeblock')
        str_key_Gen_flt_timeinterval_op_timeblock = kwargs.get('str_key_Gen_flt_timeinterval_op_timeblock')
        str_key_Gen_flt_Energy_changes_inlet_timeblock = kwargs.get('str_key_Gen_flt_Energy_changes_inlet_timeblock')
        str_key_Gen_flt_Energy_changes_internal_timeblock = kwargs.get('str_key_Gen_flt_Energy_changes_internal_timeblock')
        str_key_Gen_flt_Energy_changes_outlet_timeblock = kwargs.get('flt_Energy_{GTG,GT,3_energy_changes,outlet,timeblock}')
        str_key_GTG_flt_energy_GT_elec_output_timeblock = kwargs.get('str_key_GTG_flt_energy_GT_elec_output_timeblock')
        str_key_GTG_flt_energy_GT_waste_timeblock = kwargs.get('str_key_GTG_flt_energy_GT_waste_timeblock')
        str_key_GTG_bol_ramp_up_GTG_timeblock = kwargs.get('str_key_GTG_bol_ramp_up_GTG_timeblock')
        str_key_GTG_flt_eta_elec_normalized_timeblock = kwargs.get('str_key_GTG_flt_eta_elec_normalized_timeblock')
        # 提取slice的参数名
        str_key_Gen_ts_timestamp_start_slice = kwargs.get('str_key_Gen_ts_timestamp_start_slice')
        # 提取timeblock的参数值
        dic_general_info_timeblock = dict()
        ## 1.计算timeblock的是否在停机状态
        dic_general_info_timeblock.update({'str_key_Gen_idle_timeblock' : False})
        ## 2.计算timeblock的起始时间, 为第一个切片的起始时间
        str_name_state_GTG_1st = lst_name_key_state[0]
        dic_general_info_timeblock.update(
            {str_key_Gen_ts_timestamp_start_timeblock :\
            dic_GTG_single_time_block(str_name_state_GTG_1st).get(str_key_Gen_ts_timestamp_start_slice)})
        ## 3.计算timeblock的结束时间
        str_name_state_GTG_last = lst_name_key_state[-1]
        dic_general_info_timeblock.update(
            {str_key_Gen_ts_timestamp_end_timeblock :\
            dic_GTG_single_time_block(str_name_state_GTG_last).get(str_key_Gen_ts_timestamp_end_timeblock)})
        # 4.计算timeblock的总运行时间   
        lst_flt_timeinterval_op_timeblock = [
            dic_GTG_single_time_block.get(str_name_key_state).get(str_key_Gen_flt_timeinterval_op_timeblock)
            for str_name_key_state in lst_name_key_state]
        lst_flt_timeinterval_op_timeblock = np.sum()
        return

    def _fill_info_slice(self,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        lst_name_key_state,
        **kwargs
    ):
        """在一个timeblock里, 为每一个slice补充一个时间切片的其他信息 \TODOstr_format_timestamp
        """
        # 提取config中的数值
        str_round_timestamp = kwargs.get('str_round_timestamp')
        str_format_timestamp = kwargs.get('str_format_timestamp')
        # 提取已有的参数名
        str_key_Gen_ts_timestamp_start_slice = kwargs.get('str_key_Gen_ts_timestamp_start_slice')
        str_key_GTG_flt_timeinterval_op_slice = kwargs.get('str_key_GTG_flt_timeinterval_op_slice')
        # 提取新加入的key的参数名
        str_key_Gen_idle_slice = kwargs.get('str_key_Gen_idle_slice')
        str_key_Gen_ts_timestamp_end_slice = kwargs.get('str_key_Gen_ts_timestamp_end_slice')
        str_key_GTG_bol_ramp_up_GTG_slice = kwargs.get('str_key_GTG_bol_ramp_up_GTG_slice')
        str_key_GTG_flt_power_GT_elec_output_start_slice = kwargs.get('str_key_GTG_flt_power_GT_elec_output_start_slice')
        str_key_GTG_flt_power_GT_elec_output_end_slice = kwargs.get('str_key_GTG_flt_power_GT_elec_output_end_slice')
        str_key_GTG_flt_power_GT_waste_start_slice = kwargs.get('str_key_GTG_flt_power_GT_waste_start_slice')
        str_key_GTG_flt_power_GT_waste_end_slice = kwargs.get('str_key_GTG_flt_power_GT_waste_end_slice')
        str_key_GTG_flt_power_GT_elec_output_LB_slice = kwargs.get('str_key_GTG_flt_power_GT_elec_output_LB_slice')
        str_key_GTG_flt_power_GT_elec_output_UB_slice = kwargs.get('str_key_GTG_flt_power_GT_elec_output_UB_slice')
        str_key_GTG_flt_power_GT_waste_LB_slice = kwargs.get('str_key_GTG_flt_power_GT_waste_LB_slice')
        str_key_GTG_flt_power_GT_waste_UB_slice = kwargs.get('str_key_GTG_flt_power_GT_waste_UB_slice')
        str_key_GTG_flt_energy_GT_elec_output_slice = kwargs.get('str_key_GTG_flt_energy_GT_elec_output_slice')
        str_key_GTG_flt_energy_GT_waste_slice = kwargs.get('str_key_GTG_flt_energy_GT_waste_slice')
        # 迭代所有的slice
        for str_name_state in lst_name_key_state:
            # 提取一个slice的信息
            dic_GTG_single_slice = dic_GTG_single_time_block.get(str_name_state)
            # 1.计算slice的是否在停机状态
            dic_GTG_single_slice.update({str_key_Gen_idle_slice : False})
            # 2.计算slice的结束时间
            ts_timestamp_start_slice = pd.to_datetime(
                dic_GTG_single_slice.get(str_key_Gen_ts_timestamp_start_slice), format=str_format_timestamp)
            flt_timeinterval_op_slice = dic_GTG_single_slice.get(str_key_GTG_flt_timeinterval_op_slice)
            ts_timestamp_end_slice = ts_timestamp_start_slice + pd.Timedelta(flt_timeinterval_op_slice, unit='H')
            if str_round_timestamp is not None:
                ts_timestamp_start_slice = ts_timestamp_start_slice.round(freq=str_round_timestamp)
                ts_timestamp_end_slice = ts_timestamp_end_slice.round(freq=str_round_timestamp)
            dic_GTG_single_slice.update({str_key_Gen_ts_timestamp_start_slice : ts_timestamp_start_slice})
            dic_GTG_single_slice.update({str_key_Gen_ts_timestamp_end_slice : ts_timestamp_end_slice})
            # 3.计算slice的运行趋势
            bol_ramp_up_GTG_slice = self._calculate_ramp_trend_slice(self,
                dic_GTG_single_time_block,
                str_name_key_recorded_state=str_name_state,
                **kwargs)
            dic_GTG_single_slice.update({str_key_GTG_bol_ramp_up_GTG_slice : bol_ramp_up_GTG_slice})
            # 4.计算slice的电功率输出
            
        return

    def func_fix_timeblock_GTG(self,
        dic_2d_save,
        ts_timestamp_block,
        dic_GTG_single_time_block,
        **kwargs
    ):
        """对一个timeblock, 补充GT每一个时间切片状态的子函数, 为多个切片进行时间戳赋值, 并补充不完整的timeblock中的行为

        一个time block只有一个/多个运行切片

        * 每一个slice行为趋势:
            * Up_Factor - Up_Factor_old > 0: 启动趋势
            * Up_Factor - Up_Factor_old < 0: 停机趋势
            * Up_Factor - Up_Factor_old == 0: 维持趋势
        # 首个切片的启动时间:
            * 在启动趋势时, delta_time_slice = flt_timeinterval_timeblock_max - 总time_block时间
            * 在维持趋势时, delta_time_slice = 0
            * 在停机趋势时, delta_time_slice = 0

        # 首个填补时间
            * 仅在启动趋势时发生
            * 在time block起始时间到第一个时间slice之间, 补充一个时间段, 描述燃机不开
        # 末尾填补时间
            * 仅在停机趋势/维持趋势时发生
            * 最后一个时间slice 结束时间 到 在ime block结束时间之间, 补充一个时间段, 描述燃机不开
        """
        # 读取参数名
        str_key_Gen_idle_timeblock = kwargs.get('str_key_Gen_idle_timeblock')
        str_key_Gen_ts_timestamp_start_timeblock = kwargs.get('str_key_Gen_ts_timestamp_start_timeblock')
        str_key_Gen_ts_timestamp_end_timeblock = kwargs.get('str_key_Gen_ts_timestamp_end_timeblock')
        str_key_Gen_flt_timeinterval_op_timeblock = kwargs.get('str_key_Gen_flt_timeinterval_op_timeblock')
        str_key_Gen_flt_Energy_changes_inlet_timeblock = kwargs.get('str_key_Gen_flt_Energy_changes_inlet_timeblock')
        str_key_Gen_flt_Energy_changes_internal_timeblock = kwargs.get('str_key_Gen_flt_Energy_changes_internal_timeblock')
        str_key_Gen_flt_Energy_changes_outlet_timeblock = kwargs.get('flt_Energy_{GTG,GT,3_energy_changes,outlet,timeblock}')
        str_key_GTG_flt_energy_GT_elec_output_timeblock = kwargs.get('str_key_GTG_flt_energy_GT_elec_output_timeblock')
        str_key_GTG_flt_energy_GT_waste_timeblock = kwargs.get('str_key_GTG_flt_energy_GT_waste_timeblock')
        str_key_GTG_bol_ramp_up_GTG_timeblock = kwargs.get('str_key_GTG_bol_ramp_up_GTG_timeblock')
        str_key_GTG_flt_eta_elec_normalized_timeblock = kwargs.get('str_key_GTG_flt_eta_elec_normalized_timeblock')
        # 提取config中的数值
        flt_second_difference_allowed=kwargs.get('flt_second_difference_allowed')
        flt_timeinterval_timeblock_max = kwargs.get('flt_timeinterval_timeblock_max')
        # 提取config的参数名
        str_prefix_state_GTG = kwargs.get('str_prefix_state_GTG')

        # 提取slice的参数名   

        flt_time_residual_GTG_in_time_block = None
        if flt_time_residual_GTG_in_time_block < 0:
            raise ValueError('燃机运行时间超过了一个切片的时间')

        # 提取此time block下的所有运行切片的名字, 并排序
        lst_name_key_state = [key for key in dic_GTG_single_time_block.keys() if key.startswith(str_prefix_state_GTG)]
        lst_name_key_state = sorted(lst_name_key_state, key=lambda x: int(re.sub(str_prefix_state_GTG, '', x)))

        # 提取此slice下的信息

        # 提取此time block下的信息
        dic_general_info_timeblock = self._fill_general_info_timeblock_GTG(
            **kwargs
        )
        # 提取并设定燃机在整个time block的运行趋势走向，依照第一个切片的趋势
        self._calculate_ramp_trend_GTG(
            ts_timestamp_block=ts_timestamp_block,
            dic_GTG_single_time_block=dic_GTG_single_time_block,
            lst_name_key_state=lst_name_key_state,
            **kwargs
        )

        ## 1.补充首个不开机的燃机状态
        ts_timestamp_slice = self._create_first_missing_slice_GTG(
            dic_2d_save=dic_2d_save,
            ts_timestamp_block=ts_timestamp_block,
            dic_GTG_single_time_block=dic_GTG_single_time_block,
            flt_time_residual_GTG_in_time_block=flt_time_residual_GTG_in_time_block,
            **kwargs
        )

        # 2.遍历原始数据中已有的slice
        ts_timestamp_slice = self._fix_all_recorded_slice_GTG(
            dic_2d_save=dic_2d_save,
            ts_timestamp_slice=ts_timestamp_slice,
            ts_timestamp_block=ts_timestamp_block,
            dic_GTG_single_time_block=dic_GTG_single_time_block,
            lst_name_key_state=lst_name_key_state,
            **kwargs
        )

        ## 3.补充末尾不开机的燃机状态
        ts_timestamp_slice = self._create_last_missing_slice_GTG(
            dic_2d_save=dic_2d_save,
            ts_timestamp_slice=ts_timestamp_slice,
            ts_timestamp_block=ts_timestamp_block,
            dic_GTG_single_time_block=dic_GTG_single_time_block,
            lst_name_key_state=lst_name_key_state,
            flt_time_residual_GTG_in_time_block=flt_time_residual_GTG_in_time_block,
            **kwargs
        )

        # 检查最后时间切片所在的时间戳, 是否等于下一个time block起始时间戳, 如果不等于, 则报错

        timedelta_difference =\
            ts_timestamp_slice - ts_timestamp_block - pd.Timedelta(flt_timeinterval_timeblock_max, unit='H')
        if  (
                timedelta_difference >= pd.Timedelta(0, unit='s')
                and \
                timedelta_difference > pd.Timedelta(flt_second_difference_allowed, unit='s')
            ) or \
            (
                -timedelta_difference < pd.Timedelta(0, unit='s')
                and \
                -timedelta_difference < pd.Timedelta(-flt_second_difference_allowed, unit='s')
                
            ):
            raise ValueError(
                '运行后的时间戳不等于整个time block完整的时间, 出错了',
                '程序运行结束时的ts_timestamp_slice: {} '.format(ts_timestamp_slice),
                '本time block的起始时间戳: {}'.format(ts_timestamp_block),
            )
        return
    
    def get_patched_config_with_lib(self,
        dic_config_default,
        **kwargs
    ):
        """ 从kwargs中读取参数, 并与dic_config_all_variables_2D_nan_default中的默认值进行替换合并
        """
        dic_key_params = {}
        for key in list(dic_config_default.items()):
            dic_key_params[key] = self._get_param_with_forced(
                name_param_in_config=key, val_param=kwargs.get(key, None))
            kwargs.pop(key, None)
        return dic_key_params

    def get_patched_key_with_lib(self,
        dic_config_map_name_variables_default,
        **kwargs
    ):
        """ 从kwargs中读取参数, 并与dic_config_map_name_variables_default中的默认值进行替换合并
        """
        dic_key_params = {}
        for key in list(dic_config_map_name_variables_default.keys()):
            dic_key_params[key] = self.get_dic_key(
                key, name_forced=kwargs.get(key, None))
            kwargs.pop(key, None)
        return dic_key_params

    def convert_GTG_slice_to_2d_dict(self,
        dic_GTG,
        bol_key_sector_must_have=True,
        flt_timeinterval_timeblock_max=None,
        str_format_timestamp=None,
        str_round_timestamp=None,
        flt_second_difference_allowed=None,
        dic_config_all_variables_2D_nan=None,
        **kwargs
    ):
        """ 把GTG的原始log数据转化为按时间切片slice为key的二维字典, 此为外层函数

        Args
        ----
        dic_GTG : dict
            GTG的原始log数据
        bol_key_sector_must_have : bool, default True
            每一个时间块timeblock下, 是否必须包含sector的名字, 对于GTG来说sector的名字是'GasTurbGroup'
        flt_timeinterval_timeblock_max : float, default 0.25
            一个时间块timeblock的预设时间长度, 单位是 [h]
        str_key_sector : str, default 'GasTurbGroup'
            GTG的原始log数据中, sector的名字
        
        """
        # 参数整合
        dic_params_func = {}
        dic_params_func.update(
            self.get_patched_config_with_lib(self._dic_config, **kwargs))
        dic_params_func.update(
            self.get_patched_key_with_lib(self._dic_config_map_name_variables, **kwargs))

        # 默认NAN值的字典读取
        if dic_config_all_variables_2D_nan is None:
            dic_config_all_variables_2D_nan = self._dic_config_all_variables_2D_nan 

        # 转化为以时间戳为key的二维字典
        dic_2d_save = {}
        # 读取参数
        str_key_dic_sector = self.get_dic_key('str_key_dic_sector')
        str_key_sector = self.get_dic_key('str_key_sector')
        # 遍历每一个时间块的时间戳
        for str_timestamp, dic_content in dic_GTG.items():
            # 解析时间戳
            ts_timestamp_block = pd.to_datetime(str_timestamp, format=str_format_timestamp)
            if str_round_timestamp is not None:
                ts_timestamp_block = ts_timestamp_block.round(freq=str_round_timestamp)
            # 跳过'dic_sector'这一层
            dic_sector = dic_content.get(str_key_dic_sector)
            if\
                (not bol_key_sector_must_have)\
                or\
                (str_key_sector in dic_sector):
                # 存在sector的key 或者 不需要sector的key
                dic_GTG_single_time_block = dic_sector[str_key_sector]
                if len(dic_GTG_single_time_block) < 2:
                    # GTG中起码要有一个timeblock信息 和 一个状态信息
                    raise ValueError(
                        'GTG在时间{str_time_stamp}的数据缺失'+\
                        '当前GTG时间的timeblock字典信息为:{dic_GTG_single_time_block}'
                    )
                else:
                    # 对每一个time block进行时间片的补充优化
                    dic_params_func.update(kwargs)
                    self.func_fix_timeblock_GTG(
                        dic_2d_save=dic_2d_save,
                        ts_timestamp_block=ts_timestamp_block,
                        dic_GTG_single_time_block=dic_GTG_single_time_block,
                        **dic_params_func,
                    )
        return dic_2d_save


    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = copy.deepcopy(X)
        dic_2d_save = self.convert_GTG_slice_to_2d_dict(X)
        return dic_2d_save
