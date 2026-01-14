#!/usr/bin/env python3

import sys

from sklearn.base import BaseEstimator, TransformerMixin

import pandas as pd
import numpy as np

import copy

import time

import re

class HandleDFProcedureTransformer(BaseEstimator, TransformerMixin):
    """对DataFrame按照定义的procedure处理数据的Transformer

    *功能:
        * 1.

    """
    def __init__(self,
        **kwargs
    ) -> None:
        super().__init__()
        pass

    def _compare_float_and_raise_error_on_series(
        df_case,
        str_name_col,
        float_value_compare,
        str_logical_expression_allowed='==',
        str_bol_logical_expression_series='any',
        str_error_message_1st_line='在x条件下, 输入的col数据必须大于{}',
        str_error_message_2nd_line='错误的数据为: ',
        **kwargs
    ):
        """ 在df上选取列, 并拿列与一个float值进行比较, 如果不符合要求, 则抛出错误
        """
        series_to_compare =\
            df_case.loc[:, str_name_col]
        series_bol_res_allowed =\
            eval(
                'series_to_compare.loc[:, str_name_col]' + str_logical_expression_allowed + str(float_value_compare),
                {
                    'series_to_compare' : series_to_compare,
                    'str_name_col' : str_name_col,
                }
            )
        bol_res_logical_series = getattr(~series_bol_res_allowed, str_bol_logical_expression_series)()
        if bol_res_logical_series:
            raise ValueError(
                str_error_message_1st_line.format(float_value_compare),
                str_error_message_2nd_line, series_to_compare.loc[
                    ~series_bol_res_allowed, str_name_col],
            )
        return
    
    def _compare_and_raise_error_of_two_series(
        df_case,
        str_name_col_left,
        str_name_col_right,
        str_logical_expression_allowed='==',
        str_bol_logical_expression_series='any',
        str_error_message_1st_line='左右比较不正确',
        str_error_message_2nd_line='错误的数据为: ',      
        **kwargs
    ):
        """ 在df上选取两列, 比较他们的值, 如果不符合要求, 则抛出错误
        """
        series_to_compare_left =\
            df_case.loc[:, str_name_col_left]
        series_to_compare_right =\
            df_case.loc[:, str_name_col_right]       
        series_bol_res_allowed =\
            eval(
                'series_to_compare_left.loc[:, str_name_col_left]' +\
                    str_logical_expression_allowed +\
                    'series_to_compare_right.loc[:, str_name_col_right]',
                {
                    'series_to_compare_left' : series_to_compare_left,
                    'str_name_col_left' : str_name_col_left,
                    'series_to_compare_right' : series_to_compare_right,
                    'str_name_col_right' : str_name_col_right,
                }
            )
        bol_res_logical_series = getattr(~series_bol_res_allowed, str_bol_logical_expression_series)()
        if bol_res_logical_series:
            raise ValueError(
                str_error_message_1st_line,
                str_error_message_2nd_line, df_case.loc[
                    ~series_bol_res_allowed,
                    [str_name_col_left, str_name_col_right]],
            )
        return

    def _func_df_method_call_on_column(self,
        df_data,
        str_name_method_call,
        lst_str_key_col_data_from,
        str_key_col_res_write_to,
        dtype=None,
        func_get_dic_key=None,
        **kwargs
    ):
        """按照给定的列名列表, 进行df切片, 并调用对应的方法mehod, 结果存入指定列

        Args:
        ----
        df_BG : pd.DataFrame
            BG的数据
        str_name_method_groupby : str
            聚合后计算的方法名
        lst_str_key_col_data_from : str
            要总和的数据来源多列名
        str_key_col_res_write_to : str
            计算结果保存的列key名
        """
        # 解析参数名到列名
        str_name_col_res_write_to = func_get_dic_key(str_key_col_res_write_to)
        # 初始化结果列
        df_data.loc[:, str_name_col_res_write_to] = 0.0
        # 提取列名
        lst_str_name_col_data_from = [
            func_get_dic_key(str_key_col_data_from)
            for str_key_col_data_from in lst_str_key_col_data_from
        ]
        # 进行提取df处理
        df_handle = df_data.loc[:, lst_str_name_col_data_from]
        df_data.loc[:, str_name_col_res_write_to] = getattr(df_handle, str_name_method_call)(axis=1)
        # 更改数据类型
        if dtype is not None:
            df_data.loc[:, str_name_col_res_write_to] =\
                df_data.loc[:, str_name_col_res_write_to].astype(dtype)
        return

    def _func_df_groupby_timeblock_groupby_single_procedure(self,
        obj_DFGroupBy,
        str_name_procedure,
        str_name_method_subprocedure,
        str_key_col_data_from,
        str_key_col_res_to,
        str_key_subprocedure_str_name_col_from='str_name_col_from',
        str_key_subprocedure_str_name_col_to='str_name_col_to',
        str_key_subprocedure_res_method_groupby='res_method_groupby',
        str_key_subprocedure_time_consumed='time_consumed',
        func_get_dic_key=None,
        **kwargs):
        """对按照timeblock进行groupby后的DataFrameGroupBy对象, 执行单个subprocedure, 调用对应的计算函数, 结果保存到字典返回

        Args:
        ----
        obj_group : DataFrameGroupBy
            groupby后的对象
        str_name_procedure : str
            子进程的名字
        str_name_method_subprocedure : str
            聚合后计算的subprocedure方法名
        str_key_col_data_from : str
            要总和的数据来源多列key名
        str_key_col_res_to : str
            计算结果保存的列key名

        Return
        ------
        dic_res_groupby_single_procedure : {str : object}
            返回一个字典, 记录单个group单个procedure的各种处理结果
        """
        # 记录开始时间
        time_begin = time.time()
        # 解析参数名到列名
        str_name_col_from = func_get_dic_key(str_key_col_data_from)
        str_name_col_to = func_get_dic_key(str_key_col_res_to)

        # 计算结果
        try:
            obj_res_method_groupby =\
                getattr(obj_DFGroupBy, str_name_method_subprocedure)()
        except Exception as err:
            raise ValueError(
                "错误: 处理procedure {}时出错, 错误信息:{}".format(str_name_procedure, err)
            )
        # 记录在df_BG中
        dic_res_groupby_single_procedure = {
            str_key_subprocedure_str_name_col_from : str_name_col_from,
            str_key_subprocedure_str_name_col_to : str_name_col_to,
            str_key_subprocedure_res_method_groupby : obj_res_method_groupby,
            str_key_subprocedure_time_consumed : time.time() - time_begin
        }
        return dic_res_groupby_single_procedure     

    def _func_df_groupby_timeblock_groupby_multiple_procedures(self,
        obj_DFGroupBy,
        dic_subprocedures,
        lst_name_subprocedures_regards_priority,
        str_key_subprocedure_kwargs='kwargs',
        str_key_subprocedure_name_method_groupby='str_name_method_groupby',
        str_key_subprocedure_str_name_col_from='str_name_col_from',
        str_key_subprocedure_str_name_col_to='str_name_col_to',
        **kwargs):
        """对groupby的对象, 执行单个subprocedure, 调用对应的计算函数, 结果保存到字典返回

        Args:
        ----
        str_name_group : str
            group的名字
        dic_group_single : pd.DataFrame
            单一的group的DataFrame
        lst_name_subprocedures_regards_priority : [str]
            要执行子进程的名字, 已经按照优先级排序
        """
        # 初始化
        dic_res_groupby_multiple_procedures = {}
        # 遍历所有的subprocedure
        for str_name_procedure in lst_name_subprocedures_regards_priority:
            # 解析参数名到列名
            str_name_method_subprocedure = dic_subprocedures[str_name_procedure][str_key_subprocedure_kwargs][
                str_key_subprocedure_name_method_groupby]
            str_key_col_data_from = dic_subprocedures[str_name_procedure][str_key_subprocedure_kwargs][
                str_key_subprocedure_str_name_col_from]
            str_key_col_res_to = dic_subprocedures[str_name_procedure][str_key_subprocedure_kwargs][
                str_key_subprocedure_str_name_col_to]
            # 计算结果
            dic_res_groupby_single_procedure = self._func_df_groupby_timeblock_groupby_single_procedure(
                obj_DFGroupBy=obj_DFGroupBy,
                str_name_procedure=str_name_procedure,
                str_name_method_subprocedure=str_name_method_subprocedure,
                str_key_col_data_from=str_key_col_data_from,
                str_key_col_res_to=str_key_col_res_to,
                **kwargs)
            # 记录单组的各个过程
            dic_res_groupby_multiple_procedures[str_name_procedure] = {}
            dic_res_groupby_multiple_procedures[str_name_procedure].update(
                dic_res_groupby_single_procedure)
        return dic_res_groupby_multiple_procedures

    def _get_relevant_col_name_in_dic_subprocedure(self,
        dic_subprocedures,
        str_key_subprocedure_kwargs='kwargs',
        str_key_to_get=None,
        func_get_dic_key=None,
        bol_return_set=False,
    ):
        """ 从subprocedure的字典中提取相关的列名, 返回列表list
        """
        lst_str_name_col_to_get = [
            func_get_dic_key(
                dic_subprocedures[str_name_subprocedure][str_key_subprocedure_kwargs][str_key_to_get])
            for str_name_subprocedure in dic_subprocedures.keys()]
        if bol_return_set:
            obj_return = set(lst_str_name_col_to_get)
        else:
            obj_return = lst_str_name_col_to_get
        return obj_return

    def _groupby_energy_timeblock(self,
        df_data,
        str_name_method_groupby,
        str_key_col_data_from,
        str_key_col_res_to,
        str_key_col_belong_timeblock,
        str_name_fuel=None,
        **kwargs):
        """按同timeblock时间, 聚合对应列的数据, 并调用对应的计算函数, 结果保存到指定列中

        Args:
        ----
        df_data : pd.DataFrame
            df的数据
        str_name_method_groupby : str
            聚合后计算的方法名
        str_key_col_data_from : str
            要总和的数据来源列名
        str_key_col_res_to : str
            计算结果保存的列名
        str_key_col_belong_timeblock : str
            数据所属的时间块列名, 此列用于判断数据是否属于同一时间块
        str_name_fuel : str
            燃料名, 用于提取不同燃料对应的变量名
        """
        # 读取函数
        func_get_dic_key = kwargs['func_get_dic_key']

        # 解析参数名到列名
        str_name_col_data_from = func_get_dic_key(
            str_key_col_data_from, str_name_fuel=str_name_fuel)
        str_name_col_res_to = func_get_dic_key(
            str_key_col_res_to, str_name_fuel=str_name_fuel)
        str_name_col_belong_timeblock = func_get_dic_key(
            str_key_col_belong_timeblock, str_name_fuel=str_name_fuel)
        # 提取部分columns
        df_sliced = df_data.loc[
            :, [
                str_name_col_data_from,
                str_name_col_res_to,
                str_name_col_belong_timeblock
            ]
        ]
        # 分组后处理
        obj_group = df_sliced.groupby(by=str_name_col_belong_timeblock)
        for name_group in obj_group.groups:
            df_group_single = obj_group.get_group(name_group)
            index_group_single = df_group_single.index
            # 计算结果
            res_method_groupby = getattr(df_group_single[str_name_col_data_from], str_name_method_groupby)()
            df_data.loc[index_group_single, str_name_col_res_to] = res_method_groupby
        return

    def _func_df_groupby_timeblock_with_subprocedures(self,
        df_data,
        str_key_col_groupby = None,
        dic_subprocedures ={},
        str_name_priority = 'priority',
        str_key_subprocedure_str_name_col_from='str_name_col_from',
        str_key_subprocedure_str_name_col_to='str_name_col_to',
        str_key_subprocedure_res_method_groupby='res_method_groupby',
        str_key_subprocedure_time_consumed='time_consumed',
        func_get_dic_key=None,
        **kwargs):
        """按同timeblock时间, 使用同groupby列名, 并处理多个过程

        Args:
        ----
        df_BG : pd.DataFrame
            BG的数据
        str_key_col_groupby : str
            用于groupby的列名
        dic_subprocedures : {str : dict}
            用于处理同groupby下多个子过程的字典, key为子过程的名字, value为子过程的参数字典
        """
        # 起始时间
        time_start = time.time()
        # 解析groupby列名
        str_name_col_groupby = func_get_dic_key(str_key_col_groupby)

        # 提取所涉及的列名
        lst_str_key_col_data_relevant = self._get_relevant_col_name_in_dic_subprocedure(
            dic_subprocedures=dic_subprocedures,
            str_key_to_get=str_key_subprocedure_str_name_col_from,
            func_get_dic_key=func_get_dic_key,
            **kwargs
        )
        lst_str_key_col_data_relevant.append(str_name_col_groupby)
        # 提取涉及的列名, 形成新的DataFrame
        df_sliced = df_data.loc[:, lst_str_key_col_data_relevant]
        # 对subprocedures进行排序处理
        lst_name_subprocedures_regards_priority = list(dic_subprocedures.keys())
        lst_name_subprocedures_regards_priority = sorted(
            lst_name_subprocedures_regards_priority,
            key=lambda str_name_sp: dic_subprocedures[str_name_sp][str_name_priority]
        )
        # 分组后处理
        dic_time_consumed_multiple_procedure = {
            str_name_procedure : 0.0
            for str_name_procedure in lst_name_subprocedures_regards_priority
        }
        obj_DFGroupBy = df_sliced.groupby(by=str_name_col_groupby)
        # 对组进行聚合处理, 计算单组多子procudure的结果
        dic_res_groupby_multiple_procedures = self._func_df_groupby_timeblock_groupby_multiple_procedures(
            obj_DFGroupBy=obj_DFGroupBy,
            dic_subprocedures=dic_subprocedures,
            lst_name_subprocedures_regards_priority=lst_name_subprocedures_regards_priority,
            func_get_dic_key=func_get_dic_key,
            **kwargs
        )
        # 对groupby结果进行融合
        for str_name_procedure in dic_res_groupby_multiple_procedures.keys():
            str_name_col_from =\
                dic_res_groupby_multiple_procedures[str_name_procedure][str_key_subprocedure_str_name_col_from]
            str_name_col_to =\
                dic_res_groupby_multiple_procedures[str_name_procedure][str_key_subprocedure_str_name_col_to]
            df_res_method_groupby =\
                dic_res_groupby_multiple_procedures[str_name_procedure][str_key_subprocedure_res_method_groupby]
            flt_time_consumed =\
                dic_res_groupby_multiple_procedures[str_name_procedure][str_key_subprocedure_time_consumed]
            # 更改聚合后的列名到存储的列名
            df_res_method_groupby.rename(
                columns={
                    str_name_col_from : str_name_col_to
                }, inplace=True
            )
            # 与原始数据进行融合
            df_res_merged = df_data.loc[:, [str_name_col_to, str_name_col_groupby]]
            df_groupby_col_data = df_res_method_groupby.loc[:, [str_name_col_to]]
            df_res_merged = df_res_merged.reset_index(names='index').merge(
                df_groupby_col_data,
                left_on=str_name_col_groupby,
                right_index=True,
                how='left',
                suffixes=("_old", "")
            ).set_index('index')
            # 更新原始数据
            df_data.loc[:, str_name_col_to] = df_res_merged.loc[:, str_name_col_to].values
            # 更新时间
            dic_time_consumed_multiple_procedure[str_name_procedure] += flt_time_consumed

        # 打印耗时
        time_end = time.time()
        flt_time_consumed_total = time_end - time_start
        flt_time_consumed_overhead = flt_time_consumed_total
        for str_name_procedure in dic_time_consumed_multiple_procedure.keys():
            print('\t\t#### Subprocedure: {} 处理完成, 耗时: {:.2f}s'.format(
                str_name_procedure, dic_time_consumed_multiple_procedure[str_name_procedure]))
            flt_time_consumed_overhead -= dic_time_consumed_multiple_procedure[str_name_procedure]
        print('\t\t#### 除去各分项Subprocedure耗时外, 此Procedure的Overhead: {:.2f}s'.format(flt_time_consumed_overhead))
        return


    def _func_df_rename_col(self,
        df_data,
        bol_strip_name_col=True,
        dic_config_map_key_to_name_col=None,
        func_get_dic_key=None,
        **kwargs  
    ):
        """ 对DataFrame重命名列

        * dic_config_map_key_to_name_col: 从变量名映射到df中的列名
        * 
        """
        # 是否去除原始df中的列名的空格, 并建立 stripped的映射表
        if bol_strip_name_col:
            dic_name_col_map_striped = {
                str_name_col_unstriped.strip() : str_name_col_unstriped
                for str_name_col_unstriped in df_data.columns
            }
        else:
            dic_name_col_map_striped = {
                str_name_col_unstriped : str_name_col_unstriped
                for str_name_col_unstriped in df_data.columns
            }
        # 重命名列
        for str_key_col in dic_config_map_key_to_name_col.keys():
            str_name_col_original_striped = dic_config_map_key_to_name_col.get(str_key_col, None)
            str_name_col_new = func_get_dic_key(str_key_col)
            # 找到带空格的df中的列名
            if str_name_col_original_striped not in dic_name_col_map_striped:
                raise ValueError(
                    "错误: 重命名列时出错, df中未找到对应的列名\n",
                    "str_name_col_original: {}\n".format(str_name_col_original_striped),
                    "dic_col_name_df: {}\n".format(dic_name_col_map_striped)
                )
            else:
                str_name_col_original_unstriped = dic_name_col_map_striped[str_name_col_original_striped]
            # 重命名列
            if str_name_col_original_striped and str_name_col_new:
                df_data.rename(columns={str_name_col_original_unstriped: str_name_col_new}, inplace=True)
            else:
                raise ValueError(
                    "错误: 重命名列时出错, 未找到对应的列名\n",
                    "str_name_col_original: {}\n".format(str_name_col_original_unstriped),
                    "str_name_col_new: {}\n".format(str_name_col_new)
                )
        return

    def _func_df_check_no_none_value_in_column(self,
        df_data,
        str_key_name_col,
        func_get_dic_key=None,
        **kwargs
    ):
        """ 检查列中是否有缺失值, 是则报错, 否则不返回
        """
        # 解析参数名到列名
        str_name_col = func_get_dic_key(str_key_name_col)
        # 检查缺失值
        series_to_handle = df_data.loc[:, str_name_col]
        if series_to_handle.isna().any():
            index_isna = df_data.loc[
                df_data.loc[:, str_name_col].isna()
            ].index
            raise ValueError(
                "错误: 列{}中存在缺失值".format(str_name_col),
                "以下时间戳的数据存在缺失值: \n{}".format(index_isna)
            )
        return

    def _func_df_convert_to_timestamp(self,
        df_data,
        str_key_name_col,
        str_format_timestamp=None,
        func_get_dic_key=None,
        **kwargs              
    ):
        """ 把当前列转换为时间戳, 并考虑时间格式转化
        """
        # 解析参数名到列名
        str_name_col = func_get_dic_key(str_key_name_col)
        # 读取时间格式
        if str_format_timestamp is None:
            str_format_timestamp = kwargs['str_format_timestamp_timeblock']
        # 转换时间戳
        df_data.loc[:, str_name_col] = pd.to_datetime(
            df_data.loc[:, str_name_col],
            format=str_format_timestamp,
        )
        return

    def _func_df_convert_to_index(self,
        df_data,
        str_key_name_col,
        drop=False,
        inplace=True,
        append=False, 
        func_get_dic_key=None,
        **kwargs
    ):
        """ 把当前列转换为索引列
        """
        # 解析参数名到列名
        str_name_col = func_get_dic_key(str_key_name_col)
        # 设置索引
        df_data.set_index(
            keys=str_name_col,
            drop=drop,
            inplace=inplace,
            append=append,
        )
        return

    def _handle_procedure_pass(self,
        **kwargs
    ):
        """跳过处理缺失值
        """
        return

    def _handle_procedure_art_method(self,
        df_data,
        str_key_name_col,
        obj_func_execution,
        dic_kwargs_execution,
        str_dtype=None,
        inplace=True,
        func_get_dic_key=None,
        **kwargs    
    ):
        """ 处理缺失值中, 当art_execution为method时的处理过程
        """
        # 解析参数名到列名
        str_name_col = func_get_dic_key(str_key_name_col)
        # 读取slice
        series_to_handle = df_data.loc[:, str_name_col]
        obj_class_method = getattr(series_to_handle, obj_func_execution)
        # 加入inplace
        if inplace:
            dic_kwargs_execution['inplace'] = True
        res_execution = obj_class_method(
            **dic_kwargs_execution
        )
        # 处理返回结果
        if not inplace:
            # 如函数/方法 并非自动的inplace, 则进行赋值操作
            df_data.loc[:, str_name_col] = res_execution
        # 进行类型转换
        if str_dtype is not None:
            df_data.loc[:, str_name_col] = series_to_handle.astype(str_dtype)

        return

    def _handle_procedure_art_function(self,
        str_name_procedure,
        df_data,
        obj_func_execution,
        dic_kwargs_execution,
        dic_other_kwargs={},
        **kwargs    
    ):
        """ 处理缺失值中, 当art_execution为function时的处理过程
        """
        time_begin = time.time()
        # 处理过程
        obj_function = obj_func_execution
        obj_function(
            df_data,
            **dic_kwargs_execution,
            **dic_other_kwargs,
            **kwargs
        )
        # 打印耗时
        time_end = time.time()
        print('\t### Procedure: {} 处理完成, 耗时: {:.2f}s'.format(
            str_name_procedure, time_end - time_begin))
        return

    def _handle_procedure_without_fuel(self,
        df_data,
        dic_config_art_execution_available=None,
        dic_config_name_execution_available=None,
        dic_config_procedures=None,
        dic_config=None,
        func_get_dic_key=None,
        **kwargs
    ):
        """对Dataframe按照定义的procedure处理数据, 处理不带燃料的数据

        处理方法按照dic_config_handle_procedure中的配置字典进行
        """
        time_begin = time.time()
        # 传递config参数
        kwargs.update(dic_config)
        # 读取config参数
        str_name_transformer = kwargs.get('str_name_transformer', '缺失的Transformer名')
        # 按照优先级排序, 小的优先级先处理
        lst_name_procudure_sorted = sorted(
            dic_config_procedures.keys(),
            key=lambda name_procedure: dic_config_procedures[name_procedure].get('priority', sys.maxsize),
            reverse=False)
        # 处理
        print('## Pipeline: {} 开始执行处理procedure'.format(str_name_transformer))
        for str_name_procedure in lst_name_procudure_sorted:
            time_start = time.time()
            dic_single_procedure = copy.deepcopy(dic_config_procedures[str_name_procedure])
            # 读取处理信息
            str_key_name_col = dic_single_procedure.pop('str_key_name_col', str_name_procedure)
            str_art_execution = dic_single_procedure.pop('art_execution')
            str_name_execution = dic_single_procedure.pop('name_execution', None)
            obj_art_execution = dic_config_art_execution_available[str_art_execution]
            obj_func_execution = dic_config_name_execution_available.get(str_name_execution, None)
            dic_kwargs_execution = dic_single_procedure.pop('kwargs', {})
            dic_other_kwargs = dic_single_procedure

            try:
                obj_art_execution(
                    str_name_procedure=str_name_procedure,
                    str_key_name_col=str_key_name_col,
                    df_data=df_data,
                    obj_func_execution=obj_func_execution,
                    dic_kwargs_execution=dic_kwargs_execution,
                    dic_other_kwargs=dic_other_kwargs,
                    func_get_dic_key=func_get_dic_key,
                    **kwargs
                )
            except Exception as err:
                raise ValueError(
                    "错误: 处理procedure {}的缺失值时出错, 错误信息:{}".format(str_name_procedure, err)
                )
        # 打印处理完成信息
        time_end = time.time()
        print('TF名: {}, 处理完成, 耗时: {:.2f}秒'.format(
            str_name_transformer, time_end-time_begin))
        return df_data

    def _handle_procedure_with_fuel(self,
        df_data,
        dic_config_art_execution_available=None,
        dic_config_name_execution_available=None,
        dic_name_fuel_to_handle=None,
        dic_config_procedures=None,
        dic_config=None,
        **kwargs
    ):
        """对Dataframe按照定义的procedure处理数据, 处理带燃料的数据

        处理方法按照dic_config_handle_procedure中的配置字典进行
        """
        func_get_dic_key=None,

        time_begin = time.time()
        # 传递config参数
        kwargs.update(dic_config)
        # 读取config参数
        str_name_transformer = kwargs.get('str_name_transformer', '缺失的Transformer名')
        dic_config_name_execution_available =  self._get_param_with_forced(
            name_param_in_config='dic_config_name_execution_available',
            val_param=dic_config_name_execution_available
        )
        dic_name_fuel_to_handle = self._get_param_with_forced(
            name_param_in_config='dic_name_fuel_to_handle',
            val_param=dic_name_fuel_to_handle
        )

        # 按照优先级排序, 小的优先级先处理
        lst_name_procudure_sorted = sorted(
            dic_config_procedures.keys(),
            key=lambda name_procedure: dic_config_procedures[name_procedure].get('priority', 99),
            reverse=False)
        # 处理
        for str_name_fuel, str_name_dic_config_procedure in dic_name_fuel_to_handle.items():
            # 遍历所有的燃料名字
            dic_config_procedure = self._get_param_with_forced(
                name_param_in_config=str_name_dic_config_procedure, val_param=dic_config_procedure
            )
            # 按照优先级排序, 小的优先级先处理
            lst_name_procudure_sorted = sorted(
                dic_config_procedure.keys(),
                key=lambda name_procedure: dic_config_procedure[name_procedure]['priority'],
                reverse=False)

        print('## Pipeline: {} 开始执行处理procedure'.format(str_name_transformer))
        for str_name_procedure in lst_name_procudure_sorted:
            time_start = time.time()
            dic_single_procedure = copy.deepcopy(dic_config_procedures[str_name_procedure])
            # 读取处理信息
            str_key_name_col = dic_single_procedure.pop('str_key_name_col', str_name_procedure)
            str_art_execution = dic_single_procedure.pop('art_execution')
            str_name_execution = dic_single_procedure.pop('name_execution', None)
            obj_art_execution = dic_config_art_execution_available[str_art_execution]
            obj_func_execution = dic_config_name_execution_available.get(str_name_execution, None)
            dic_kwargs_execution = dic_single_procedure.pop('kwargs', {})
            dic_other_kwargs = dic_single_procedure
            dic_other_kwargs.update(kwargs)

            try:
                obj_art_execution(
                    df_data=df_data,
                    str_name_procedure=str_name_procedure,
                    str_key_name_col=str_key_name_col,
                    obj_func_execution=obj_func_execution,
                    dic_kwargs_execution=dic_kwargs_execution,
                    **dic_other_kwargs
                )
            except Exception as err:
                raise ValueError(
                    "错误: 处理procedure {}的缺失值时出错, 错误信息:{}".format(str_name_procedure, err)
                )
        # 打印处理完成信息
        time_end = time.time()
        print('TF名: {}, 处理完成, 耗时: {:.2f}秒'.format(
            str_name_transformer, time_end-time_begin))
        return df_data

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return
