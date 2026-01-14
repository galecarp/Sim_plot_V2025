#!/usr/bin/env python3

import copy

import numpy as np

from code_source.abstractclasses.abstractclassconfig import AbstractClassConfig
from code_source.abstractclasses.abstractconfigvariablesnan import AbstractClassVariablesNaN
from code_source.abstractclasses.abstractclassvariablemapping import AbstractClassVariableMapping

class ParserConfigReader(AbstractClassConfig, AbstractClassVariableMapping, AbstractClassVariablesNaN):
    """ 读取不同的解析器对应的config文件
    
    """
    def __init__(self,
        **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_dic_config(**kwargs)
        pass

    def _init_dic_config(self,
        dic_config,
        **kwargs
    ):
        """ 定义之后config中的空字典
        """
        dic_config_default = {
            "str_name_path_config_col_name" : "_config\_config_rename_col",
            "str_name_file_config_col_name" : r'config_rename_col@FAS.json'
        }
        # 替换默认的字典
        self._dic_config = {}
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config_default,
            bol_create_new_key=False,
            bol_replace_dict=True,
        )
        # # 更新自定义的字典
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config,
            bol_create_new_key=False,
            bol_replace_dict=False,
        )
        return

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
    
    def get_config(self, name_var:str, val_forced=None):
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
        if val_forced is not None:
            return val_forced
        else:
            return self._dic_config_map_name_variables[name_var]

    def get_dic_config(self,
        str_name_path_config_col_name=None,
        str_name_file_config_col_name=None,
        **kwargs
    ):
        """读取设定的config文件进入字典
        """
        # 读取参数
        str_name_file_config_col_name = self.get_config(
            'str_name_path_config_col_name', val_forced=val_forced)

        return
