#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Callable, Optional

from code_source.pyqtcurveplotter.enums.languageenum import LanguageEnum


class AbstractLanguageManager(ABC):
    """
    语言管理器抽象基类
    
    定义了语言管理器的通用接口和观察者模式的实现。

    """
    
    def __init__(self):
        """初始化观察者列表"""
        self._observers: List[Callable[[str], None]] = []
        self._current_language: Optional[str] = None
        pass
    
    def connect(self, callback: Callable[[str, Optional[str]], None]):
        """
        连接观察者回调函数
        
        当语言改变时，所有连接的回调函数都会被调用。
        
        Args:
            callback: 回调函数，签名为 callback(new_language: str) -> None
            
        Example:
            >>> def on_language_changed(language: str):
            ...     print(f"Language changed to: {language}")
            >>> 
            >>> manager.connect(on_language_changed)
        """
        if callback not in self._observers:
            self._observers.append(callback)
        return
    
    def disconnect(self, callback: Callable[[str, Optional[str]], None]):
        """
        断开观察者回调函数
        
        Args:
            callback: 要断开的回调函数
            
        Example:
            >>> manager.disconnect(on_language_changed)
        """
        if callback in self._observers:
            self._observers.remove(callback)
        return
    
    def disconnect_all(self):
        """
        断开所有观察者
        
        Example:
            >>> manager.disconnect_all()
        """
        self._observers.clear()
        return
    
    def notify_observers(self,
        str_language: str,
        str_language_old: Optional[str] = None
    ):
        """
        通知所有观察者语言已改变
        
        遍历所有已连接的回调函数并执行它们。
        如果某个回调函数执行失败，捕获异常并继续执行其他回调。
        """
        for callback in self._observers:
            try:
                callback(str_language, str_language_old)
            except Exception as e:
                print(f"警告: 观察者回调函数执行失败: {e}")
        return
    
    def get_observer_count(self) -> int:
        """
        获取当前连接的观察者数量
        """
        return len(self._observers)
    
    # ========================================================================
    # 语言管理的抽象接口 (子类必须实现)
    # ========================================================================
    
    @abstractmethod
    def switch_language(self, str_language: str) -> bool:
        """
        切换到指定语言（抽象方法）
        
        子类必须实现此方法来定义具体的语言切换逻辑。
        实现时应该：
        1. 执行语言切换的具体操作
        2. 更新内部语言状态
        3. 调用 notify_observers() 通知所有观察者
        
        Args:
            str_language: 目标语言代码
            
        Returns:
            bool: 切换是否成功
            
        Example (子类实现):
            >>> def switch_language(self, str_language: str) -> bool:
            ...     # 执行具体的语言切换逻辑
            ...     success = self._do_language_switch(str_language)
            ...     if success:
            ...         self._current_language = str_language
            ...         self.notify_observers(str_language)
            ...     return success
        """
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        """
        获取当前语言代码（抽象方法）
        
        子类必须实现此方法来返回当前的语言代码。
        
        Returns:
            str: 当前语言代码
            
        Example (子类实现):
            >>> def get_language(self) -> str:
            ...     return self._current_language
        """
        pass
    
    # ========================================================================
    # 可选的辅助方法 (子类可以选择性覆盖)
    # ========================================================================
    
    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表（可选方法）
        
        子类可以覆盖此方法来返回支持的语言列表。
        默认实现返回空列表。
        
        Returns:
            List[str]: 支持的语言代码列表
        """
        return []
    
    def is_language_supported(self, str_language: str) -> bool:
        """
        检查指定语言是否被支持（可选方法）
        
        子类可以覆盖此方法来实现自定义的语言支持检查逻辑。
        默认实现基于 get_supported_languages() 的返回值。
        
        Args:
            str_language: 要检查的语言代码
            
        Returns:
            bool: 是否支持该语言
        """
        lst_language_supported = self.get_supported_languages()
        if not lst_language_supported:
            # 如果没有定义支持的语言列表，则认为支持所有语言
            return True
        return str_language in lst_language_supported
