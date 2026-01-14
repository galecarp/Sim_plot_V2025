#!/usr/bin/env python3

"""X轴(时间轴)管理 UI 组件"""
from typing import Optional, Callable, Dict, Tuple, override
from PySide6.QtWidgets import (
    QWidget, QDateTimeEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QHBoxLayout, QFormLayout, QLabel
)
from PySide6.QtCore import QDateTime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .base import BaseUIComponents


class XAxisUIComponents(BaseUIComponents):
    """
    X轴(时间轴)相关的 UI 组件容器
    
    管理时间设置相关的UI组件：
    - 起始时间选择器
    - 时间跨度输入框
    - 时间单位选择器
    
    Attributes:
        tab_widget: 时间设置标签页 Widget
        datetimeedit_start: 起始时间选择器
        spin_span: 时间跨度输入框
        combo_span_unit: 时间单位选择器
        hbox_span: 跨度和单位的水平布局
    """
    
    def __init__(self):
        # UI组件引用
        self.widget_tab: Optional[QWidget] = None
        self.datetimeedit_start: Optional[QDateTimeEdit] = None
        self.spin_span: Optional[QDoubleSpinBox] = None
        self.combo_span_unit: Optional[QComboBox] = None
        self.hbox_span: Optional[QHBoxLayout] = None
        # 时间展示
        self.str_format_datetime: str = "yyyy-MM-dd HH:mm:ss"
        # 初始化时间跨度单位映射
        self.dic_map_unit_span : Dict[int, Dict[str, str]] = {}
        self._init_dic_map_unit_span()
        pass

    def _init_dic_map_unit_span(self):
        """
        初始化时间跨度单位映射

        时间单位为datetime timedelta可识别的字符串
        """
        self.dic_map_unit_span = {
            # 小时
            0: {
                'display' : '小时',
                'disambiguation' : 'f_time_hour',
                'unit_datetime' : 'hours',
                'func_calc_end' : self._calc_timestamp_yield,
                'n_metric_lower': None,
            },  
            # 天
            1: {
                'display' : '天',
                'disambiguation' : 'f_time_day',
                'unit_datetime' : 'days',
                'func_calc_end' : self._calc_timestamp_regular,
                'n_metric_lower': 24,
            },
            # 月
            2: {
                'display' : '月',
                'disambiguation' : 'f_time_month',
                'unit_datetime' : 'months',
                'func_calc_end' : self._calc_timestamp_regular,
                'n_metric_lower': None,
            }, 
            # 年
            3: {
                'display' : '年',
                'disambiguation' : 'f_time_year',
                'unit_datetime' : 'years',
                'func_calc_end' : self._calc_timestamp_regular,
                'n_metric_lower': 12,
            }   
        }
        pass
    
    @override
    def create_widgets(self,
        parent: Optional[QWidget] = None,
        str_prefix_name: str = "xaxis",
        func_tr: Optional[Callable[[str, str], str]] = None,
        **kwargs
    ) -> 'XAxisUIComponents':
        """
        创建时间轴UI组件
        
        Args:
            parent: 父widget
            name_prefix: 组件名称前缀
            tr_func: 翻译函数
            
        Returns:
            self，支持链式调用
        """
        func_tr = func_tr or (lambda text, ctx='': text)
        
        # 创建主widget
        self.widget_tab = QWidget(parent)
        self.widget_tab.setObjectName(f"{str_prefix_name}_tab")
        layout = QFormLayout()
        
        # 创建起始时间选择器
        self.datetimeedit_start : QDateTimeEdit = self._create_datetimeedit_start(
            str_prefix_name=str_prefix_name
        )
        
        # 创建时间跨度输入框
        self.spin_span : QDoubleSpinBox = self._create_spin_span(
            str_prefix_name=str_prefix_name
        )
        
        # 创建单位选择器
        self.combo_span_unit : QComboBox = self._create_combo_span_unit(
            str_prefix_name=str_prefix_name,
            func_tr=func_tr
        )
        
        # 创建水平布局
        self.hbox_span = QHBoxLayout()
        self.hbox_span.addWidget(self.spin_span)
        self.hbox_span.addWidget(self.combo_span_unit)
        
        # 组装到主布局
        layout.addRow(
            QLabel(func_tr("起始时间: ", 'f_start_time')), 
            self.datetimeedit_start
        )
        layout.addRow(
            QLabel(func_tr("时间跨度/单位: ", 'f_time_span')),
            self.hbox_span
        )
        # 设置布局
        self.widget_tab.setLayout(layout)
        return self
    
    @override
    def connect_signals(self, **callbacks) -> 'XAxisUIComponents':
        """
        连接信号到回调函数
        
        Args:
            **callbacks: 支持以下回调:
                - on_time_changed: 时间改变时的回调
                - on_unit_changed: 单位改变时的回调
                
        Returns:
            self，支持链式调用
        """
        if on_time_changed := callbacks.get('on_time_changed'):
            if self.datetimeedit_start:
                self.datetimeedit_start.dateTimeChanged.connect(on_time_changed)
            if self.spin_span:
                self.spin_span.valueChanged.connect(on_time_changed)
            
        if on_unit_changed := callbacks.get('on_unit_changed'):
            if self.combo_span_unit:
                self.combo_span_unit.currentIndexChanged.connect(on_unit_changed)
            
        return self
    
    @override
    def get_main_widget(self) -> Optional[QWidget]:
        """获取主widget"""
        return self.widget_tab
    
    # ============================================================
    # 起始时间相关方法
    # ============================================================
    def _create_datetimeedit_start(self,
        str_prefix_name: str = "xaxis",
    ) -> QDateTimeEdit:
        """
        创建起始时间选择器
        """
        datetimeedit_start = QDateTimeEdit(self.widget_tab)
        datetimeedit_start.setObjectName(f"{str_prefix_name}_datetimeedit_start")
        datetimeedit_start.setDateTime(QDateTime.currentDateTime())
        datetimeedit_start.setDisplayFormat(self.str_format_datetime)
        datetimeedit_start.setCalendarPopup(True)
        return datetimeedit_start

    # ============================================================
    # 时间跨度Combo 和 spin相关方法
    # ============================================================
    def _split_float_part(self, flt_value: float) -> Tuple[int, float]:
        """ 拆分整数和小数部分
        """
        int_part = int(flt_value)
        float_part = flt_value - int_part
        return int_part, float_part

    def _calc_timestamp_yield(self,
        ts_timestamp_start: datetime,
        flt_val_span: float,
        idx_unit: int=None,
    ) -> datetime:
        """ 对于小时以下的小数, 直接放弃
        """
        int_part, float_part = self._split_float_part(flt_val_span)
        # 提取单位类型
        str_unit_datetime = self.dic_map_unit_span[idx_unit]['unit_datetime']
        # 计算时间
        ts_timestamp = (
            ts_timestamp_start
            + relativedelta(**{str_unit_datetime: int_part}))
        return ts_timestamp
    
    def _calc_timestamp_regular(self,
        ts_timestamp_start: datetime,
        flt_val_span: float,
        idx_unit: int=None,
    ) -> datetime:
        """ 规则的转化
        """
        int_part, float_part = self._split_float_part(flt_val_span)
        # 提取单位类型
        str_unit_datetime = self.dic_map_unit_span[idx_unit]['unit_datetime']
        # 提取下一个更小单位的类型
        idx_unit_lower = idx_unit - 1
        str_unit_datetime_lower = self.dic_map_unit_span[idx_unit_lower]['unit_datetime']
        # 提取向下一级转换的比例
        n_scale_metric_lower = self.dic_map_unit_span[idx_unit]['n_metric_lower']
        # 计算小数部分对应的更小单位数值
        int_part_metric_lower = int(float_part * n_scale_metric_lower)
        # 计算结束时间
        ts_timestamp = (
            ts_timestamp_start
            + relativedelta(**{str_unit_datetime: int_part})
            + relativedelta(**{str_unit_datetime_lower: int_part_metric_lower}))
        return ts_timestamp
    
    def _calc_timestamp_month(self,
        ts_timestamp_start: datetime,
        flt_val_span: float,
        idx_unit: int=None,
    ) -> datetime:
        """ 对于月的非规则转化
        """
        int_part, float_part = self._split_float_part(flt_val_span)
        # 计算整数部分的结束时间
        ts_timestamp_month = (
            ts_timestamp_start
            + relativedelta(months=int_part))
        # 计算小数部分对应的天数
        # 计算下一个月的实际天数
        ts_timestamp_full_month_end = ts_timestamp_month + relativedelta(months=1)
        n_days_full_month = (ts_timestamp_full_month_end - ts_timestamp_month).days
        # 加上小数部分对应的天数
        n_days_float_equiv = int(n_days_full_month * float_part)
        ts_timestamp = ts_timestamp_month + relativedelta(days=n_days_float_equiv)
        return ts_timestamp

    def _calc_timestamp_end(self,
        ts_timestamp_start: datetime,
        flt_val_span: float,
        idx_unit: int=None,
    ) -> datetime:
        """ 计算结束时间戳
        需要考虑到小数的问题，将小数部分转换为更小的时间单位
        
        对于"月"单位：
        - 整数部分使用relativedelta精确计算
        - 小数部分通过计算实际月份/年份天数来转换
        
        对于其他单位：
        - 直接使用relativedelta计算, 并只提取下一级的单位, 进行小数转换
        
        Args:
            ts_timestamp_start: 开始的时间戳
            flt_val_span: 输入的跨度数值（可以是小数）
            idx_unit: dic_map_unit_span中的单位索引
                0: 小时, 1: 天, 2: 月, 3: 年

        Returns:
            结束时间戳
        """
        # 获取处理时间的函数
        func_calc_end : Callable[[datetime, float, int], datetime] = self.dic_map_unit_span[idx_unit]['func_calc_end']
        # 计算结束时间
        ts_timestamp_end = func_calc_end(
            ts_timestamp_start=ts_timestamp_start,
            flt_val_span=flt_val_span,
            idx_unit=idx_unit)
        return ts_timestamp_end

    def _rounddown_timestamp(self,
        ts_timestamp: datetime,
        idx_unit: int=None,
    ):
        """ 根据当前时间戳以及设置的时间单位进行取整
        规则为取下一个更小单位的整数倍, 再化为对应的小数部分
        """
        # 获取处理时间的函数
        func_calc : Callable[[datetime, float, int], datetime] = self.dic_map_unit_span[idx_unit]['func_calc_end']
        # 计算取整后的时间戳
        ts_timestamp = func_calc(
            ts_timestamp_start=ts_timestamp,
            flt_val_span=0,
            idx_unit=idx_unit)
        return ts_timestamp
    
    def _select_unit_for_timedelta(self,
        ts_timestamp_start: datetime,
        ts_timestamp_end: datetime
    ) -> int:
        """ 为给定的时间范围选择合适的时间单位的序号
        """
        int_unit_datetime = 0
        return int_unit_datetime

    def _create_spin_span(self,
        str_prefix_name: str = "xaxis",
    ) -> QDoubleSpinBox:
        """
        创建时间跨度输入框, 只允许正数
            
        Returns:
            时间跨度输入框
        """
        spin_span = QDoubleSpinBox(self.widget_tab)
        spin_span.setObjectName(f"{str_prefix_name}_spin_span")
        spin_span.setRange(1, 1e9)
        spin_span.setValue(100)
        return spin_span

    def _create_combo_span_unit(self,
        str_prefix_name: str = "xaxis",
        func_tr: Optional[Callable[[str, str], str]] = None,
    ) -> QComboBox:
        """
        创建时间跨度单位选择器
            
        Returns:
            时间单位选择器
        """
        combo_span_unit = QComboBox(self.widget_tab)
        combo_span_unit.setObjectName(f"{str_prefix_name}_combo_unit")
        combo_span_unit.addItems([
            func_tr(dic_single["display"], dic_single["disambiguation"])
            for dic_single in self.dic_map_unit_span.values()
        ])
        return combo_span_unit
    
    def get_unit_span_timedelta(self) -> str:
        """
        获取当前选择的时间单位字符串, 并转化为datetime可识别的时间单位字符串
        
        Returns:
            datetime timedelta可识别的时间单位字符串
        """
        if not self.combo_span_unit:
            return None
        int_unit_index = self.combo_span_unit.currentIndex()
        return self.dic_map_unit_span[int_unit_index]['unit_datetime']

    def get_value_span_timedelta(self) -> float:
        """
        获取当前时间跨度数值

        """
        if not self.spin_span:
            return None
        return float(self.spin_span.value())

    def get_timestamp_end(self) -> datetime:
        """
        根据起始时间和跨度计算结束时间戳
        """        
        ts_timestamp_start : datetime  = self.datetimeedit_start.dateTime()
        float_val_span = float(self.spin_span.value())
        idx_unit = self.combo_span_unit.currentIndex()
        
        # 根据单位类型进行日期运算
        ts_timestamp_end = self._calc_timestamp_end(
            ts_timestamp_start=ts_timestamp_start,
            flt_val_span=float_val_span,
            idx_unit=idx_unit
        )
        return ts_timestamp_end
    
    def get_timestamp_start(self) -> datetime:
        """
        获取起始时间戳
        
        Returns:
            起始时间的Unix时间戳
        """
        return self.datetimeedit_start
    
    def set_time_range(self,
        ts_timestamp_start: datetime,
        ts_timestamp_end: datetime
    ):
        """
        根据x轴拖拉条的反馈, 设置时间范围（阻止信号）
        设置内容:
        - 设置起始时间
        - 根据跨度时长选择
        根据起止时间和当前选择的单位,反向计算跨度值
        """
        # 阻止信号
        self.datetimeedit_start.blockSignals(True)
        self.spin_span.blockSignals(True)
        self.combo_span_unit.blockSignals(True)
        
        # 设置起始时间
        self.datetimeedit_start.setDateTime(
            QDateTime.fromSecsSinceEpoch(int(ts_timestamp_start.timestamp()))
        )
        
        # 根据当前单位计算跨度值
        str_unit_datetime = self.get_timedelta_unit_span()
        
        # 使用relativedelta计算时间差
        delta = relativedelta(ts_timestamp_end, ts_timestamp_start)
        
        # 根据单位提取对应的数值
        unit_values = {
            'hours': delta.hours + delta.days * 24,
            'days': delta.days,
            'weeks': delta.days // 7,
            'months': delta.months + delta.years * 12,
            'years': delta.years
        }
        
        span_value = unit_values.get(str_unit_datetime, 0)
        self.spin_span.setValue(span_value)
        
        # 恢复信号
        self.datetimeedit_start.blockSignals(False)
        self.spin_span.blockSignals(False)
        self.combo_span_unit.blockSignals(False)
        return
