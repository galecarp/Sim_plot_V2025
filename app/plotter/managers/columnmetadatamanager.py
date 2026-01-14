#!/usr/bin/env python3

from typing import List, Set, Dict, Optional, Callable, override

from app.plotter.managers.abstractmanager import AbstractManager

class ColumnMetadataManager(AbstractManager ):
    """
    列元数据管理器
    
    管理数据源的全局信息，包括：
    - 所有可用的列名
    - 列名的多语言映射
    - 列名的正反向转换（实际列名 <-> 显示列名）
    
    这是一个只读的数据源注册表，不涉及具体的曲线实例。
    用于在UI中提供列选择、显示等功能。
    
    Attributes:
        lst_name_col_actual: 所有可用的实际列名列表
        func_get_display_name: 将实际列名转换为显示列名的回调函数
        func_get_actual_name: 将显示列名转换为实际列名的回调函数
    """
    
    def __init__(self,
        lst_name_col_actual: List[str],
        func_get_display_name: Optional[Callable[[str], str]] = None,
        func_get_actual_name: Optional[Callable[[str], Optional[str]]] = None
    ):
        """
        初始化列元数据管理器
        
        Args:
            lst_name_col_actual: 所有可用的实际列名列表
            func_get_display_name: 
                将实际列名转换为显示列名的回调函数
                示例: "GTG_P_out" -> "燃气轮机出力"
                如果为 None，则使用原始列名
            func_get_actual_name: 
                将显示列名转换为实际列名的回调函数
                示例: "燃气轮机出力" -> "GTG_P_out"
                如果为 None，则使用原始列名
        """
        super().__init__()
        self.lst_name_col_actual = lst_name_col_actual
        self.func_get_display_name = func_get_display_name or (lambda x: x)
        self.func_get_actual_name = func_get_actual_name or (lambda x: x)
        
        # 构建快速查找集合
        self._set_name_col_actual: Set[str] = set(lst_name_col_actual)
        # 初始化信号
        self._init_signal()
        pass

    @override
    def _init_signal(self):
        """初始化信号"""
        self.dic_signals = {
        }
        pass

    # 信号处理
    @override
    def _connect_signals(self):
        """连接到下游的信号"""
        pass
    
    def get_display_name(self, str_name_col_actual: str) -> str:
        """
        获取列的显示名称
        
        Args:
            str_name_col_actual: 实际列名
            
        Returns:
            显示列名（可能经过多语言翻译）
        """
        return self.func_get_display_name(str_name_col_actual)
    
    def get_actual_name(self, str_name_col_display: str) -> Optional[str]:
        """
        获取列的实际名称
        
        Args:
            str_name_col_display: 显示列名
            
        Returns:
            实际列名，如果不存在则返回 None
        """
        return self.func_get_actual_name(str_name_col_display)
    
    def get_all_actual_names(self) -> List[str]:
        """
        获取所有可用的实际列名
        
        Returns:
            实际列名列表
        """
        return self.lst_name_col_actual.copy()
    
    def get_all_display_names(self) -> List[str]:
        """
        获取所有可用的显示列名
        
        Returns:
            显示列名列表（经过转换）
        """
        return [self.get_display_name(name) for name in self.lst_name_col_actual]
    
    def is_valid_actual_name(self, str_name_col_actual: str) -> bool:
        """
        检查实际列名是否有效
        
        Args:
            str_name_col_actual: 要检查的实际列名
            
        Returns:
            如果列名在可用列表中则返回 True，否则返回 False
        """
        return str_name_col_actual in self._set_name_col_actual
    
    def is_valid_display_name(self, str_name_col_display: str) -> bool:
        """
        检查显示列名是否有效
        
        Args:
            str_name_col_display: 要检查的显示列名
            
        Returns:
            如果该显示名称可以转换为有效的实际列名则返回 True
        """
        actual_name = self.get_actual_name(str_name_col_display)
        return actual_name is not None and self.is_valid_actual_name(actual_name)
    
    def get_column_count(self) -> int:
        """
        获取可用列的总数
        
        Returns:
            列的数量
        """
        return len(self.lst_name_col_actual)
