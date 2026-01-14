#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class AbstractClassConstant(metaclass=ABCMeta):
    """抽象类, 用于规范default类的接口

    """
    def __init__(self, **kwargs) -> None:
        return

    _dic_const = {
        # 默认值字典, 用于存储默认值
            
    }

    @abstractmethod
    def _init_dic_const(self):
        """初始化常量字典的内容
        """
        pass

    @property
    def dic_const(self):
        return self._dic_const
    