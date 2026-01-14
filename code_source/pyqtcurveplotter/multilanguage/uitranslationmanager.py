#!/usr/bin/env python3

from typing import Optional, List, Callable, Union
from pathlib import Path
from PyQt6.QtCore import QTranslator, QCoreApplication, QLocale
from PyQt6.QtWidgets import QApplication

from code_source.pyqtcurveplotter.enums.languageenum import LanguageEnum
from code_source.pyqtcurveplotter.multilanguage.abstractlanguagemanager import AbstractLanguageManager
from code_source.general_toolkits.override import override


class UITranslationManager(AbstractLanguageManager):
    """
    界面翻译管理器
    
    管理应用程序的多语言翻译，支持运行时切换语言。
    
    职责分离:
    - UITranslationManager: 使用 Qt 的 .tr() 方法管理UI元素（按钮、标签等）的翻译
    - ColNameManager: 使用字典映射管理数据列名的翻译
    
    两者都支持观察者模式，可以同时被语言切换动作触发。
    """
    
    def __init__(self,
        app: Optional[QApplication] = None
    ):
        """
        初始化翻译管理器
        
        Args:
            app: QApplication实例, 如果为None则自动获取
        """
        # 调用父类初始化（初始化观察者列表）
        super().__init__()
        
        self.app : QApplication = app or QCoreApplication.instance()
        self.translator = QTranslator()
        
        # 翻译文件所在目录
        self.str_prefix_file_translation: str = 'pyqtcurveplotter_{}.qm'
        self.str_name_folder_translation: str = 'translations'
        self.path_folder_translation : Path = Path(__file__).parent / self.str_name_folder_translation
        
        # 当前语言
        self.str_code_language = LanguageEnum.CN  # 默认中文
        self._current_language = LanguageEnum.CN  # 同步父类属性
        
        pass

    @override
    def switch_language(self,
        str_code_language: Union[str, LanguageEnum]
    ) -> bool:
        """
        切换到指定语言
        
        Args:
            str_code_language: 语言代码
            
        Returns:
            bool: 是否成功加载翻译文件
        """
        return self._load_language_translator(str_code_language)
    
    def _load_language_translator (self,
        str_code_language: Union[str, LanguageEnum]
    ) -> bool:
        """
        加载指定语言的翻译文件（内部方法，直接调用 switch_language
        
        Args:
            language_code: 语言代码
            
        Returns:
            bool: 是否成功加载翻译文件
        """
        # 保存当前语言状态，以便失败时恢复
        str_code_language_old = self.str_code_language
        translator_old = self.translator
        
        # 移除旧的翻译器
        if self.translator:
            self.app.removeTranslator(self.translator)
        
        # 创建新的翻译器
        self.translator = QTranslator()
        
        # 翻译文件路径:
        str_name_file_ts = self.str_prefix_file_translation.format(str_code_language)
        path_file_ts = self.path_folder_translation / str_name_file_ts
        
        # 加载翻译文件
        if path_file_ts.exists():
            success = self.translator.load(str(path_file_ts))
            if success:
                # 成功加载：安装新翻译器并更新语言
                self.app.installTranslator(self.translator)
                self.str_code_language = str_code_language
                self._current_language = str_code_language  # 同步父类属性
                # 通知所有观察者语言已改变
                self.notify_observers(str_code_language)
                return True
            else:
                # 加载失败：恢复旧翻译器
                print(f"加载翻译文件失败: {path_file_ts}")
                self.translator = translator_old
                if translator_old:
                    self.app.installTranslator(translator_old)
                return False
        else:
            # 文件不存在：恢复旧翻译器
            print(f"翻译文件不存在: {path_file_ts}")
            self.translator = translator_old
            if translator_old:
                self.app.installTranslator(translator_old)
            return False
    
    @override
    def get_language(self) -> str:
        """
        获取当前语言代码
        
        Returns:
            str: 当前语言代码
        """
        return self.str_code_language
    
    @override
    def get_supported_languages(self) -> List[str]:
        """
        获取所有可用的语言列表（重写父类方法）
        
        Returns:
            list[str]: 可用语言代码列表
        """
        # 获取参数
        path_folder_translation : Path = self.path_folder_translation
        str_prefix_file_translation : str = self.str_prefix_file_translation
        # 默认只有中文
        if not path_folder_translation.exists():
            return [LanguageEnum.CN]
        # 模式匹配
        str_pattern_file_ts = str_prefix_file_translation.format('*')
        # 搜索翻译文件
        lst_language = []
        for path_file_ts in path_folder_translation.glob(str_pattern_file_ts):
            # 从文件名提取语言代码: pyqtcurveplotter_en.qm -> en
            str_code_language = path_file_ts.stem.split('_', 1)[1]
            lst_language.append(str_code_language)
        
        # 始终包含中文（源语言）
        if LanguageEnum.CN not in lst_language:
            lst_language.insert(0, LanguageEnum.CN)
        return lst_language
    
    def get_lst_language(self,
    ) -> list[str]:
        """
        获取所有可用的语言列表（兼容旧接口）
        
        Returns:
            list[str]: 可用语言代码列表
        """
        return self.get_supported_languages()
