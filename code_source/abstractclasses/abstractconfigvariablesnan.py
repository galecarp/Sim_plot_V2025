#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class AbstractClassVariablesNaN(metaclass=ABCMeta):
    """抽象类, 用于规范VariablesNaN类的接口

    """
    def __init__(self, **kwargs) -> None:
        return

    @abstractmethod
    def _init_dic_config_all_variables_2D_nan(self,
        **kwargs):
        """初始化默认字典的内容
        """
        pass

    @property  
    def dic_config_all_variables_2D_nan(self):
        return self._dic_config_all_variables_2D_nan
    @dic_config_all_variables_2D_nan.setter
    def dic_config_all_variables_2D_nan(self, dic_config_all_variables_2D_nan):
        self._dic_config_all_variables_2D_nan = dic_config_all_variables_2D_nan
        return
    