#!/usr/bin/env python3

import copy

from sklearn.base import BaseEstimator, TransformerMixin

import numpy as np

from code_source.abstractclasses.abstractclassconfig import AbstractClassConfig
from code_source.abstractclasses.abstractconfigvariablesnan import AbstractClassVariablesNaN
from code_source.abstractclasses.abstractclassvariablemapping import AbstractClassVariableMapping

class DataReaderTransformer(AbstractClassConfig, AbstractClassVariableMapping, AbstractClassVariablesNaN):
    """ 读取不同的数据文件
    
    适用于2024版本
    """
    def __init__(self,
        **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_dic_config_map_name_variables(**kwargs)
        self._init_dic_config_all_variables_2D_nan(**kwargs)
        self._init_dic_config(**kwargs)
        pass

    def _init_dic_config(self,
        **kwargs
    ):
        """ 定义之后config中的空字典
        """
        self._dic_config = {}
        return

    def _init_dic_config_map_name_variables(self,
        dic_config_map_name_variables=None,
        **kwargs
        ):
        """ 定义GTGDataFrame中, 本类中的变量名与原始数据中的变量名的对应关系
        """
        dic_config_map_name_variables_default = {
            # 一些非列名的命名规范
            'str_prefix_state_GTG' : 'states_of_GT_No',
            'str_key_sector' : 'GasTurbGroup',
            'str_key_dic_sector' : 'dic_sector',
            'str_key_general_info_timeblock' : 'general_info_GT',
            # 新添加的变量
            'str_key_ts_timestamp_GTG_slice' : 'ts_Timestamp_{GTG,GT,op,slice}',
            'str_key_ts_timestamp_GTG_timeblock' : 'ts_Timestamp_{GTG,GT,op,timeblock}',
            'str_key_bol_GTG_idle' : 'bol_GT_idle',
            # 新添加的拆分出来的变量
            'str_key_bol_ramp_up_GTG_slice' : 'bol_RampUp_{GTG,GT,slice}',
            'str_key_bol_ramp_up_GTG_timeblock' : 'bol_RampUp_{GTG,GT,timeblock}',
            'str_key_flt_power_GT_elec_output_start_slice' : 'flt_Power_{GTG,GT,elec-output,start,slice}',
            'str_key_flt_power_GT_elec_output_end_slice' : 'flt_Power_{GTG,GT,elec-output,end,slice}',
            'str_key_flt_power_GT_waste_start_slice' : 'flt_Power_{GTG,GT,waste-consume,start,slice}',
            'str_key_flt_power_GT_waste_end_slice' : 'flt_Power_{GTG,GT,waste-consume,end,slice}',
            'str_key_flt_power_GT_elec_output_LB_slice' : 'flt_Power_{GTG,GT,elec-output,LB,slice}',
            'str_key_flt_power_GT_elec_output_UB_slice' : 'flt_Power_{GTG,GT,elec-output,UB,slice}',
            'str_key_flt_power_GT_waste_LB_slice' : 'flt_Power_{GTG,GT,waste-consume,LB,slice}',
            'str_key_flt_power_GT_waste_UB_slice' : 'flt_Power_{GTG,GT,waste-consume,UB,slice}',
            'str_key_flt_energy_GT_elec_output_slice' : 'flt_Energy_{GTG,GT,elec-output,slice}',
            'str_key_flt_energy_GT_waste_slice' : 'flt_Energy_{GTG,GT,waste-consume,slice}',
            'str_key_flt_energy_GT_elec_output_timeblock' : 'flt_Energy_{GTG,GT,elec-output,timeblock}',
            'str_key_flt_energy_GT_waste_timeblock' : 'flt_Energy_{GTG,GT,waste-consume,timeblock}',

            # 从原始数据中timeblock的general info信息字典
            'str_key_flt_power_demand_GTG_timeblock' : 'flt_Power_{GTG,GT,demand,elec,timeblock}',
            'str_key_flt_timeinterval_GTG_timeblock' : 'flt_TimeInterval_{GTG,GT,op,timeblock}',
            'str_key_flt_energy_GTG_timeblock' : 'flt_Energy_{GTG,GT,elec/waste,timeblock}',

            # 原始数据中的已有的slice变量名
            'str_key_bol_GTG_elec_slice' : 'bol_{GTG,GT,elec,slice}',
            'str_key_flt_energy_GTG_elec_or_waste_slice': 'flt_Energy_{GTG,GT,elec/waste,slice}',
            'str_key_int_indexmode_GTG_slice' : 'int_IndexMode_{GTG,GT,slice}',
            'str_key_str_namemode_GTG_slice' : 'str_NameMode_{GTG,GT,op,slice}',
            'str_key_flt_timeinterval_ramp_up_nominal_slice' : 'flt_TimeInterval_{GTG,GT,ramp_up,nominal,slice}',
            'str_key_flt_timeinterval_ramp_down_nominal_slice' : 'flt_TimeInterval_{GTG,GT,ramp_down,nominal,slice}',
            'str_key_flt_timeinterval_ramp_up_past_equiv_slice' : 'flt_TimeInterval_{GTG,GT,ramp_up,past-equiv,slice}',
            'str_key_flt_timeinterval_ramp_down_past_equiv_slice' : 'flt_TimeInterval_{GTG,GT,ramp_down,past-equiv,slice}',
            'str_key_flt_timeinterval_op_slice' : 'flt_TimeInterval_{GTG,GT,op,slice}',
            'str_key_flt_power_LB_normalized_slice' : 'flt_Power_{GTG,GT,mode-LB,normalized,slice}',
            'str_key_flt_power_UB_normalized_slice' : 'flt_Power_{GTG,GT,mode-UB,normalized,slice}',
            'str_key_flt_power_elec_normalized_begin_slice' : 'flt_Power_{GTG,GT,elec,normalized,begin,slice}',
            'str_key_flt_power_elec_normalized_end_slice' : 'flt_Power_{GTG,GT,elec,normalized,end,slice}',
            'str_key_flt_percent_ramp_height_last_slice' : 'flt_Percent_{GTG,GT,ramp_height,last_slice}',
            'str_key_flt_percent_ramp_height_this_slice' : 'flt_Percent_{GTG,GT,ramp_height,this_slice}',  
            'str_key_flt_eta_elec_normalized_slice' : 'flt_Eta_{GTG,GT,elec,normalized,slice}',
        }
        # 替换默认的字典
        self._dic_config_map_name_variables = {}
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config_map_name_variables,
            dic_update_from=dic_config_map_name_variables_default,
            bol_create_new_key=False,
            bol_replace_dict=True,
        )
        # # 更新自定义的字典
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config_map_name_variables,
            dic_update_from=dic_config_map_name_variables,
            bol_create_new_key=False,
            bol_replace_dict=False,
        )
        pass

    def _init_dic_config_all_variables_2D_nan(self,
        dic_config_all_variables_2D_nan=None,
        **kwargs):
        """ 定义GTGDataFrame中, 燃机类中应该包含的所有的变量名, 以及对应的缺失下的默认值
        """
        dic_config_all_variables_2D_nan_default = {
            # 新添加的变量
            'str_key_ts_timestamp_GTG_slice' : np.nan,
            'str_key_ts_timestamp_GTG_timeblock' : np.nan,
            'str_key_bol_GTG_idle' : 1,
            # 新添加的拆分出来的变量
            'str_key_bol_ramp_up_GTG_slice' : np.nan,
            'str_key_bol_ramp_up_GTG_timeblock' : np.nan,            
            'str_key_flt_power_GT_elec_output_start_slice' : np.nan,
            'str_key_flt_power_GT_elec_output_end_slice' : np.nan,
            'str_key_flt_power_GT_waste_start_slice' : np.nan,
            'str_key_flt_power_GT_waste_end_slice' : np.nan,
            'str_key_flt_power_GT_elec_output_LB_slice' : np.nan,
            'str_key_flt_power_GT_elec_output_UB_slice' : np.nan,
            'str_key_flt_power_GT_waste_LB_slice' : np.nan,
            'str_key_flt_power_GT_waste_UB_slice' : np.nan,
            'str_key_flt_energy_GT_elec_output_slice' : np.nan,
            'str_key_flt_energy_GT_waste_slice' : np.nan,
            'str_key_flt_energy_GT_elec_output_timeblock' : np.nan,
            'str_key_flt_energy_GT_waste_timeblock' : np.nan,

            # 从原始数据中timeblock的general info信息字典
            'str_key_flt_power_demand_GTG_timeblock' : np.nan,
            'str_key_flt_timeinterval_GTG_timeblock' : np.nan,
            'str_key_flt_energy_GTG_timeblock' : np.nan,

            # 原始数据中的已有的slice变量名
            'str_key_bol_GTG_elec_slice' : np.nan,
            'str_key_flt_energy_GTG_elec_or_waste_slice': np.nan,
            'str_key_int_indexmode_GTG_slice' : np.nan,
            'str_key_str_namemode_GTG_slice' : np.nan,
            'str_key_flt_timeinterval_ramp_up_nominal_slice' : np.nan,
            'str_key_flt_timeinterval_ramp_down_nominal_slice' : np.nan,
            'str_key_flt_timeinterval_ramp_up_past_equiv_slice' : np.nan,
            'str_key_flt_timeinterval_ramp_down_past_equiv_slice' : np.nan,
            'str_key_flt_timeinterval_op_slice' : np.nan,
            'str_key_flt_power_LB_normalized_slice' : np.nan,
            'str_key_flt_power_UB_normalized_slice' : np.nan,
            'str_key_flt_power_elec_normalized_begin_slice' : np.nan,
            'str_key_flt_power_elec_normalized_end_slice' : np.nan,
            'str_key_flt_percent_ramp_height_last_slice' : np.nan,
            'str_key_flt_percent_ramp_height_this_slice' : np.nan,  
            'str_key_flt_eta_elec_normalized_slice' : np.nan,
        }
        # 替换默认的字典
        self._dic_config_all_variables_2D_nan = {}
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config_all_variables_2D_nan,
            dic_update_from=dic_config_all_variables_2D_nan_default,
            bol_create_new_key=False,
            bol_replace_dict=True,
        )
        # 更新自定义的字典
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config_all_variables_2D_nan,
            dic_update_from=dic_config_all_variables_2D_nan,
            bol_create_new_key=False,
            bol_replace_dict=False,
        )
        pass

    def _update_key_from_other_dict(self,
        dic_update_to=None,
        dic_update_from=None,
        bol_create_new_key=False,
        bol_replace_dict=False,
        **kwargs
    ):
        """把dic_update_from中的key-value更新到dic_update_to中

        Args
        ----
        dic_update_to : dict
            被更新的字典
        dic_update_from : dict
            更新的字典的信息来源
        bol_create_new_key : bool
            如果为True, 则如果dic_update_from中的某个key在dic_update_to中不存在, 则创建新的key
            如果为False, 则多出的新key会报错
        bol_replace_dict : bool
            如果为True, 则用dic_update_from直接替换dic_update_to
            如果为False, 则更新key而非替换

        """
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
                        raise ValueError(
                            f'输出字典中有要更新字典中不带有的新key, 输入key为{key_from}\n'+\
                            '但设置bol_create_new_key为False, 不允许创建新的key'
                        )
                    elif key_from in dic_update_to:
                        # 创建新的key / 更新已有的key
                        dic_update_to.update({key_from : val_from})
        return
    
    def get_dic_key(self, name_var:str, name_forced=None):
        """ 提供变量名, 返回原始数据中的key名

        此变量和GeneralGTGTransformer中的dic_config_map_name_variables中定义对应

        Args
        ----
        name_var : str
            变量名, 对应此变量和GeneralGTGTransformer中的dic_config_map_name_variables中的key
            此key用于统一程序中使用参数名, 并与原始数据中的变量名进行解耦
        name_forced : str
            如果不为None, name_forced, 否则返回name_var对应的key
        """
        if name_forced is not None:
            return name_forced
        else:
            return self._dic_config_map_name_variables[name_var]

    def get_dic_config_all_variables_2D_nan_with_mapped_name(self,
        dic_config_all_variables_2D_nan=None
    ):
        """ 返回一个字典, 没项都是 dic_config_all_variables_2D_nan中存在的
        但是key是对应的原始数据中的key, 即定义在dic_config_map_name_variables中的key
        """
        if dic_config_all_variables_2D_nan is None:
            dic_config_all_variables_2D_nan = self._dic_config_all_variables_2D_nan
        dic_config_all_variables_2D_nan_with_mapped_name = {
            self.get_dic_key(name_var=name_key_var) : val_var
            for name_key_var, val_var in dic_config_all_variables_2D_nan.items()
        }
        return dic_config_all_variables_2D_nan_with_mapped_name

    def fit(self, X, y):
        return

    def transform(self, X):
        return