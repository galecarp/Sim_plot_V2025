#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict, Optional, Union
import os
from pathlib import Path
from tqdm import tqdm
import copy
import time
import json


from code_source.general_toolkits.dicttoolkit import _update_key_from_other_dict
from code_source.general_toolkits.benchtimeusage import BenchTimeUsage

class PipelineBreak:
    """用于中断 pipeline 执行并返回特定值的包装类
    
    在任何 task 的 method 中返回此对象，将立即中断整个 pipeline 的执行
    并返回包装的值
    
    Example:
        def some_method(self, input=None):
            if some_condition:
                return PipelineBreak(value=final_result)
            return normal_result
    """
    def __init__(self, value=None):
        self.value = value
    
    def __repr__(self):
        return f"PipelineBreak(value={self.value})"

class AbstractDistributor():

    @abstractmethod
    def __init__(self,
        str_name_distributor=None,
        dic_work=None,
        dic_parsed_variable_global=None,
        dic_config_variable_parse=None,
        dic_config_variable_default=None,
        **kwargs
    ):
        """

        Attributes
        ----------
        dic_work : dict
            包含任务的字典, key为任务名, value为一个字典dic_task, 包含任务的参数和任务调用的函数
        """
        super().__init__()
        pass

    @abstractmethod
    def __init_dic_work(self,
        dic_work=None
    ):
        """初始化任务字典

        """
        self.dic_work = None
        self.dic_work = dic_work
        pass

    @abstractmethod
    def __init_dic_config_variable_parse(self,
        dic_config_variable=None
    ):
        """初始化变量字典, 如果没有传入, 则使用默认值

        """
        # 默认值
        dic_config_variable_parse = {}
        # 设置参数
        pass

    def _get_dic_config_variable_parse(self,

    ):
        """ 返回dic_config_variable_parse的拷贝
        """
        return copy.deepcopy(self.dic_config_variable_parse)

    def _convert_variable_parse_to_dic_config_variable(self,
    ):
        """解析dic_config_variable_parse中的参数, 并赋值给dic_config_variable_default

        """
        dic_config_variable_default = {}
        for str_name_variable in self.dic_config_variable_parse:
            dic_config_variable_default[str_name_variable] = self.dic_config_variable_parse[str_name_variable]['default']
        self.dic_config_variable_default = dic_config_variable_default
        return

    def _clean_config_sim(self,
    ):
        """ 清除文件str_file_config_sim
        """
        # 读取参数
        str_name_file_config_sim = getattr(self, 'str_file_config_sim', 'config_sim.json')
        str_path_variant = os.getcwd()
        path_variant = Path(str_path_variant)
        path_file_config_sim = path_variant / str_name_file_config_sim
        # 如果文件存在, 则删除
        if path_file_config_sim.exists() and path_file_config_sim.is_file():
            path_file_config_sim.unlink()
        return

    def _read_config_sim(self,
        dic_parsed_variable_global:Dict = None
    ):
        """读取模拟配置json 并记录入合并dic_parsed_variable_global.
        dic_parsed_variable_global 中的值为优先级更高的值
        """
        # 读取参数
        str_name_file_config_sim = getattr(self, 'str_file_config_sim', 'config_sim.json')
        str_path_variant = os.getcwd()
        path_variant = Path(str_path_variant)
        path_file_config_sim = path_variant / str_name_file_config_sim
        # 如果文件不存在, 则为空字典
        if not path_file_config_sim.exists() or not path_file_config_sim.is_file():
            dic_config_sim = {}
        else:
            # 读取json
            with open(path_file_config_sim, 'r', encoding='utf-8') as f:
                dic_config_sim = json.load(f)
        # 记录
        dic_variable_global_updated = dic_config_sim
        _update_key_from_other_dict(
            dic_update_to=dic_variable_global_updated,
            dic_update_from=dic_parsed_variable_global,
            bol_create_new_key=True,
        )
        # 输出
        tqdm.write("读取配置文件和输出参数的总参数字典为 : {}".format(dic_variable_global_updated))
        return dic_variable_global_updated
    
    def _write_configs_to_json(self,
        dic_variable_to_write:Dict = None,
        bol_overwrite:bool = False,
    ):
        """ 将指定的变量写入到模拟配置json中
        """
        # 参数读取
        path_variant_full = Path(self.str_path_variant_full)
        str_file_config_sim = self.str_file_config_sim
        path_file_config_sim = path_variant_full / str_file_config_sim
        # 判断文件是否存在
        if not path_file_config_sim.exists():
            # 创建一个新的文件
            dic_config_sim = {}
            with open(path_file_config_sim, 'w', encoding='utf-8') as f:
                json.dump(dic_config_sim, f, indent=4, ensure_ascii=False)
        elif bol_overwrite:
            # 直接覆盖
            dic_config_sim = {}
            with open(path_file_config_sim, 'w', encoding='utf-8') as f:
                json.dump(dic_config_sim, f, indent=4, ensure_ascii=False)
        # 读取已有的文件
        with open(path_file_config_sim, 'r', encoding='utf-8') as f:
            dic_config_sim = json.load(f)
        # 更新字典
        _update_key_from_other_dict(
            dic_update_to=dic_config_sim,
            dic_update_from=dic_variable_to_write,
            bol_create_new_key=True,
            bol_ignore_new_key=False,
        )
        # 重新写入文件
        with open(path_file_config_sim, 'w', encoding='utf-8') as f:
            json.dump(dic_config_sim, f, indent=4, ensure_ascii=False)
        return

    def _set_config_variable(self,
        dic_parsed_variable_global,
        dic_config_variable_default,
        dic_config_variable_parse_default
    ):
        """ 从default字典里面, 找到本类需要的参数, 并在dic_parsed_variable_global里面找到对应的值, 如果没有, 则使用默认值
        """
        for str_name_variable in dic_config_variable_default:
            if str_name_variable in dic_parsed_variable_global:
                val_to_set = dic_parsed_variable_global[str_name_variable]
                type_to_set = dic_config_variable_parse_default[str_name_variable].get('type', str)
                if val_to_set is not None:
                    if type_to_set is bool:
                        # 如果val_to_set 为 False或false的字符串, 则
                        if isinstance(val_to_set, str) and val_to_set.lower() == 'false':
                            val_to_set = False
                        else:
                            val_to_set = bool(val_to_set)
                    else:
                        val_to_set = type_to_set(val_to_set)
                setattr(self, str_name_variable, val_to_set)
            else:
                setattr(self, str_name_variable, dic_config_variable_default[str_name_variable])
        return
    
    def _return_pipeline_break(self,
        value=None
    ):
        """ 返回一个 PipelineBreak 对象, 用于中断 pipeline 执行
        """
        return PipelineBreak(value=value)

    def do_single_task(self,
        str_task_name='',
        dic_task=None,
        input = None,
        bol_plot_taskname=False
    ):
        """ 按照dic_work中的单一项目干活
        """
        # 读取参数
        str_name_method_call = dic_task['method']
        dic_kwargs = dic_task.get('kwargs', {})
        str_text_task_benchmark = dic_task.get('str_text_task_benchmark', None)
        # 读取参数
        bol_time_benchmark = self.bol_time_benchmark
        # 时间
        flt_time_start = time.time()
        # 调用函数
        res = getattr(self, str_name_method_call)(input = input, **dic_kwargs)
        # 打印时间
        if str_text_task_benchmark is None:
            str_text_task_benchmark = "完成任务 '{}': {{}} s".format(str_task_name)
        BenchTimeUsage._print_time_usage(
            str_text=str_text_task_benchmark,
            flt_time_last=flt_time_start,
            bol_time_benchmark=bol_time_benchmark,
        )
        # 打印
        if bol_plot_taskname:
            print("完成子任务: {}".format(str_task_name))
        return res


    def do_work(self,
        input=None,
        bol_plot_taskname=False
    ):
        """ 按照dic_work中的项目干活

        """
        ts_time_start = time.time()
        # 读取参数
        dic_work = self.dic_work
        str_name_distributor = self.str_name_distributor
        # 逐个处理
        n_tasks = len(dic_work)
        # 使用tqdm显示进度
        n_length_step = 1
        # 初始化
        res = input
        bol_pipeline_break = False
        with tqdm(total=n_tasks, desc="处理{}的任务".format(str_name_distributor)) as pbar:
            for str_task_name, dic_task in dic_work.items():
                res = self.do_single_task(
                    str_task_name, dic_task,
                    input=res,
                    bol_plot_taskname=bol_plot_taskname)
                # 检查是否需要中断 pipeline
                if isinstance(res, PipelineBreak):
                    tqdm.write(f"Pipeline 在任务 '{str_task_name}' 后被中断")
                    res = res.value  # 提取实际返回值
                    bol_pipeline_break = True
                    pbar.update(n_length_step)
                    break
                # 完成更新pbar
                pbar.update(n_length_step)
        # 完成时间记录
        ts_time_end = time.time()
        if bol_pipeline_break:
            tqdm.write(f"{str_name_distributor}的任务被提前中断, 用时 {ts_time_end - ts_time_start:.2f} 秒")
        else:
            tqdm.write(f"完成{str_name_distributor}的所有任务, 用时 {ts_time_end - ts_time_start:.2f} 秒")
        return res
