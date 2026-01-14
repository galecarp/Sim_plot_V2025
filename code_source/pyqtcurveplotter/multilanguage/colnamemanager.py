#!/usr/bin/env python3


from typing import Optional, Dict, List, Union, Callable, Any
from code_source.pyqtcurveplotter.enums.languageenum import LanguageEnum
from code_source.pyqtcurveplotter.multilanguage.abstractlanguagemanager import AbstractLanguageManager
from code_source.general_toolkits.override import override

class ColNameManager(AbstractLanguageManager):
    """
    列名管理器
    
    管理数据框中的列名及其多语言显示名称
    Args:
    ----
    dic_map_col_to_display_language: 列名多语言映射字典
        格式: {
            <actual_column_name>: {
                LanguageEnum.CN: "中文显示名",
                LanguageEnum.EN: "English Display Name",
            }
        }
    str_language_current: 当前语言代码
    """
    
    def __init__(self,
        dic_map_col_to_display_language: Optional[Dict[str, Dict[str, str]]] = None,
        dic_map_display_to_actual: Optional[Dict[str, Dict[str, str]]] = None,
        str_language_current: str = LanguageEnum.CN.value
    ):
        # 调用父类初始化（初始化观察者列表）
        super().__init__()
        
        # 初始化多语言映射
        self._init_language_mapping(dic_map_col_to_display_language, str_language_current)
        
        # 如没有提供反向映射，则创建之
        if dic_map_display_to_actual is None:
            self.dic_map_display_to_actual: Dict[str, Dict[str, str]] = self._create_map_display_name_to_actual()
        else:
            self.dic_map_display_to_actual = dic_map_display_to_actual
        
        pass

    def _init_language_mapping(self,
        dic_map_col_to_display_language: Optional[Dict[str, Dict[str, str]]],
        str_language_current: str
    ):
        """
        初始化多语言映射
        
        Args:
            dic_map_col_to_display_language: 列名多语言映射字典
            str_language_current: 当前语言代码
        """
        # 保存多语言映射字典
        self.dic_map_col_to_display_language = dic_map_col_to_display_language or {}
        
        # 当前语言
        self.str_language_current = str_language_current
        self._current_language = str_language_current  # 同步父类属性
        
        # 支持的语言列表（从映射中提取）
        self.lst_language_supported = self._extract_supported_languages()
        pass
        
    def _create_map_display_name_to_actual(self) -> Dict[str, Dict[str, str]]:
        """
        创建显示名称到实际列名的反向映射字典
        
        Returns:
            dict: {语言代码: {显示名称: 实际列名}}
        """
        if not self.dic_map_col_to_display_language:
            return {}
        
        # 预先为所有语言创建空字典
        dic_map_display_to_actual = {}
        for str_language in self.lst_language_supported:
            dic_map_display_to_actual[str_language] = {}
        
        # 遍历映射创建反向映射字典
        for str_name_col_actual, dic_language_map in self.dic_map_col_to_display_language.items():
            for str_language, str_name_col_display in dic_language_map.items():
                # 直接赋值，无需检查 key 是否存在
                dic_map_display_to_actual[str_language][str_name_col_display] = str_name_col_actual
        
        return dic_map_display_to_actual
    
    # == 多语言辅助函数 ==
    def _extract_supported_languages(self) -> List[str]:
        """
        从映射字典中提取支持的语言列表
        """
        if not self.dic_map_col_to_display_language:
            return [LanguageEnum.CN]  # 默认支持的语言
        
        # 从第一个列名的映射中提取语言
        set_language = set()
        str_name_col_first = list(self.dic_map_col_to_display_language.keys())[0]
        dic_map_name_display_first = self.dic_map_col_to_display_language[str_name_col_first]
        
        return sorted(list(dic_map_name_display_first.keys()))
    
    @override
    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表（重写父类方法）
        
        Returns:
            List[str]: 支持的语言代码列表
        """
        return self.lst_language_supported
    
    def get_display_name(self,
        str_name_col_actual: str
    ) -> str:
        """
        根据实际列名和当前语言获取显示名称
        
        性能优化: 使用 dict.get() 链式调用，避免 try/except 和多次检查
        
        Args:
            str_name_col_actual: 实际的列名（数据中的列名）
            
        Returns:
            显示名称。如果没有映射，返回实际列名
        """
        # 链式 get() 调用：高效且简洁
        # 1. 获取列的语言映射字典 (如果不存在返回空字典)
        # 2. 从语言映射中获取当前语言的显示名 (如果不存在返回实际列名)
        return self.dic_map_col_to_display_language.get(
            str_name_col_actual, {}
        ).get(
            self.str_language_current, str_name_col_actual
        )
    
    def get_actual_name(self,
        str_name_col_display: str
    ) -> Optional[str]:
        """
        根据显示名称和当前语言获取实际列名      
        
        性能优化:
        - 使用缓存的反向映射字典，O(1) 查找而非 O(n) 遍历
        - 使用 dict.get() 链式调用，避免 try/except 和多次检查
        
        Args:
            str_name_col_display: 显示的列名
            
        Returns:
            实际列名。如果找不到, 返回原显示名称
        """
        # 链式 get() 调用：高效且简洁
        return self.dic_map_display_to_actual.get(
            self.str_language_current, {}
        ).get(
            str_name_col_display, str_name_col_display
        )
    
    # == 改变语言 ==
    @override
    def switch_language(self,
        str_language: Union[str, LanguageEnum]
    ):
        """
        切换当前语言, 并不检查语言是否支持
        Args:
            str_language: 语言代码
        """        
        # 保存旧语言用于通知
        str_language_old = self.str_language_current
        
        # 更新当前语言
        self.str_language_current = str_language
        self._current_language = str_language  # 同步父类属性
        
        # 通知所有观察者语言已改变
        self.notify_observers(str_language, str_language_old)
        return
    
    @override
    def get_language(self) -> str:
        """
        获取当前语言代码（重写父类方法）
        
        Returns:
            str: 当前语言代码
        """
        return self.str_language_current

    def set_language(self,
        str_language: Union[str, LanguageEnum],
        bol_force: bool = False
    ):
        """
        设置当前语言并通知所有观察者
        
        Args:
            str_language: 语言代码
        """
        if str_language not in self.lst_language_supported:
            raise ValueError(f"语言 '{str_language}' 不在支持列表中")
        # 检查语言是否改变
        if not bol_force and str_language == self.str_language_current:
            return
        # 切换语言
        return self.switch_language(str_language)
