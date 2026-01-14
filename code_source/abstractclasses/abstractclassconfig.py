#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod


class AbstractClassConfig(metaclass=ABCMeta):
    """抽象类, 用于规范config类的接口

    """
    def __init__(self, **kwargs) -> None:
        return

    @abstractmethod
    def _init_dic_config(self,
        **kwargs):
        """初始化默认字典的内容
        """
        pass

    @abstractmethod
    def get_config(self, name_param, bol_must_have=True):
        """获取配置参数
        """
        pass

    @abstractmethod
    def get_param_with_forced(self, name_param_in_config=None, val_param=None):
        """当传入的参数为None时, 如val_param不为None, 则直接返回val_param,  否则从config读取对应的参数值
        """
        pass
