#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class AbstractClassVariableMapping(metaclass=ABCMeta):
    """抽象类, 用于规范VariableMapping类的接口

    """
    def __init__(self, **kwargs) -> None:
        return

    @abstractmethod
    def _init_dic_config_map_name_variables(self,
        **kwargs):
        """初始化默认字典的内容
        """
        pass

    @abstractmethod
    def get_dic_key(self, name_var:str, name_forced=None):
        """ 提供变量名, 返回原始数据中的key名

        此变量和GeneralTransformer中的dic_config_map_name_variables中定义对应
        """
        pass

    @abstractmethod
    def get_dic_config_all_variables_2D_nan_with_mapped_name(self,
        dic_config_all_variables_2D_nan=None
    ):
        """ 返回一个字典, 没项都是 dic_config_all_variables_2D_nan中存在的
        但是key是对应的原始数据中的key, 即定义在dic_config_map_name_variables中的key
        """
        pass

    @abstractmethod
    def get_patched_map_name_variables_with_lib(self,
        dic_config_map_name_variables_default,
        **kwargs
    ):
        """ 从kwargs中读取参数, 并与dic_config_map_name_variables_default中的默认值进行替换合并
        即如果kwargs中有某个参数, 则使用kwargs的参数值, 没有则从dic_config_map_name_variables_default中读取
        最后合并为一个完整的参数字典
        """
        pass
    
