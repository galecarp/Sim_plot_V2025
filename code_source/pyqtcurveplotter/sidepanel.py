#!/usr/bin/env python3

from typing import Tuple, List, Set, Dict, Optional, Callable
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QGroupBox, QCheckBox, QComboBox, QPushButton, QLabel, 
    QDoubleSpinBox, QScrollArea, QColorDialog, QFormLayout, 
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QLineEdit, QSpinBox, QFrame, QTabWidget, QDateTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt6.QtGui import QColor

from code_source.pyqtcurveplotter.enums.languageenum import LanguageEnum
from code_source.pyqtcurveplotter.axisconfigpanel import AxisConfigPanel
from code_source.pyqtcurveplotter.graphconfigs.axisconfig import AxisConfig
from code_source.pyqtcurveplotter.graphconfigs.curveconfig import CurveConfig
from code_source.pyqtcurveplotter.multilanguage.qt6i18nwidget import (
    QT6I18nWidget, I18nUpdateType, I18nRegistration
)
from code_source.pyqtcurveplotter.curveconfigpanel import CurveConfigWidget

class SidePanel(QWidget, QT6I18nWidget):
    """
    侧边栏配置面板
    
    继承AbstractI18nWidget以支持多语言组件的统一管理
    """
    # 信号
    sig_config_changed: pyqtSignal = pyqtSignal()
    sig_xaxis_time_changed: pyqtSignal = pyqtSignal(float, float)
    
    def __init__(self,
        lst_name_col: List[str],
        n_subplot: int = 3,
        func_get_display_name: Optional[Callable[[str], str]] = None,
        func_get_actual_name: Optional[Callable[[str], Optional[str]]] = None,
        lst_language_supported: Optional[List[str]] = None,
        str_language_current: str = LanguageEnum.CN,
        func_on_language_changed: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Args:
            lst_name_col: 数据列名列表（实际列名）
            n_subplot: 子图数量
            func_get_display_name: 获取显示名称的回调函数 (actual_name) -> display_name
            func_get_actual_name: 获取实际名称的回调函数 (display_name) -> actual_name
            lst_language_supported: 支持的语言列表
            str_language_current: 当前语言代码
            func_on_language_changed: 语言改变时的回调函数 (language_code) -> None
            parent: 父组件
        """
        # 初始化
        super(QWidget, self).__init__(parent=parent)
        super(QT6I18nWidget, self).__init__()
        self._str_name = "SidePanel"
        self.lst_name_col = lst_name_col
        self.n_subplot = n_subplot
        # 常值
        self.str_name_axis_left = 'main'  # 主轴名称
        
        # 多语言支持
        self.lst_language_supported = lst_language_supported or [LanguageEnum.CN, LanguageEnum.EN]
        self.str_language_current = str_language_current
        self.func_on_language_changed = func_on_language_changed
        # 多语言支持(列名)
        self.func_get_display_name = func_get_display_name or (lambda x: x)
        self.func_get_actual_name = func_get_actual_name or (lambda x: x)

        # 初始化轴配置管理器
        self._init_axisconfig_subplot()
        # 初始化曲线配置管理器
        self._init_curveconfig_subplot()
        # 初始y轴容器和布局存储
        self._init_dic_yaxis()
        # 初始曲线容器和布局存储
        self._init_dic_curve()
        # 初始化侧边栏的标签页
        self.init_all_tabs()
        pass


    
    def _init_curveconfig_subplot(self):
        """初始化曲线存储

        dic_curveconfig_subplot 结构:
            {
                idx_subplot : {
                    str_name_col_actual : CurveConfig,
                    ...
                },
                ...
            }
        """
        self.dic_curveconfig_subplot: Dict[int, Dict[str, CurveConfig]] = {
            idx_subplot : {}
            for idx_subplot in range(self.n_subplot)
        }
        pass

    def _init_added_cols_subplot(self):
        """初始化子图的已显示列存储
        dic_added_cols_subplot 结构:
            {
                idx_subplot : Set[str_name_col_actual],
                ...
            }
        """
        self.dic_added_cols_subplot : Dict[int, Set[str]] = {
            idx_subplot : set()
            for idx_subplot in range(self.n_subplot)
        }
        pass

    def _init_dic_yaxis(self):
        """初始化y轴配置面板 的 容器 和 布局
        """
        self.dic_container_yaxis_subplot : Dict[int, QWidget] = {}
        self.dic_layout_yaxis_subplot : Dict[int, QVBoxLayout] = {}
        pass

    # def _init_dic_curve(self):
    #     """初始化曲线配置面板 的 容器 和 布局
    #     """
    #     self.dic_selector_curve_subplot : Dict[int, QComboBox] = {}
    #     self.dic_container_curve_subplot : Dict[int, QWidget] = {}
    #     self.dic_layout_curve_subplot : Dict[int, QVBoxLayout] = {}
    #     pass

    def init_all_tabs(self):
        """初始化子图的设置标签页
        """
        # 主布局
        layout_main = QVBoxLayout()
        # 标签页
        self.widget_tab = QTabWidget()
        str_name_widget_tab = f"{self._str_name}_tab_widget"
        self.widget_tab.setObjectName(str_name_widget_tab)
        
        # 1.通用设置标签页
        tab_general = self._create_general_tab()
        self.addTab(
            widget_container = self.widget_tab,
            widget = tab_general,
            text_main = "通用设置",
            text_disambiguation = 'f_config_general' 
        )
        
        # 2.时间设置标签页
        tab_time = self._create_xaxis_tab()
        self.addTab(
            widget_container = self.widget_tab,
            widget = tab_time,
            text_main = "时间设置",
            text_disambiguation = 'f_setting_time',

        )
        
        # 3.为每个子图创建单独的plot标签页
        for idx_subplot in range(self.n_subplot):
            tab_plot = self._create_plot_tab(idx_subplot)
            self.addTab(
                widget_container = self.widget_tab,
                widget = tab_plot,
                text_main = "子图{}",
                text_disambiguation = 'f_subplot',
                lst_args_format = [idx_subplot + 1]
            )
        # 组织主布局
        layout_main.addWidget(self.widget_tab)
        self.setLayout(layout_main)
        pass
    
    # 1.通用标签页
    def _create_general_tab(self,
    ) -> QWidget:
        """
        创建通用设置标签页
        """
        # 创建容器和布局
        widget = QWidget()
        layout = QFormLayout()
        # 设定名字
        str_name_widget = f"{self._str_name}_tab_general"
        widget.setObjectName(str_name_widget)
        
        # 创建语言选择器
        self.combo_language = QComboBox()
        self.combo_language.setObjectName(f"{self._str_name}_combo_language")
        self.combo_language.addItems(self.lst_language_supported)
        ## 设置当前语言
        idx_current = self.combo_language.findText(self.str_language_current)
        if idx_current >= 0:
            self.combo_language.setCurrentIndex(idx_current)
        self.combo_language.currentTextChanged.connect(self._on_language_changed)
        ## 组织布局
        label_combo_language = self.createLabel(
            text_main="语言: ",
            text_disambiguation="f_language"
        )
        # 展示行布局
        layout.addRow(label_combo_language, self.combo_language)

        # 设置布局
        widget.setLayout(layout)
        return widget
    
    # 2.x轴的标签页
    def _subcreate_start_time_input(self) -> QDateTimeEdit:
        """
        创建起始时间输入框
        """
        datetimeedit_start : QDateTimeEdit = QDateTimeEdit() # 日期时间输入框
        # 设定名字
        str_name_widget = f"{self._str_name}_datetimeedit_start"
        datetimeedit_start.setObjectName(str_name_widget)
        # 设置属性
        datetimeedit_start.setDateTime(QDateTime.currentDateTime()) # 默认值为当前时间
        datetimeedit_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss") # 显示格式
        datetimeedit_start.setCalendarPopup(True) # 启用日历弹出
        datetimeedit_start.dateTimeChanged.connect(self.emit_xaxis_time_range) # 改变值连接信号回调
        self.datetimeedit_start = datetimeedit_start
        return

    def _subcreate_spin_time_span(self) -> QDoubleSpinBox:
        """
        创建时间段长度输入框
        """
        spin_span : QDoubleSpinBox = QDoubleSpinBox() # 浮点输入框
        # 设定名字
        str_name_widget = f"{self._str_name}_spin_time_span"
        spin_span.setObjectName(str_name_widget)
        # 设置属性
        spin_span.setRange(1, 1e9) # 设置范围
        spin_span.setValue(100) # 默认值
        spin_span.valueChanged.connect(self.emit_xaxis_time_range) # 改变值连接信号回调
        self.spin_span = spin_span
        return

    def _subcreate_combo_span_unit(self) -> QComboBox:
        """
        创建时间段长度单位选择器
        """
        # 创建"时间段长度单位"选择器
        combo_span_unit : QComboBox = QComboBox()
        # 设定名字
        str_name_widget = f"{self._str_name}_combo_span_unit"
        combo_span_unit.setObjectName(str_name_widget)
        # 设置属性
        self.addComboBoxItems(
            combo_box=combo_span_unit,
            widget_container=self.widget_tab,
            widget=combo_span_unit,
            text_main="时间跨度/单位: ",
            text_disambiguation="f_time_span",
            lst_items=[
                ("小时", "unit_hour"),
                ("天", "unit_day"),
                ("周", "unit_week"),
                ("月", "unit_month"),
                ("年", "unit_year"),
            ]
        )
        # 回调链接
        combo_span_unit.currentIndexChanged.connect(self._on_span_unit_changed)
        self.combo_span_unit = combo_span_unit
        
        # 注册时间单位选择器
        self.register_i18n_widget(
            key="combo_span_unit",
            widget=combo_span_unit,
            update_type=I18nUpdateType.ITEMS,
            i18n_key=None,
            lst_items=[
                ("小时", "unit_hour"),
                ("天", "unit_day"),
                ("周", "unit_week"),
                ("月", "unit_month"),
                ("年", "unit_year"),
            ]
        )
        return

    def _subcreate_hbox_span_unit(self) -> QHBoxLayout:
        """
        创建水平布局来放置时间跨度输入框和单位选择框
        """
        hbox_span = QHBoxLayout()
        hbox_span.addWidget(self.spin_span)
        hbox_span.addWidget(self.combo_span_unit)
        self.hbox_span = hbox_span
        return hbox_span

    def _create_xaxis_tab(self) -> QWidget:
        """
        创建xaxis用的时间设置标签页
        """
        # 创建容器和布局
        widget = QWidget()
        layout = QFormLayout()
        # 设定名字
        str_name_widget = f"{self._str_name}_tab_xaxis"
        widget.setObjectName(str_name_widget)
        # 创建"起始时间"输入框（日期时间格式）
        self._subcreate_start_time_input()
        # 创建"时间段长度"输入框
        self._subcreate_spin_time_span()
        # 创建"时间段长度单位"选择器
        self._subcreate_combo_span_unit()
        # 创建水平布局来放置时间跨度输入框和单位选择框
        hbox_time_span = self._subcreate_hbox_span_unit()

        # 组织布局
        # 展示起始时间展示行
        label_start_time = self.createLabel(
            text_main="起始时间:",
            text_disambiguation="f_start_time"
        )
        layout.addRow(label_start_time, self.datetimeedit_start)

        # 时间段长度和单位布局
        label_time_span = self.createLabel(
            text_main="时间段长度/单位:",
            text_disambiguation="f_time_span"
        )
        layout.addRow(label_time_span, hbox_time_span)
        # 设置布局
        widget.setLayout(layout)
        return widget
    
    # 创建滚动区域
    def _update_combobox_for_cols(self,
        widget: QComboBox,
        text: str,
        registration: I18nRegistration
    ) -> None:
        """
        自定义更新包含列名的下拉框
        
        需要同时更新列名
        """
        # 保存当前选择的实际列名
        str_current_text = widget.currentText()
        str_actual_name = self.func_get_actual_name(str_current_text)
        
        # 阻止信号
        widget.blockSignals(True)
        widget.clear()
        
        # 添加所有列名（使用显示名称）
        for str_name_col in self.lst_name_col:
            str_display_name = self.func_get_display_name(str_name_col)
            widget.addItem(str_display_name)
        
        # 恢复之前的选择
        if str_actual_name:
            str_new_display_name = self.func_get_display_name(str_actual_name)
            idx = widget.findText(str_new_display_name)
            if idx >= 0:
                widget.setCurrentIndex(idx)
        
        widget.blockSignals(False)
        return
    
    def _update_listwidget_for_cols(self,
        widget: QListWidget,
        text: str,
        registration: I18nRegistration
    ) -> None:
        """
        自定义更新包含列名的列表框
        
        需要同时更新列名
        """
        # 保存当前选择的实际列名
        str_current_text = widget.currentText()
        str_actual_name = self.func_get_actual_name(str_current_text)
        
        # 阻止信号
        widget.blockSignals(True)
        widget.clear()
        
        # 添加所有列名（使用显示名称）
        for str_name_col in self.lst_name_col:
            str_display_name = self.func_get_display_name(str_name_col)
            widget.addItem(str_display_name)
        
        # 恢复之前的选择
        if str_actual_name:
            str_new_display_name = self.func_get_display_name(str_actual_name)
            idx = widget.findText(str_new_display_name)
            if idx >= 0:
                widget.setCurrentIndex(idx)
        
        widget.blockSignals(False)
        return

    def _subcreate_scroll_area(self) -> QScrollArea:
        """
        创建滚动区域
        """
        scroll_area = QScrollArea() # 滚动区域的外部容器
        scroll_area.setWidgetResizable(True) # 大小自适应
        widget_scroll = QWidget() # 滚动区域的内容容器
        boxlayout_scroll = QVBoxLayout() # 滚动区域的布局
        return scroll_area, widget_scroll, boxlayout_scroll
    
    def _subcreate_container_yaxis(self,
    ) -> QWidget:
        """
        创建y轴容器
        """
        # 创建y轴容器
        container_yaxis = QWidget()
        # 垂直布局, 用于放置多个y轴配置面板
        boxlayout_container_yaxis = QVBoxLayout() 
        # 边距设为0
        boxlayout_container_yaxis.setContentsMargins(0, 0, 0, 0)
        # 设置布局
        container_yaxis.setLayout(boxlayout_container_yaxis)
        return container_yaxis, 

    def _subcreate_combobox_curves(self,
        boxlayout_curve_manager : QVBoxLayout,
        idx_subplot : int
    ) -> QComboBox:
        """
        创建下拉框形式, 备用
        """
        label_curve_candidate = self.createLabel(
            text_main="-- 可添加曲线 --",
            text_disambiguation="f_add_curve_candidate"
        )
        selector_curve_candidate = QComboBox()
        selector_curve_candidate.setObjectName(f"{self._str_name}_selector_curve_subplot_{idx_subplot}")
        selector_curve_candidate.addItems(self.lst_name_col)
        selector_curve_candidate.currentTextChanged.connect(
            lambda str_name_col, idx_subplot=idx_subplot: self.add_curve(idx_subplot, str_name_col)
        )
        ## 曲线选择器需要自定义更新（包含占位符和列名）
        self.register_i18n_widget(
            key=f"subplot_{idx_subplot}_selector_curve",
            widget=selector_curve_candidate,
            type_update=I18nUpdateType.CUSTOM,
            text_main=None,
            custom_updater=self._update_combobox_for_cols
        )
        boxlayout_curve_manager.addWidget(label_curve_candidate)
        boxlayout_curve_manager.addWidget(selector_curve_candidate)
        return selector_curve_candidate
    
    def _subcreate_listwidget_col_candidate(self,
        boxlayout_curve_manager : QVBoxLayout,
        idx_subplot : int
    ) -> QListWidget:
        """
        创建曲线列表容器用于保存可添加的曲线
        """
        label_curve_candidate = self.createLabel(
            text_main="-- 可添加曲线 --",
            text_disambiguation="f_add_curve_candidate"
        )
        selector_curve_candidate = QListWidget()
        selector_curve_candidate.setMaximumHeight(150)  # 限制高度
        selector_curve_candidate.setObjectName(f"{self._str_name}_selector_curve_subplot_{idx_subplot}")
        # 添加所有的列名
        for str_name_col_actual in self.lst_name_col:
            str_name_col_display = self.func_get_display_name(str_name_col_actual)
            selector_curve_candidate.addItem(str_name_col_display)
        # 双击添加曲线
        selector_curve_candidate.itemDoubleClicked.connect(
            lambda str_name_col, idx_subplot=idx_subplot : self.add_curve(idx_subplot, str_name_col)
        )
        ## 曲线选择器需要自定义更新（包含占位符和列名）
        self.register_i18n_widget(
            key=f"subplot_{idx_subplot}_selector_curve_candidate",
            widget=selector_curve_candidate,
            type_update=I18nUpdateType.CUSTOM,
            text_main=None,
            custom_updater=self._update_listwidget_for_cols
        )
        # 加入布局
        boxlayout_curve_manager.addWidget(label_curve_candidate)
        boxlayout_curve_manager.addWidget(selector_curve_candidate)
        return selector_curve_candidate

    def _subcreate_listwidget_col_existing(self,
        boxlayout_curve_manager : QVBoxLayout,
        idx_subplot : int
    ) -> QListWidget:
        """
        创建曲线列表容器用于保存可添加的曲线
        """
        label_curve_candidate = self.createLabel(
            text_main="-- 可添加曲线 --",
            text_disambiguation="f_add_curve_candidate"
        )
        selector_curve_candidate = QListWidget()
        selector_curve_candidate.setMaximumHeight(150)  # 限制高度
        selector_curve_candidate.setObjectName(f"{self._str_name}_selector_curve_subplot_{idx_subplot}")
        # 添加所有的列名
        for str_name_col_actual in self.lst_name_col:
            str_name_col_display = self.func_get_display_name(str_name_col_actual)
            selector_curve_candidate.addItem(str_name_col_display)
        # 双击添加曲线
        selector_curve_candidate.itemDoubleClicked.connect(
            lambda str_name_col, idx_subplot=idx_subplot : self.add_curve(idx_subplot, str_name_col)
        )
        ## 曲线选择器需要自定义更新（包含占位符和列名）
        self.register_i18n_widget(
            key=f"subplot_{idx_subplot}_selector_curve_candidate",
            widget=selector_curve_candidate,
            type_update=I18nUpdateType.CUSTOM,
            text_main=None,
            custom_updater=self._update_listwidget_for_cols
        )
        # 加入布局
        boxlayout_curve_manager.addWidget(label_curve_candidate)
        boxlayout_curve_manager.addWidget(selector_curve_candidate)
        return selector_curve_candidate

    def _create_yaxis_manager_groupbox(self,
        idx_subplot : int
    ) -> QGroupBox:
        """
        创建y轴管理分组盒子
        """
        # 初始化 "Y轴管理"分组盒子
        groupbox_yaxis_manager = QGroupBox()
        groupbox_yaxis_manager.setObjectName(f"{self._str_name}_groupbox_yaxis_subplot_{idx_subplot}")
        self.setTitle(
            widget=groupbox_yaxis_manager,
            text_main="Y轴配置",
            text_disambiguation='f_yaxis_manager',
        )
        boxlayout_yaxis_manager = QVBoxLayout()

        # 初始化 添加轴按钮
        btn_add_axis = QPushButton()
        btn_add_axis.setObjectName(f"{self._str_name}_btn_add_axis_{idx_subplot}")
        self.setText(
            widget=btn_add_axis,
            text_main="+ 添加右侧Y轴",
            text_disambiguation="f_add_yaxis"
        )
        btn_add_axis.clicked.connect(lambda: self.add_axis(idx_subplot))
        boxlayout_yaxis_manager.addWidget(btn_add_axis)
        
        # 轴列表容器
        container_yaxis = self._subcreate_container_yaxis()
        boxlayout_yaxis_manager.addWidget(container_yaxis)
        # 添加到类属性
        self.dic_container_yaxis_subplot[idx_subplot] = container_yaxis
        self.dic_layout_yaxis_subplot[idx_subplot] = boxlayout_yaxis_manager
        
        # 加入y轴管理组盒子和布局
        groupbox_yaxis_manager.setLayout(boxlayout_yaxis_manager)
        return groupbox_yaxis_manager

    def _create_curve_manager_groupbox(self,
        idx_subplot : int
    ) -> QGroupBox:
        """
        创建曲线管理分组盒子

        曲线选择设置为三个部分
            1. 下拉框形式 ComboBox: 选择需要添加的数据列
            2. 曲线列表容器
                2.1.:使用ListWidget显示已经添加的曲线配置列表
                2.2.: 显示已经添加的曲线配置面板
        """
        groupbox_curve_manager = QGroupBox()
        groupbox_curve_manager.setObjectName(f"{self._str_name}_groupbox_curve_subplot_{idx_subplot}")
        self.setTitle(
            widget=groupbox_curve_manager,
            text_main="曲线管理",
            text_disambiguation='f_curve_manager',
        )
        boxlayout_curve_manager = QVBoxLayout()
        
        # 1.添加待添加数据列的下拉框选择器
        selector_curve_candidate = self._subcreate_listwidget_col_candidate(
            boxlayout_curve_manager=boxlayout_curve_manager,
            idx_subplot=idx_subplot
        )
        
        # 2.已展示数据列的列表容器, 垂直布局
        label_curve_existing = self.createLabel(
            text_main="-- 已有曲线 --",
            text_disambiguation="f_curves_existing"
        )
        container_curve_existing = QWidget()
        boxlayout_container_curve = QVBoxLayout()
        boxlayout_container_curve.setContentsMargins(0, 0, 0, 0)
        container_curve_existing.setLayout(boxlayout_container_curve)
        boxlayout_curve_manager.addWidget(label_curve_existing)
        boxlayout_curve_manager.addWidget(container_curve_existing)
        
        # 加入曲线管理组盒子和布局
        groupbox_curve_manager.setLayout(boxlayout_curve_manager)
        return groupbox_curve_manager

    def _create_plot_tab(self,
        idx_subplot : int
    ) -> QWidget:
        """
        创建子图配置标签页

        创建滚动区域, 并提供y轴管理和曲线管理区域
        """
        widget_subplot_tab = QWidget()
        boxlayout_subplot_tab = QVBoxLayout()
        # 设定名字
        str_name_widget = f"{self._str_name}_tab_subplot_{idx_subplot}"
        widget_subplot_tab.setObjectName(str_name_widget)
        
        # 0.初始化 整体配置标签页 为 滚动区域
        scroll_area, widget_scroll, boxlayout_scroll = self._new_scroll_area()

        # 1.创建 y轴管理区域
        groupbox_yaxis_manager = self._create_yaxis_manager_groupbox(idx_subplot)
        boxlayout_scroll.addWidget(groupbox_yaxis_manager)
        
        # 2.创建 曲线管理
        groupbox_curve_manager = self._create_curve_manager_groupbox(idx_subplot)
        boxlayout_scroll.addWidget(groupbox_curve_manager)

        # 3.添加scroll伸缩空间, 防止组件挤在一起
        boxlayout_scroll.addStretch()

        # 4.添加滚动区域内容
        ## 4.1.将垂直布局应用到滚动区域的内容容器上
        widget_scroll.setLayout(boxlayout_scroll)
        # 4.2.将滚动的内容容器安装到滚动区域中，使其可滚动
        scroll_area.setWidget(widget_scroll)
        # 4.3.将滚动区域添加到主布局中
        boxlayout_subplot_tab.addWidget(scroll_area)
        # 4.4.设置主布局
        widget_subplot_tab.setLayout(boxlayout_subplot_tab)

        # 5.添加默认左侧主轴配置面板
        self._add_axis_config_panel(
            idx_subplot=idx_subplot,
            str_name_axis=self.str_name_axis_left
        )
        return widget_subplot_tab
    
    # 图配置的增删改查

    def _add_curve_panel(self,
        idx_subplot: int,
        str_name_col_actual: str
    ):
        """ 添加曲线配置面板, CurveConfigWidget
        """
        # 获取曲线配置
        curve_config = self.dic_curveconfig_subplot[idx_subplot][str_name_col_actual]
        # 创建配置面板
        panel_curve = CurveConfigWidget(
            curve_config=curve_config,
            dic_axisconfig=self.dic_axisconfig_subplot[idx_subplot],
            func_get_display_name=self.func_get_display_name
        )
        # 
        panel_curve.sig_delete_requested.connect(
            lambda name: self.remove_curve(idx_subplot, name)
        )
        panel.sig_config_changed.connect(self.sig_config_changed.emit)
        return

    def _add_curve(self,
        idx_subplot: int,
        str_name_col_display: str,
        str_name_axis: str = None
    ):
        """
        添加新轴

        1. 列的配置curveconfig
        2. 曲线配置面板的创建和添加
        """
        # 获取实际列名
        str_name_col_actual = self.func_get_actual_name(str_name_col_display)
        # 检查子图中是否已添加
        if str_name_col_actual in self.dic_added_cols_subplot[idx_subplot]:
            print(f"子图{idx_subplot}已包含列 {str_name_col_actual}，无法重复添加")
            return

        # 创建子图所对应的曲线配置
        if str_name_col_actual not in self.dic_curveconfig_subplot[idx_subplot]:
            # 不存在配置则创建新配置
            curveconfig = self._initialize_col_as_curve_in_subplot(
                str_name_col_actual=str_name_col_actual,
                idx_subplot=idx_subplot,
                str_name_axis=str_name_axis
            )
        else:
            # 已存在配置则使用已有配置
            curveconfig = self.dic_curveconfig_subplot[idx_subplot][str_name_col_actual]
        # 记录入子图正在显示的列集合
        self.dic_added_cols_subplot[idx_subplot].add(str_name_col_actual)

        # 获取可用轴列表
        lst_name_axis_avail = list(self.dic_axisconfig_subplot[idx_subplot].keys())

        # 生成轴ID
        lst_name_col = list(self.dic_axisconfig_subplot[idx_subplot].keys())
        str_name_axis = f"axis_{len(lst_name_col)}"
        # 创建轴配置
        axisconfig = AxisConfig(
            str_name_axis=str_name_axis,
            side_axis='right',
            label=f"轴 {len(lst_name_axis)}",
            color=QColor(100 + len(lst_name_axis) * 40, 100, 200)
        )
        
        self.dic_axisconfig_subplot[idx_subplot][str_name_axis] = axisconfig
        self._add_axis_config_panel(idx_subplot, str_name_axis)
        
        # 更新所有曲线的可用轴列表
        self._update_all_available_axes(idx_subplot)
        
        self.configChanged.emit()
        return
    
    def _add_axis_config_panel(self,
        idx_subplot: int,
        str_name_axis: str
    ):
        """
        添加轴配置面板
        """
        axiscofig : AxisConfig = self.dic_axisconfig_subplot[idx_subplot][str_name_axis]
        lst_name_axis_avail = list(self.dic_axisconfig_subplot[idx_subplot].keys())
        
        panel = AxisConfigPanel(axis_config, available_axes)
        panel.configChanged.connect(self.configChanged.emit)
        panel.deleteRequested.connect(lambda aid: self.remove_axis(plot_idx, aid))
        
        # 添加分隔线
        if axis_id != 'main':
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            axis_layout = getattr(self, f'plot{plot_idx}_axis_layout')
            axis_layout.addWidget(line)
        
        axis_layout = getattr(self, f'plot{plot_idx}_axis_layout')
        axis_layout.addWidget(panel)
        
        # 保存引用
        setattr(panel, '_axis_id', str_name_axis)
        setattr(panel, '_plot_idx', idx_subplot)
        return
    
    def remove_axis(self, plot_idx: int, axis_id: str):
        """移除轴"""
        if axis_id == 'main':
            return
        
        # 删除配置
        if axis_id in self.plot_axis_managers[plot_idx]:
            del self.plot_axis_managers[plot_idx][axis_id]
        
        # 删除面板
        axis_layout = getattr(self, f'plot{plot_idx}_axis_layout')
        for i in range(axis_layout.count()):
            widget = axis_layout.itemAt(i).widget()
            if isinstance(widget, AxisConfigPanel) and hasattr(widget, '_axis_id'):
                if widget._axis_id == axis_id:
                    axis_layout.removeWidget(widget)
                    widget.deleteLater()
                    # 也删除分隔线
                    if i > 0:
                        prev_widget = axis_layout.itemAt(i - 1).widget()
                        if isinstance(prev_widget, QFrame):
                            axis_layout.removeWidget(prev_widget)
                            prev_widget.deleteLater()
                    break
        
        # 更新曲线的轴选择（将使用被删除轴的曲线改为主轴）
        for curve_config in self.curve_configs[plot_idx]:
            if curve_config.axis_id == axis_id:
                curve_config.axis_id = 'main'
        
        self._update_all_available_axes(plot_idx)
        self.configChanged.emit()
    
    def add_curve(self, plot_idx: int, col_name: str):
        """添加曲线"""
        if col_name == "-- 添加曲线 --" or not col_name:
            return
        
        # 检查是否已存在
        for config in self.curve_configs[plot_idx]:
            if config.curve_name == col_name:
                return
        
        # 创建曲线配置
        colors = [
            QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
            QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)
        ]
        color_idx = len(self.curve_configs[plot_idx]) % len(colors)
        
        curve_config = CurveConfig(
            curve_name=col_name,
            plot_idx=plot_idx,
            color=colors[color_idx]
        )
        
        # 添加到列表
        self.curve_configs[plot_idx].append(curve_config)
        
        # 创建UI组件
        widget = CurveConfigWidget(
            curve_config=curve_config,
            dic_axisconfig=self.dic_axisconfig_subplot[plot_idx],
            func_get_display_name=self.func_get_display_name
        )
        widget.sig_config_changed.connect(self.sig_config_changed.emit)
        widget.deleteRequested.connect(lambda name: self.remove_curve(plot_idx, name))
        
        curve_layout = getattr(self, f'plot{plot_idx}_curve_layout')
        curve_layout.addWidget(widget)
        
        # 重置选择器
        selector = getattr(self, f'plot{plot_idx}_curve_selector')
        selector.setCurrentIndex(0)
        
        self.configChanged.emit()
    
    def remove_curve(self, plot_idx: int, curve_name: str):
        """移除曲线"""
        # 从配置中删除
        self.curve_configs[plot_idx] = [
            c for c in self.curve_configs[plot_idx]
            if c.curve_name != curve_name
        ]
        
        # 从UI删除
        curve_layout = getattr(self, f'plot{plot_idx}_curve_layout')
        for i in range(curve_layout.count()):
            widget = curve_layout.itemAt(i).widget()
            if isinstance(widget, CurveConfigWidget):
                if widget.curve_config.curve_name == curve_name:
                    curve_layout.removeWidget(widget)
                    widget.deleteLater()
                    break
        
        self.configChanged.emit()
    
    def _update_all_available_axes(self, plot_idx: int):
        """更新所有组件的可用轴列表"""
        # 曲线配置组件现在从 dic_axisconfig 动态获取，只需刷新UI
        curve_layout = getattr(self, f'plot{plot_idx}_curve_layout')
        for i in range(curve_layout.count()):
            widget = curve_layout.itemAt(i).widget()
            if isinstance(widget, CurveConfigWidget):
                widget.refresh_available_axes()
    
    def _on_span_unit_changed(self, index: int):
        """
        时间段单位改变时的回调
        """
        # 更新后缀（对应：秒、小时、天、周、月、年）
        suffixes = [" s", " hour", " day", " week", " month", " year"]
        self.spin_span.setSuffix(suffixes[index])
        # 触发时间范围更新
        self.emit_xaxis_time_range()
    
    def _get_span_in_seconds(self) -> float:
        """
        获取时间段长度（转换为秒）
        """
        value = self.spin_span.value()
        unit_index = self.combo_span_unit.currentIndex()
        
        # 转换系数（转换为秒）对应：秒、小时、天、周、月、年
        conversions = [
            1,           # 秒
            3600,        # 小时 = 3600秒
            86400,       # 天 = 24*3600秒
            604800,      # 周 = 7*24*3600秒
            2592000,     # 月 = 30*24*3600秒（近似）
            31536000     # 年 = 365*24*3600秒（近似）
        ]
        
        return value * conversions[unit_index]
    
    def emit_xaxis_time_range(self):
        """
        回调, 文字输入框触发发射时间范围改变信号
        """
        # 获取起始时间的时间戳（秒）
        flt_start = self.datetimeedit_start.dateTime().toSecsSinceEpoch()
        flt_duration = self._get_span_in_seconds()
        # 发射信号, 触发事件
        self.sig_xaxis_time_changed.emit(flt_start, flt_start + flt_duration)
        return
    
    def update_time_range(self, start: float, end: float):
        """从外部更新时间范围"""
        self.datetimeedit_start.blockSignals(True)
        self.spin_span.blockSignals(True)
        self.combo_span_unit.blockSignals(True)
        
        # 将时间戳转换为QDateTime
        self.datetimeedit_start.setDateTime(QDateTime.fromSecsSinceEpoch(int(start)))
        
        # 根据当前单位设置值（对应：秒、小时、天、周、月、年）
        duration_seconds = end - start
        unit_index = self.combo_span_unit.currentIndex()
        conversions = [1, 3600, 86400, 604800, 2592000, 31536000]
        self.spin_span.setValue(duration_seconds / conversions[unit_index])
        
        self.datetimeedit_start.blockSignals(False)
        self.spin_span.blockSignals(False)
        self.combo_span_unit.blockSignals(False)
    
    def _on_language_changed(self, str_language: str):
        """
        语言选择器改变时的回调
        """
        self.str_language_current = str_language
        
        # 调用主窗口的语言改变回调
        if self.func_on_language_changed:
            self.func_on_language_changed(str_language)
    
    def refresh_language_display(self):
        """
        刷新所有显示的文字（在切换语言后调用）
        
        使用AbstractI18nWidget的统一刷新机制
        """
        # 调用基类的统一刷新方法
        self.refresh_all_i18n()
        
        # 触发配置改变信号，让主窗口重新绘制
        self.sig_config_changed.emit()
    

    def get_plot_axes(self, plot_idx: int) -> Dict[str, AxisConfig]:
        """获取子图的轴配置"""
        return self.plot_axis_managers[plot_idx]
    
    def get_plot_curves(self, plot_idx: int) -> List[CurveConfig]:
        """获取子图的曲线配置"""
        return [c for c in self.curve_configs[plot_idx] if c.enabled]