#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class AbstractClassDefault(metaclass=ABCMeta):
    """抽象类, 用于规范default类的接口

    """
    def __init__(self, **kwargs) -> None:
        return

    _dic_default = {
        # 默认值字典, 用于存储默认值
            
    }

    @abstractmethod
    def _init_dic_default(self):
        """初始化默认字典的内容
        """
        pass

    @property
    def dic_default(self):
        return self._dic_default
    