#!/usr/bin/env python3

from sklearn.base import BaseEstimator, TransformerMixin

import pandas as pd
import numpy as np

import copy

import time

import re

from code_source.preprocessing.preprocessing_RAW.generalrawtransformer import GeneralRAWTransformer

class HandleColumnTransformer(BaseEstimator, TransformerMixin, GeneralRAWTransformer):
    """对raw数据的Dataframe的列进行处理的transformer

    *功能:
        * 1.

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
        """ dic_config_handle_missing_values: 定义对每一列如何处理缺失值的配置字典
            
        Args
        ----
        art_execution : str
            执行的方法的类型, 可选值有: 类的方法'method', 函数'function', 和df函数'df_function'
            * 类的方法'method': 即对于列对象pd.series取得其方法名, 并执行该方法
                getattr(列对象, name_execution)(**kwargs)
            * 函数'function': 即对于列对象pd.series执行指定的函数
                * 函数(列对象, **kwargs)
            * df函数'df-function': 即对于整个df执行指定的函数
                * df函数(列名, df, **kwargs)
                * 用于处理需要从整个df中获取信息的列
        name_execution : str
            执行的方法/函数 的名称, 对应到dic_config_name_execution_available中的key
        kwargs : dict
            执行方法/函数的参数字典
        dtype : str
            (可选) 在处理缺失值后, 对列进行强制类型转换
            为None或不给出时不进行类型转换
        """
        super()._init_dic_config(dic_config=dic_config, **kwargs)
        dic_config_default = {
            'name_transformer' : 'HandleColumnTransformer',
            'str_format_timestamp_slice_slice' : r'%Y-%m-%d %H:%M:%S.%f',
            'str_format_timestamp_timeblock' : r'%Y-%m-%d %H:%M:%S',
            'dic_config_art_execution_available' : {
                'pass' : self._handle_col_pass,
                'method' : self._handle_col_art_method,
                'function' : self._handle_col_art_function,
                'df_function' : self._handle_col_art_df_function,
            },
            'dic_config_name_execution_available' : {
                'fillna' : 'fillna',
                'check_no_nan' : self._check_no_none_value_in_column,
                'convert_to_index' : self._convert_to_index,
                'convert_to_timestamp' : self._convert_to_timestamp,
            },
            'dic_config_original_name_col' : {
                # **timeblock变量** 
                'str_key_Gen_ts_Timestamp_belong_timeblock' : 'DateTime',
                # **slice变量** 
                'str_key_RAW_flt_Power_elec_windpv_slice' : 'WS_Power[MW]',
                'str_key_RAW_flt_Power_elec_demand_slice' : 'BaseLoad[MW]',               
                'str_key_RAW_flt_Power_elec_residual_slice' : 'DeltaPower[MW]',
                'str_key_RAW_flt_Power_elec_waste_slice' : 'Power_Surplus[MW]',            
                'str_key_RAW_flt_Temperature_outdoor_C_slice' : 'Temperature[℃]',
            },
            'dic_config_handle_col_value' : {
                # **timeblock变量** 
                '把timeblock列转为时间戳的形式,并进行时间格式转化': {
                    'priority' : 1,
                    'str_name_col' : 'str_key_Gen_ts_Timestamp_belong_timeblock',
                    'art_execution' : 'function',
                    'name_execution' : 'convert_to_timestamp',
                },
                '把timeblock列转为index': {
                    'priority' : 2,
                    'str_name_col' : 'str_key_Gen_ts_Timestamp_belong_timeblock',
                    'art_execution' : 'function',
                    'name_execution' : 'convert_to_index',
                    'kwargs' : {'drop': False, 'inplace':True},
                },
                # **slice变量** 
                'str_key_RAW_flt_Power_elec_windpv_slice' : {
                    'priority' : 3,
                    'art_execution' : 'function',
                    'name_execution' : 'check_no_nan',
                },
                'str_key_RAW_flt_Power_elec_demand_slice' : {
                    'priority' : 3,
                    'art_execution' : 'function',
                    'name_execution' : 'check_no_nan',
                },        
                'str_key_RAW_flt_Power_elec_residual_slice' : {
                    'priority' : 3,
                    'art_execution' : 'function',
                    'name_execution' : 'check_no_nan',
                },
                'str_key_RAW_flt_Power_elec_waste_slice' : {
                    'priority' : 3,
                    'art_execution' : 'function',
                    'name_execution' : 'check_no_nan',
                },
                'str_key_RAW_flt_Temperature_outdoor_C_slice' : {
                    'priority' : 3,
                    'art_execution' : 'function',
                    'name_execution' : 'check_no_nan',
                },
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

    def _rename_col(self,
        df_RAW,
        **kwargs  
    ):
        """ 重命名列
        """
        dic_config_original_name_col = kwargs['dic_config_original_name_col']
        dic_col_name_df = {
            str_name_col_unstriped.strip() : str_name_col_unstriped
            for str_name_col_unstriped in df_RAW.columns
        }
        for str_key_col in dic_config_original_name_col.keys():
            str_name_col_original = dic_config_original_name_col.get(str_key_col, None)
            str_name_col_new = self.get_dic_key(str_key_col)
            # 找到带空格的df中的列名
            if str_name_col_original not in dic_col_name_df:
                raise ValueError(
                    "错误: 重命名列时出错, df中未找到对应的列名\n",
                    "str_name_col_original: {}\n".format(str_name_col_original),
                    "dic_col_name_df: {}\n".format(dic_col_name_df)
                )
            else:
                str_name_col_in_df = dic_col_name_df[str_name_col_original]
            # 重命名列
            if str_name_col_original and str_name_col_new:
                df_RAW.rename(columns={str_name_col_in_df: str_name_col_new}, inplace=True)
            else:
                raise ValueError(
                    "错误: 重命名列时出错, 未找到对应的列名\n",
                    "str_name_col_original: {}\n".format(str_name_col_original),
                    "str_name_col_new: {}\n".format(str_name_col_new)
                )
        return

    def _convert_to_timestamp(self,
        df_RAW,
        str_name_col_to_handle,
        str_format_timestamp=None,
        **kwargs              
    ):
        """ 把当前列转换为时间戳, 并考虑时间格式转化
        """
        # 读取时间格式
        if str_format_timestamp is None:
            str_format_timestamp = kwargs['str_format_timestamp_timeblock']
        # 转换时间戳
        df_RAW.loc[:, str_name_col_to_handle] = pd.to_datetime(
            df_RAW.loc[:, str_name_col_to_handle],
            format=str_format_timestamp,
        )
        return

    def _convert_to_index(self,
        df_RAW,
        str_name_col_to_handle,
        drop=False,
        inplace=True,
        append=False,
        **kwargs
    ):
        """ 把当前列转换为索引列
        """
        df_RAW.set_index(
            keys=str_name_col_to_handle,
            drop=drop,
            inplace=inplace,
            append=append,
        )
        return

    def _check_no_none_value_in_column(self,
        df_RAW,
        str_name_col_to_handle,
        **kwargs
    ):
        """ 检查列中是否有缺失值, 是则报错, 否则不返回
        """
        series_to_handle = df_RAW.loc[:, str_name_col_to_handle]
        if series_to_handle.isna().any():
            index_isna = df_RAW.loc[
                df_RAW.loc[:, str_name_col_to_handle].isna()
            ].index
            raise ValueError(
                "错误: 列{}中存在缺失值".format(str_name_col_to_handle),
                "以下时间戳的数据存在缺失值: \n{}".format(index_isna)
            )
        return

    def _handle_col_pass(self,
        **kwargs
    ):
        """跳过处理缺失值
        """
        return

    def _handle_col_art_method(self,
        df_RAW,
        str_name_col_to_handle,
        obj_func_execution,
        dic_kwargs_execution,
        str_dtype=None,
        bol_inplace_execution=True,
        **kwargs    
    ):
        """ 处理缺失值中, 当art_execution为method时的处理过程
        """
        series_to_handle = df_RAW.loc[:, str_name_col_to_handle]
        obj_class_method = getattr(series_to_handle, obj_func_execution)
        res_execution = obj_class_method(
            **dic_kwargs_execution
        )
        # 处理返回结果
        if not bol_inplace_execution:
            # 如函数/方法 并非自动的inplace, 则进行赋值操作
            df_RAW.loc[:, str_name_col_to_handle] = res_execution
        # 进行类型转换
        if str_dtype is not None:
            df_RAW.loc[:, str_name_col_to_handle] = series_to_handle.astype(str_dtype)

        return
    
    def _handle_col_art_function(self,
        df_RAW,
        str_name_col_to_handle,
        obj_func_execution,
        dic_kwargs_execution,
        str_dtype=None,
        bol_inplace_execution=True,
        **kwargs    
    ):
        """ 处理缺失值中, 当art_execution为function时的处理过程
        """
        series_to_handle = df_RAW.loc[:, str_name_col_to_handle]
        obj_function = obj_func_execution
        res_execution = obj_function(
            df_RAW,
            str_name_col_to_handle,
            **dic_kwargs_execution,
            **kwargs
        )
        # 处理返回结果
        if not bol_inplace_execution:
            # 如函数/方法 并非自动的inplace, 则进行赋值操作
            df_RAW.loc[:, str_name_col_to_handle] = res_execution
        # 进行类型转换
        if str_dtype is not None:
            df_RAW.loc[:, str_name_col_to_handle] = series_to_handle.astype(str_dtype)
        return
    
    def _handle_col_art_df_function(self,
        df_RAW,
        str_name_col_to_handle,
        obj_func_execution,
        dic_kwargs_execution,
        str_dtype=None,
        bol_inplace_execution=True,
        **kwargs    
    ):
        """ 处理缺失值中, 当art_execution为df_function时的处理过程
        """
        series_to_handle = df_RAW.loc[:, str_name_col_to_handle]
        obj_df_function = obj_func_execution
        res_execution = obj_df_function(
            df_RAW,
            str_name_col_to_handle,
            **dic_kwargs_execution,
            **kwargs
        )
        # 处理返回结果
        if not bol_inplace_execution:
            # 如函数/方法 并非自动的inplace, 则进行赋值操作
            df_RAW.loc[:, str_name_col_to_handle] = res_execution
        # 进行类型转换
        if str_dtype is not None:
            df_RAW.loc[:, str_name_col_to_handle] = series_to_handle.astype(str_dtype)
        return

    def _handle_col(self,
        df_RAW,
        dic_config_art_execution_available=None,
        dic_config_name_execution_available=None,
        dic_config_handle_col_value=None,
        **kwargs
    ):
        """对的Dataframe处理缺失值

        处理方法按照dic_config_handle_missing_values中的配置字典进行
        """
        time_begin = time.time()
        # 读取config参数
        kwargs.update(self._dic_config)
        str_name_transformer = kwargs.get('name_transformer', '')
        dic_config_art_execution_available =  self._get_param_with_forced(
            name_param_in_config='dic_config_art_execution_available', val_param=dic_config_art_execution_available
        )
        dic_config_name_execution_available =  self._get_param_with_forced(
            name_param_in_config='dic_config_name_execution_available', val_param=dic_config_name_execution_available
        )
        dic_config_handle_col_value =  self._get_param_with_forced(
            name_param_in_config='dic_config_handle_col_value', val_param=dic_config_handle_col_value
        )
        # 更改列名
        self._rename_col(df_RAW, **kwargs)

        # 处理列的优先级
        lst_name_procedure_handle = dic_config_handle_col_value.keys()
        lst_name_procedure_handle = sorted(
            lst_name_procedure_handle,
            key=lambda name_procedure: dic_config_handle_col_value[name_procedure].get('priority', 99)
        )
        # 
        for str_name_key  in lst_name_procedure_handle:
            dic_col_handle = dic_config_handle_col_value[str_name_key]
            # 读取处理信息
            str_var_col_to_handle = dic_col_handle.get('str_name_col', str_name_key)
            str_name_col_to_handle = self.get_dic_key(str_var_col_to_handle)
            str_art_execution = dic_col_handle['art_execution']
            str_name_execution = dic_col_handle.get('name_execution', None)
            obj_art_execution = dic_config_art_execution_available[str_art_execution]
            obj_func_execution = dic_config_name_execution_available.get(str_name_execution, None)
            dic_kwargs_execution = dic_col_handle.get('kwargs', {})
            str_dtype = dic_col_handle.get('dtype', None)

            try:
                obj_art_execution(
                    df_RAW=df_RAW,
                    str_name_col_to_handle=str_name_col_to_handle,
                    obj_func_execution=obj_func_execution,
                    dic_kwargs_execution=dic_kwargs_execution,
                    str_dtype=str_dtype,
                    **kwargs
                )
            except Exception as err:
                raise ValueError(
                    "错误: 处理列{}时出错, 处理执行项目: {}, 错误信息:{}".format(
                        str_name_col_to_handle, str_name_execution, err)
                )
        # 打印处理完成信息
        time_end = time.time()
        print('TF名: {}, 处理完成, 耗时: {:.2f}秒'.format(
            str_name_transformer, time_end-time_begin))
        return df_RAW

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # 1.读取数据
        df_RAW = self.read_input_transformer(X)
        # 2.处理数据
        bol_copy_input = self._dic_config.get('bol_copy_input', True)
        if bol_copy_input:
            df_RAW = df_RAW.copy(deep=True)
        df_RAW = self._handle_col(df_RAW)
        # 3.写入数据
        obj_return = self.save_output_transformer(X, df_RAW)
        return obj_return
    