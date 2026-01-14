#!/usr/bin/env python3
"""
多语言支持抽象类/接口类

提供统一的组件注册和多语言更新机制
"""
from abc import ABC, abstractmethod

from typing import Dict, Any, Callable, Optional, List, Union
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QComboBox, QLineEdit, QLabel, QPushButton,
    QTextEdit, QPlainTextEdit, QTabWidget
)


class I18nUpdateType(Enum):
    """多语言更新类型枚举"""
    TEXT = "text"              # 普通文本 (QPushButton, QLabel等的setText)
    TITLE = "title"            # 标题 (QGroupBox的setTitle)
    TAB_TEXT = "tab_text"      # 标签页文本 (QTabWidget的setTabText)
    EDIT = "edit" # 占位符文本 (QLineEdit等的setPlaceholderText)
    COMBOITEMS= "comboitems"            # 下拉框项目 (QComboBox的items)
    TOOLTIP = "tooltip"        # 工具提示 (setToolTip)
    WINDOW_TITLE = "window_title"  # 窗口标题 (setWindowTitle)
    CUSTOM = "custom"          # 自定义更新函数


class I18nRegistration():
    """
    多语言注册信息数据类
    
    封装单个组件的多语言更新所需的全部信息
    """
    
    def __init__(self,
        widget: Any,
        type_update: I18nUpdateType,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        lst_args_format: Optional[List] = None,
        updater_custom: Optional[Callable[[Any, "I18nRegistration"], None]] = None,
        **kwargs
    ):
        """
        Args:
            widget: 需要更新的组件引用
            update_type: 更新类型 (I18nUpdateType枚举)
            text_main: 主显示文字 (传递给tr()方法的第一个参数)
            text_disambiguation: 翻译的唯一ID (传递给tr()方法的第二个参数)
            lst_args_format: 格式化参数列表, 用于text_main.format()
            updater_custom: 自定义更新函数 (widget, registration) -> None
            **kwargs: 其他参数，例如:
                - tab_widget: 标签页所属的QTabWidget
                - tab_index: 标签页索引
                - items_list: ComboBox的items翻译键列表
        """
        self.widget = widget
        self.type_update = type_update
        self.text_main = text_main
        self.text_disambiguation = text_disambiguation
        self.lst_args_format = lst_args_format or []
        self.updater_custom = updater_custom
        self.kwargs = kwargs


class QT6I18nWidget(ABC):
    """
    QT6多语言支持 Mixin
    
    提供统一的多语言组件注册和更新机制。
    任何需要多语言支持的QWidget类都可以继承此类。
    
    使用方式:
        1. 继承此类
        2. 在创建组件时调用 register_i18n_widget() 注册
        3. 语言切换时调用 refresh_all_i18n() 刷新所有文本
    
    Example:
        class MyPanel(QWidget, AbstractI18nWidget):
            def __init__(self):
                super().__init__()
                AbstractI18nWidget.__init__(self)
                
                # 创建并注册组件
                self.btn = QPushButton("保存")
                self.register_i18n_widget(
                    key="btn_save",
                    widget=self.btn,
                    update_type=I18nUpdateType.TEXT,
                    i18n_key="保存",
                    context="btn_save"
                )
            
            def on_language_changed(self):
                self.refresh_all_i18n()

        # 创建组件示例
            # 注册按钮文本
            self.register_i18n_widget(
                key="btn_add_axis",
                widget=btn,
                update_type=I18nUpdateType.TEXT,
                i18n_key="+ 添加右侧Y轴",
                context="f_add_yaxis"
            )
            
            # 注册标签页
            self.register_i18n_widget(
                key="tab_general",
                widget=None,  # 标签页文本更新不需要widget
                update_type=I18nUpdateType.TAB_TEXT,
                i18n_key="通用设置",
                context="f_general_settings",
                tab_widget=self.tabs,
                tab_index=0
            )
            
            # 注册ComboBox items
            self.register_i18n_widget(
                key="combo_unit",
                widget=combo,
                update_type=I18nUpdateType.ITEMS,
                i18n_key=None,  # items不需要单一key
                items_list=[
                    ("小时", "unit_hour"),
                    ("天", "unit_day"),
                ]
            )
    """
    
    def __init__(self):
        """
        初始化多语言支持
        """
        self._str_name = None
        self._dic_i18n_registry: Dict[str, I18nRegistration] = {}
        # 处理registration的字典
        self._init_dic_updater()
        pass

    def _init_dic_updater(self) -> None:
        """
        初始化处理注册信息的字典
        
        将注册信息字典映射到处理函数
        """
        dic_updater_default = {
            I18nUpdateType.TEXT : self._update_text,
            I18nUpdateType.TITLE : self._update_title,
            I18nUpdateType.TAB_TEXT : self._update_tab_text,
            I18nUpdateType.EDIT : self._update_edit,
            I18nUpdateType.COMBOITEMS : self._update_comboitems,
            I18nUpdateType.TOOLTIP : self._update_tooltip,
            I18nUpdateType.WINDOW_TITLE : self._update_window_title,
            I18nUpdateType.CUSTOM : self._update_custom,
        }
        self.dic_updater = dic_updater_default
        return
        
    def register_i18n_widget(self,
        key: str,
        widget: Any,
        type_update: I18nUpdateType,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        lst_args_format: Optional[List] = None,
        updater_custom: Optional[Callable] = None,
        **kwargs
    ) -> None:
        """
        注册需要多语言更新的组件
        
        Args:
            key: 注册键，唯一标识此组件，建议格式: "模块_组件类型_用途"
                 例如: "subplot_0_groupbox_yaxis", "tab_general"
            widget: 组件引用
            type_update: 更新类型 (I18nUpdateType枚举)
            text_main: 主显示文字 (传递给tr()方法的第一个参数)
            text_disambiguation: 翻译的唯一ID (传递给tr()方法的第二个参数)
            lst_args_format: 格式化参数列表
            updater_custom: 自定义更新函数
            **kwargs: 其他参数
        
        """
        registration = I18nRegistration(
            widget=widget,
            type_update=type_update,
            text_main=text_main,
            text_disambiguation=text_disambiguation,
            lst_args_format=lst_args_format,
            updater_custom=updater_custom,
            **kwargs
        )
        self._dic_i18n_registry[key] = registration
        return
        
    def unregister_i18n_widget(self, key: str) -> bool:
        """
        取消注册组件
        
        Args:
            key: 注册键
            
        Returns:
            是否成功取消注册
        """
        if key in self._dic_i18n_registry:
            del self._dic_i18n_registry[key]
            return True
        return False
            
    def refresh_all_registration(self) -> None:
        """
        刷新所有注册的多语言组件
        
        遍历所有注册的组件并更新其文本
        """
        for key, registration in self._dic_i18n_registry.items():
            self._update_single_registration(registration)
            
    def _update_single_registration(self,
        registration: I18nRegistration
    ) -> None:
        """
        更新单个组件的多语言文本
        
        Args:
            registration: 注册信息
        """
        widget = registration.widget
        # 对于某些更新类型(如TAB_TEXT)，widget可以为None
        if widget is None and registration.type_update not in [I18nUpdateType.TAB_TEXT, I18nUpdateType.CUSTOM]:
            return
        
        type_update = registration.type_update
        method_updater: Callable = self._get_updater(type_update)
        
        # 调用对应的更新方法
        method_updater(widget, registration)
        return
    
    def _get_translated_text(self, registration: I18nRegistration) -> str:
        """
        获取翻译后的文本
        
        Args:
            registration: 注册信息
            
        Returns:
            翻译后并格式化的文本
        """
        # 获取翻译文本
        text_display = self.tr(registration.text_main, registration.text_disambiguation)
        
        # 应用格式化参数
        if registration.lst_args_format:
            text_display = text_display.format(*registration.lst_args_format)
            
        return text_display
    
    # 更新方法实现部分
    def _update_text(self, widget: QWidget, registration: I18nRegistration) -> None:
        """更新普通文本 (setText)
        
        适用于: QPushButton, QLabel, QLineEdit等所有有setText方法的组件
        """
        text = self._get_translated_text(registration)
        widget.setText(text)
        return
        
    def _update_title(self, widget: QGroupBox, registration: I18nRegistration) -> None:
        """更新标题 (setTitle)
        
        适用于: QGroupBox
        """
        text = self._get_translated_text(registration)
        widget.setTitle(text)
        return
        
    def _update_tab_text(self, widget: QTabWidget, registration: I18nRegistration) -> None:
        """更新标签页文本
        
        适用于: QTabWidget
        widget参数直接传入QTabWidget, kwargs中提供tab索引: index_tab (int)
        """
        index_tab: int = registration.kwargs['index_tab']
        if index_tab is None:
            return
        text = self._get_translated_text(registration)
        widget.setTabText(index_tab, text)
        return
        
    def _update_edit(self,
        widget: Union[QLineEdit, QTextEdit, QPlainTextEdit],
        registration: I18nRegistration
    ) -> None:
        """更新占位符文本
        
        适用于: QLineEdit, QTextEdit, QPlainTextEdit
        """
        text = self._get_translated_text(registration)
        widget.setPlaceholderText(text)
        return
        
    def _update_comboitems(self, widget: QComboBox, registration: I18nRegistration) -> None:
        """
        更新下拉框items
        
        适用于: QComboBox
        需要在kwargs中提供items_list: List[Tuple[str, str]]
        每个tuple为 (text_main, text_disambiguation)
        """ 
        lst_item_combo = registration.kwargs['lst_item_combo']
        if not lst_item_combo:
            return
            
        # 保存当前选择的索引
        index_current = widget.currentIndex()
        
        # 阻止信号
        widget.blockSignals(True)
        try:
            widget.clear()
            
            # 重新添加翻译后的所有items
            for text_main, text_disambiguation in lst_item_combo:
                text = self.tr(text_main, text_disambiguation)
                widget.addItem(text)
            
            # 恢复选择
            if 0 <= index_current < widget.count():
                widget.setCurrentIndex(index_current)
            else:
                widget.setCurrentIndex(0)
        finally:
            # 确保信号一定会被恢复
            widget.blockSignals(False)
        return
        
    def _update_tooltip(self, widget: QWidget, registration: I18nRegistration) -> None:
        """更新工具提示
        
        适用于: 所有QWidget及其子类
        """
        text = self._get_translated_text(registration)
        widget.setToolTip(text)
        return
        
    def _update_window_title(self, widget: QWidget, registration: I18nRegistration) -> None:
        """更新窗口标题
        
        适用于: QMainWindow, QDialog, QWidget等所有有setWindowTitle的组件
        """
        text = self._get_translated_text(registration)
        widget.setWindowTitle(text)
        return
        
    def _update_custom(self, widget: Any, registration: I18nRegistration) -> None:
        """自定义更新"""
        if registration.updater_custom is None:
            return
        registration.updater_custom(widget, registration)
        return
        
    # 增加的方法
    def addTab(self,
        widget_container : QTabWidget,
        widget: QWidget,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        key_registration: Optional[str] = None,
        str_name_widget_container: Optional[str] = None,
        str_name_widget: Optional[str] = None,
        **kwargs
    ) -> int:
        """
        添加标签页并自动注册多语言支持
        
        Args:
            widget_container: QTabWidget容器
            widget: 要添加的页面组件
            text_main: 标签页文本
            text_disambiguation: 翻译上下文
            key_registration: 注册键，如果为None则自动生成
            
        Returns:
            int: 新添加的标签页索引
        """
        # 添加标签页，addTab返回新标签页的索引
        index_tab = widget_container.addTab(
            widget,
            self.tr(text_main, text_disambiguation)
        )
        
        # 自动生成注册键（如果未提供）
        if key_registration is None:
            if str_name_widget_container is None:
                str_name_widget_container = widget_container.objectName() or "tabwidget"
            if str_name_widget is None:
                str_name_widget = widget.objectName() or "tabpage"
            key_registration = f"{str_name_widget_container}_{index_tab}_{str_name_widget}"
        
        # 注册多语言标签页文本, 注意传入的是widget_container
        self.register_i18n_widget(
            key=key_registration,
            widget=widget_container,
            type_update=I18nUpdateType.TAB_TEXT,
            text_main=text_main,
            text_disambiguation=text_disambiguation,
            index_tab=index_tab,
            **kwargs
        )
        return index_tab 

    def addComboBoxItems(self,
        widget_container : QComboBox,
        widget: QWidget,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        key_registration: Optional[str] = None,
        str_name_widget_container: Optional[str] = None,
        str_name_widget: Optional[str] = None,
        lst_item_combo: Optional[List[tuple]] = None,
        **kwargs
    ):
        """
        添加标签页并自动注册多语言支持
        
        Args:
            widget_container: QComboBox容器
            widget: 要添加的页面组件
            text_main: 标签页文本
            text_disambiguation: 翻译上下文
            key_registration: 注册键，如果为None则自动生成
        """
        # 添加combo box items
        if lst_item_combo is None:
            lst_item_combo = []
        for idx_item, (text_main, text_disambiguation) in enumerate(lst_item_combo):
            # 添加item
            widget_container.addItem(
                self.tr(text_main, text_disambiguation)
            )
        n_items = widget_container.count()
        # 自动生成注册键（如果未提供）
        if key_registration is None:
            if str_name_widget_container is None:
                str_name_widget_container = widget_container.objectName() or "combobox"
            if str_name_widget is None:
                str_name_widget = widget.objectName() or f"item_combobox_{n_items}_items"
            key_registration = f"{str_name_widget_container}_{str_name_widget}"
        
        # 注册多语言标签页文本
        self.register_i18n_widget(
            key=key_registration,
            widget=widget_container,
            type_update=I18nUpdateType.COMBOITEMS,
            text_main=text_main,
            text_disambiguation=text_disambiguation,
            lst_item_combo=lst_item_combo,
            **kwargs
        )
        # 设定combobox
        widget_container.setCurrentIndex(0) # 默认选择第一个
        return
    
    # 改文字的方法
    def setTitle(self,
        widget: QWidget,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        key_registration: Optional[str] = None,
        str_name_widget_container: Optional[str] = None,
        str_name_widget: Optional[str] = None,
        widget_container : Any = None,
        **kwargs
    ):
        """
        更改Title并自动注册多语言支持
        
        Args:
            widget: 要改变标题的组件
            text_main: 标签页文本
            text_disambiguation: 翻译上下文
            key_registration: 注册键，如果为None则自动生成
        """
        # 自动生成注册键（如果未提供）
        if key_registration is None:
            if str_name_widget is None:
                str_name_widget = widget.objectName() or f"item_with_title_{text_disambiguation}"
            key_registration = f"{self._str_name}_{str_name_widget}"
        
        # 注册多语言标签页文本
        self.register_i18n_widget(
            key=key_registration,
            widget=widget,
            type_update=I18nUpdateType.TITLE,
            text_main=text_main,
            text_disambiguation=text_disambiguation,
            **kwargs
        )
        return
    
    def setText(self,
        widget: QWidget,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        key_registration: Optional[str] = None,
        str_name_widget_container: Optional[str] = None,
        str_name_widget: Optional[str] = None,
        widget_container : Any = None,
        **kwargs
    ):
        """
        更改Text并自动注册多语言支持
        
        Args:
            widget: 要改变Text的组件
            text_main: 标签页文本
            text_disambiguation: 翻译上下文
            key_registration: 注册键，如果为None则自动生成
        """
        # 自动生成注册键（如果未提供）
        if key_registration is None:
            if str_name_widget is None:
                str_name_widget = widget.objectName() or f"item_with_text_{text_disambiguation}"
            key_registration = f"{self._str_name}_{str_name_widget}"
        
        # 注册多语言标签页文本
        self.register_i18n_widget(
            key=key_registration,
            widget=widget,
            type_update=I18nUpdateType.TEXT,
            text_main=text_main,
            text_disambiguation=text_disambiguation,
            **kwargs
        )
        return
    
    # 改创建label的方法
    def createLabel(self,
        text_main: str,
        text_disambiguation: Optional[str] = None,
        key_registration: Optional[str] = None,
        str_name_widget_container: Optional[str] = None,
        str_name_widget: Optional[str] = None,
        widget_container : Any = None,
        widget : Any = None,
        **kwargs
    ) -> QLabel:
        """
        添加文字label并自动注册多语言支持
        
        Args:
            widget_container: 无用参数，仅为保持接口一致性
            widget: 要添加的页面组件
            text_main: 标签页文本
            text_disambiguation: 翻译上下文
            key_registration: 注册键，如果为None则自动生成
        """
        # 生成QLabel
        label = QLabel(self.tr(text_main, text_disambiguation))

        # 自动生成注册键（如果未提供）
        if key_registration is None:
            if str_name_widget is None:
                str_name_widget = f"label_{text_disambiguation}"
            key_registration = f"{self._str_name}_{str_name_widget}"
        
        # 注册多语言标签页文本
        self.register_i18n_widget(
            key=key_registration,
            widget=label,
            type_update=I18nUpdateType.TEXT,
            text_main=text_main,
            text_disambiguation=text_disambiguation
        )
        return label
    


    # Getters / Setters
    def get_i18n_registry_info(self) -> Dict[str, str]:
        """
        获取注册信息摘要（用于调试）
        
        Returns:
            Dict: key为注册键, value为主显示语言和更新类型摘要
        """
        dic_info_reg = {}
        for key, reg in self._dic_i18n_registry.items():
            dic_info_reg[key] = f"{reg.type_update.value}: {reg.text_main}"
        return dic_info_reg
    
    def _get_updater(self,
        type_update: I18nUpdateType
    ) -> Optional[Callable]:
        """
        获取对应更新类型的处理函数
        
        Args:
            update_type: 更新类型
            
        Returns:
            处理函数引用或None
        """
        return self.dic_updater[type_update]
