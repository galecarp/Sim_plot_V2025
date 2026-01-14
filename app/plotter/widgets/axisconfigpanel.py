#!/usr/bin/env python3
"""
Y轴配置面板模块


"""

from typing import List, Optional, Union
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QComboBox,
    QGroupBox, QRadioButton, QCheckBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal

from app.plotter.graphconfigs.axisconfig import AxisConfig
from app.plotter.enums.modeenum import AlignmentMode, RangeMode
from app.plotter.enums.valueenum import UnitValue


class AxisConfigPanel(QWidget):
    """
    单个Y轴的配置面板

    此模块提供单个Y轴的配置面板, 用于设置Y轴的标签、单位、颜色、范围和对齐等属性。
    每个Y轴(主轴或副轴)都有一个对应的配置面板，用户可以通过面板进行交互式配置。
    
    功能说明：
    --------
    在多Y轴绘图中, 每个Y轴都有独立的配置参数 (标签、单位、颜色、范围等）。
    AxisConfigPanel 提供了一个可重用的UI组件, 用于：
    1. 显示和编辑单个Y轴的所有配置参数
    2. 支持主轴（左侧）和副轴（右侧）的不同配置需求
    3. 提供副轴与主轴的对齐功能
    4. 实时反馈配置变更，触发图表重绘
    
    主要功能：
    - 基础配置：轴标签、单位、颜色
    - 范围设置：自动范围 vs 手动范围
    - 对齐设置：副轴可选择对齐到其他轴，支持多种对齐模式
    - 删除功能：副轴可以被删除, 需要父组件处理删除请求
    
    设计模式：
    --------
    采用数据驱动UI的方式, 配置存储在 AxisConfig 对象中，
    面板作为视图层，负责展示和收集用户输入，通过信号通知外部配置变更。
    """
    
    # 信号定义
    sig_config_changed: Signal = Signal()  # 配置改变信号
    sig_delete_requested: Signal = Signal(str)  # 删除请求信号，参数为轴名称
    
    def __init__(self,
        axisconfig: AxisConfig,
        lst_name_axis_avail: List[str],
        parent: Optional[QWidget] = None
    ):
        """
        初始化轴配置面板
        
        Args:
            axisconfig: 轴配置对象，存储轴的所有配置参数
            lst_name_axis_avail: 可用的轴名称列表，用于对齐设置中选择目标轴
            parent: 父widget, 可选
        """
        super().__init__(parent)
        
        # 存储配置对象和可用轴列表
        self.axisconfig = axisconfig
        self.lst_name_axis_avail = lst_name_axis_avail
        
        # 初始化主要的布局
        self._init_layout_main()
        # 从配置对象加载初始值到UI
        self.load_config_to_ui()
        pass
    
    def _init_layout_main(self):
        """
        初始化 轴配置面板UI
        
        创建完整的轴配置面板，包括：
        1. 基础信息：标签、单位、颜色
        2. 范围设置：自动/手动模式
        3. 对齐设置（仅副轴）：对齐模式和参数
        4. 删除按钮（仅副轴）
        """
        # 主布局，使用表单布局方便标签-控件对齐
        layout_main = QFormLayout()
        
        # === 1. 基础信息区域 ===
        self._init_layout_basic_config(layout_main)

        
        # === 2. 范围设置区域 ===
        groupbox_range = self._create_range_groupbox()
        layout_main.addRow(groupbox_range)
        
        # === 3. 对齐设置区域（仅副轴显示）===
        if not self.axisconfig.bol_is_prim_axis:
            groupbox_align = self._create_alignment_groupbox()
            layout_main.addRow(groupbox_align)
        
        # === 4. 删除按钮（仅副轴显示）===
        if not self.axisconfig.bol_is_prim_axis:
            self.btn_delete = QPushButton("删除此轴")
            self.btn_delete.clicked.connect(
                lambda: self.sig_delete_requested.emit(self.axisconfig.str_name_axis)
            )
            layout_main.addRow(self.btn_delete)
        
        # 设置主布局
        self.setLayout(layout_main)
        return
    
    def _init_layout_basic_config(self,
        layout_main: QFormLayout
    ):
        """
        初始化 轴 基础信息区域布局

        包括:
            1. 轴标签
            2. 轴数值的单位
            3. 颜色选择
        """
        # 1.1轴标签输入框
        edit_label = QLineEdit()
        edit_label.textChanged.connect(self.on_anything_changed)
        layout_main.addRow("轴标签:", edit_label)
        
        # 1.2.轴单位下拉框（从UnitValue枚举中选择）
        combo_unit = QComboBox()
        # 添加所有可用的单位，显示枚举的value（字符串）
        combo_unit.addItems([unit.value for unit in UnitValue])
        combo_unit.setEditable(True)  # 允许用户输入自定义单位
        combo_unit.currentTextChanged.connect(self.on_anything_changed)
        layout_main.addRow("单位:", combo_unit)
        
        # 1.3轴颜色选择按钮
        layout_color = QHBoxLayout()
        btn_color = QPushButton()
        btn_color.setFixedSize(60, 25)  # 固定按钮大小
        btn_color.clicked.connect(self._select_color_axis_process)
        layout_color.addWidget(btn_color)
        layout_color.addStretch()  # 添加弹性空间，将按钮推到左侧
        layout_main.addRow("轴颜色:", layout_color)
        
        # 存储控件引用
        self.edit_label = edit_label
        self.combo_unit = combo_unit
        self.btn_color = btn_color
        return
    
    def _create_range_groupbox(self) -> QGroupBox:
        """
        创建范围设置分组盒子
        
        范围设置包括：
        - 自动模式: 根据数据自动调整Y轴范围
        - 手动模式: 用户指定Y轴的最小值和最大值
        
        Returns:
            QGroupBox: 范围设置的分组盒子
        """
        # 分组盒子
        groupbox_range = QGroupBox("范围设置")
        boxlayout_range = QVBoxLayout()
        
        # 1.创建单选按钮：自动 vs 手动
        self.radiobtn_range_auto = QRadioButton("自动")
        self.radiobtn_range_manual = QRadioButton("手动")
        self.radiobtn_range_auto.toggled.connect(self.on_range_mode_changed)
        boxlayout_range.addWidget(self.radiobtn_range_auto)
        boxlayout_range.addWidget(self.radiobtn_range_manual)
        
        # 2.手动范围输入控件
        layout_manual = QFormLayout()
        
        ## 2.1.最小值输入框
        self.spin_range_min = QDoubleSpinBox()
        self.spin_range_min.setRange(-1e9, 1e9)  # 设置输入范围
        self.spin_range_min.setDecimals(3)  # 小数位数
        self.spin_range_min.valueChanged.connect(self.on_anything_changed)
        
        ## 2.2.最大值输入框
        self.spin_range_max = QDoubleSpinBox()
        self.spin_range_max.setRange(-1e9, 1e9)
        self.spin_range_max.setDecimals(3)
        self.spin_range_max.valueChanged.connect(self.on_anything_changed)
        
        layout_manual.addRow("最小值:", self.spin_range_min)
        layout_manual.addRow("最大值:", self.spin_range_max)
        boxlayout_range.addLayout(layout_manual)
        
        groupbox_range.setLayout(boxlayout_range)
        return groupbox_range
    
    def _create_alignment_groupbox(self) -> QGroupBox:
        """
        创建对齐设置分组盒子（仅副轴需要）
        
        对齐功能允许副轴与其他轴进行坐标对齐，确保不同Y轴的数值在视觉上有意义的对应关系。
        
        支持的对齐模式：
        - NONE: 不对齐
        - VALUE: 指定值对齐 - 将本轴的某个值对齐到目标轴的某个值
        - RANGE_RATIO: 比例对齐 - 设置本轴范围与目标轴范围的比例关系
        
        Returns:
            QGroupBox: 对齐设置的分组盒子
        """
        # 分组盒子
        groupbox_align = QGroupBox("对齐设置")
        boxlayout_align = QVBoxLayout()
        
        # 1.启用对齐复选框
        self.checkbox_align_enable = QCheckBox("启用对齐")
        self.checkbox_align_enable.stateChanged.connect(self.on_alignment_enable_state_changed)
        boxlayout_align.addWidget(self.checkbox_align_enable)
        
        # 2.对齐到哪个轴
        layout_align_to_axis = QFormLayout()
        self.combo_align_to_axis = QComboBox()
        self.combo_align_to_axis.currentTextChanged.connect(self.on_anything_changed)
        layout_align_to_axis.addRow("对齐到轴:", self.combo_align_to_axis)
        boxlayout_align.addLayout(layout_align_to_axis)
        
        # 3.对齐模式选择
        self.combo_align_mode = QComboBox()
        ## 3.1.添加所有对齐模式（除了NONE，因为NONE通过取消勾选"启用对齐"实现）
        self.combo_align_mode.addItems([
            mode.value for mode in AlignmentMode if mode != AlignmentMode.NONE
        ])
        self.combo_align_mode.currentTextChanged.connect(self.on_align_mode_changed)
        layout_align_to_axis.addRow("对齐模式:", self.combo_align_mode)
        
        # 4. 一次性创建所有对齐参数控件（根据模式启用/禁用，而非删除/创建）
        self.layout_align_params = QFormLayout()
        self._create_all_alignment_param_widgets()
        boxlayout_align.addLayout(self.layout_align_params)
        
        groupbox_align.setLayout(boxlayout_align)
        return groupbox_align
    
    # === plot的配置区域 ===
    def _update_color_button(self):
        """
        更新颜色按钮的显示
        
        将颜色按钮的背景色设置为配置对象中的颜色值，
        让用户可以直观地看到当前选择的颜色。
        """
        self.btn_color.setStyleSheet(
            f"background-color: {self.axisconfig.color.name()}; "
            f"border: 1px solid #888;"
        )
        return
    
    def _select_color_axis_process(self):
        """
        选择颜色对话框
        
        弹出颜色选择对话框，让用户选择轴的颜色。
        选择的颜色会应用到配置对象，并更新按钮显示。
        """
        color = QColorDialog.getColor(
            initial=self.axisconfig.color,
            parent=self,
            title="选择轴颜色"
        )
        
        # 检查用户是否选择了有效颜色（未取消）
        if color.isValid():
            # 更新配置对象
            self.axisconfig.color = color
            # 更新按钮显示
            self._update_color_button()
            # 触发配置变更信号
            self.on_anything_changed()
        return
    
    def _update_axis_combo_align_to_axis(self,
        lst_name_axis_avail: List[str]
    ):
        """
        更新可用轴列表
        
        当子图中的轴发生变化时（如添加或删除轴），需要调用此函数更新对齐设置中的
        可选目标轴列表。确保下拉框中显示的是最新的可用轴。
        
        Args:
            lst_name_axis: 可用的轴名称列表
        """
        str_name_combo_align_to_axis = 'combo_align_to_axis'
        # 检查是否有对齐下拉框（仅副轴有）
        if not hasattr(self, str_name_combo_align_to_axis):
            return
        
        # 保存当前选择的轴名
        self.lst_name_axis_avail = lst_name_axis_avail
        str_name_axis_align_to = self.combo_align_to_axis.currentText()
        
        # 清空并重新填充下拉框
        self.combo_align_to_axis.clear()
        
        # 过滤掉自己（不能对齐到自己）
        lst_name_axis_can_align_to = [
            str_name_axis for str_name_axis in lst_name_axis_avail 
            if str_name_axis != self.axisconfig.str_name_axis
        ]
        self.combo_align_to_axis.addItems(lst_name_axis_can_align_to)
        
        # 如果之前选择的轴还在列表中，恢复选择
        if str_name_axis_align_to in lst_name_axis_can_align_to:
            self.combo_align_to_axis.setCurrentText(str_name_axis_align_to)
        return

    # === 辅助函数区域 ===
    def _create_all_alignment_param_widgets(self):
        """
        一次性创建所有可能的对齐参数控件
        
        创建所有对齐模式可能需要的控件，初始状态下隐藏。
        根据用户选择的对齐模式，动态显示/隐藏和启用/禁用相应控件。
        这样避免了频繁创建/删除控件，提供更流畅的用户体验。
        """
        # VALUE模式参数：本轴值
        self.spin_align_value_src = QDoubleSpinBox()
        self.spin_align_value_src.setRange(-1e9, 1e9)
        self.spin_align_value_src.setDecimals(5)
        self.spin_align_value_src.setValue(self.axisconfig.flt_align_src)
        self.spin_align_value_src.valueChanged.connect(self.on_anything_changed)
        
        # VALUE模式参数：目标轴值
        self.spin_align_value_tgt = QDoubleSpinBox()
        self.spin_align_value_tgt.setRange(-1e9, 1e9)
        self.spin_align_value_tgt.setDecimals(5)
        self.spin_align_value_tgt.setValue(self.axisconfig.flt_align_tgt)
        self.spin_align_value_tgt.valueChanged.connect(self.on_anything_changed)
        
        # VALUESCALE模式参数：拉伸系数
        self.spin_scale_span = QDoubleSpinBox()
        self.spin_scale_span.setRange(0.0, 1e6)
        self.spin_scale_span.setDecimals(5)
        self.spin_scale_span.setValue(self.axisconfig.flt_ratio_scale)
        self.spin_scale_span.valueChanged.connect(self.on_anything_changed)
        
        # 添加到布局
        self.layout_align_params.addRow("本轴值:", self.spin_align_value_src)
        self.layout_align_params.addRow("目标轴值:", self.spin_align_value_tgt)
        self.layout_align_params.addRow("对齐跨度的拉伸系数:", self.spin_scale_span)
        
        # 初始状态：所有控件都隐藏
        self._set_alignment_params_visibility(AlignmentMode.ZERO)
        return

    def _set_alignment_params_visibility(self,
        mode_align: AlignmentMode
    ):
        """
        根据对齐模式设置参数控件的可见性和启用状态
        
        Args:
            mode_align: 对齐模式
            
        不同模式需要的参数：
        - ZERO: 无参数
        - VALUE: 本轴值 + 目标轴值
        - VALUESCALE: 本轴值 + 目标轴值 + 拉伸系数
        """
        # 根据模式决定哪些控件可见和启用
        if mode_align == AlignmentMode.ZERO:
            # ZERO模式：隐藏所有参数
            self.spin_align_value_src.setVisible(False)
            self.spin_align_value_tgt.setVisible(False)
            self.spin_scale_span.setVisible(False)
            # 同时隐藏标签
            self.layout_align_params.labelForField(self.spin_align_value_src).setVisible(False)
            self.layout_align_params.labelForField(self.spin_align_value_tgt).setVisible(False)
            self.layout_align_params.labelForField(self.spin_scale_span).setVisible(False)
            
        elif mode_align == AlignmentMode.VALUE:
            # VALUE模式：显示本轴值和目标轴值，隐藏拉伸系数
            self.spin_align_value_src.setVisible(True)
            self.spin_align_value_src.setEnabled(True)
            self.spin_align_value_tgt.setVisible(True)
            self.spin_align_value_tgt.setEnabled(True)
            self.spin_scale_span.setVisible(False)
            # 显示对应标签
            self.layout_align_params.labelForField(self.spin_align_value_src).setVisible(True)
            self.layout_align_params.labelForField(self.spin_align_value_tgt).setVisible(True)
            self.layout_align_params.labelForField(self.spin_scale_span).setVisible(False)
            
        elif mode_align == AlignmentMode.VALUESCALE:
            # VALUESCALE模式：显示所有参数
            self.spin_align_value_src.setVisible(True)
            self.spin_align_value_src.setEnabled(True)
            self.spin_align_value_tgt.setVisible(True)
            self.spin_align_value_tgt.setEnabled(True)
            self.spin_scale_span.setVisible(True)
            self.spin_scale_span.setEnabled(True)
            # 显示所有标签
            self.layout_align_params.labelForField(self.spin_align_value_src).setVisible(True)
            self.layout_align_params.labelForField(self.spin_align_value_tgt).setVisible(True)
            self.layout_align_params.labelForField(self.spin_scale_span).setVisible(True)
        return

    @staticmethod
    def _convert_str_to_unitvalue(
        str_unit: str
    ) -> UnitValue:
        """
        将UnitValue枚举转换为字符串
        
        Args:
            unit_value: UnitValue枚举
            
        Returns:
            str: 对应的字符串表示
        """
        try:
            # 尝试通过字符串值匹配枚举
            unit_value = UnitValue(str_unit)
        except ValueError:
            # 如果输入的是自定义字符串（不在枚举中），保持原值
            raise ValueError(f"Invalid unit string: {str_unit}")
        return unit_value

    # === 回调函数区域 ===
    def on_alignment_enable_state_changed(self,
        int_state_checkbox: int
    ):
        """
        对齐启用状态改变回调
        
        当用户勾选/取消勾选"启用对齐"时触发。
        更新配置对象的对齐模式，并触发配置变更信号。
        
        Args:
            int_state_checkbox: 复选框状态值
        """
        # 判断是否启用对齐
        bol_alignment_enabled = int_state_checkbox == Qt.CheckState.Checked.value
        
        # 启用/禁用对齐相关控件
        self.combo_align_to_axis.setEnabled(bol_alignment_enabled)
        self.combo_align_mode.setEnabled(bol_alignment_enabled)
        
        if bol_alignment_enabled:
            # 启用对齐：从下拉框获取当前选择的对齐模式
            str_mode = self.combo_align_mode.currentText()
            mode_align = AlignmentMode(str_mode)
            self.axisconfig.mode_align = mode_align
            # 显示对应的参数控件
            self._set_alignment_params_visibility(mode_align)
        else:
            # 禁用对齐：设置为NONE模式并隐藏所有参数
            self.axisconfig.mode_align = AlignmentMode.NONE
            self._set_alignment_params_visibility(AlignmentMode.ZERO)
        
        # 触发配置变更信号
        self.on_anything_changed()
        pass

    def on_align_mode_changed(self,
        mode_align: Union[str, AlignmentMode]
    ):
        """
        对齐模式改变回调
        
        当用户切换对齐模式时触发。
        根据新的对齐模式，显示/隐藏相应的参数输入控件。
        
        Args:
            mode_align: 对齐模式（字符串或枚举）
        """
        # 转换为枚举类型
        if isinstance(mode_align, str):
            mode_align = AlignmentMode(mode_align)
        
        # 更新配置对象
        self.axisconfig.mode_align = mode_align
        
        # 根据模式显示/隐藏对应的参数控件
        self._set_alignment_params_visibility(mode_align)
            
        # 仅在启用对齐时触发配置变更信号
        if self.checkbox_align_enable.isChecked():
            self.on_anything_changed()
        return
    
    def on_range_mode_changed(self):
        """
        范围模式改变回调
        
        当用户切换"自动"和"手动"单选按钮时触发。
        更新配置对象的范围模式，并触发配置变更信号。
        """
        if self.radiobtn_range_auto.isChecked():
            # 选择了自动模式
            self.axisconfig.mode_range = RangeMode.AUTO
        else:
            # 选择了手动模式
            self.axisconfig.mode_range = RangeMode.MANUAL
        
        # 触发配置变更信号
        self.on_anything_changed()
        pass
  
    def on_anything_changed(self):
        """
        任何设置改变都应该触发的回调
        
        此函数负责将UI的当前值同步到配置对象中, 并发射配置变更信号。
        
        同步的配置项包括：
        - 基础信息：标签、单位
        - 范围参数：最小值、最大值
        - 对齐参数：对齐目标轴、对齐值、对齐比例等
        """
        # 保存UI数据到配置对象
        self.save_ui_to_config()
        
        # 发射配置变更信号，通知外部组件
        self.sig_config_changed.emit()
        return
    
    # === axisconfig同步到config的函数区域 ===
    def _sync_basic_info_to_config(self):
        """
        将基础信息同步到配置对象
        
        包括：
        - 轴标签
        - 轴单位
        """
        self.axisconfig.str_label = self.edit_label.text()
        # 将下拉框的字符串转换为UnitValue枚举
        str_unit = self.combo_unit.currentText()
        unit_value = AxisConfigPanel._convert_str_to_unitvalue(str_unit)
        self.axisconfig.unit_value = unit_value
        return
    
    def _sync_range_to_config(self):
        """
        将范围设置同步到配置对象
        
        包括：
        - 范围模式（自动/手动）
        - 最小值和最大值（仅手动模式）
        """
        self.axisconfig.lb_range = self.spin_range_min.value()
        self.axisconfig.ub_range = self.spin_range_max.value()
        return
    
    def _sync_alignment_to_config(self):
        """
        将对齐设置同步到配置对象
        
        包括：
        - 对齐启用状态
        - 对齐目标轴
        - 对齐模式
        - 对齐参数（根据模式）
        """
        if not self.axisconfig.bol_is_prim_axis and hasattr(self, 'combo_align_to_axis'):
            # 对齐目标轴
            self.axisconfig.str_name_axis_align = self.combo_align_to_axis.currentText()
            
            # VALUE模式的对齐参数
            if hasattr(self, 'spin_align_value_src'):
                self.axisconfig.flt_align_src = self.spin_align_value_src.value()
                self.axisconfig.flt_align_tgt = self.spin_align_value_tgt.value()
            
            # VALUESCALE模式的对齐参数
            if hasattr(self, 'spin_scale_span'):
                self.axisconfig.flt_ratio_scale = self.spin_scale_span.value()
        return

    def save_ui_to_config(self):
        """
        保存UI数据到配置对象
        
        加载的配置项包括：
        - 基础信息：标签、单位、颜色
        - 范围设置：模式和数值
        - 对齐设置：启用状态、目标轴、对齐模式等
        """
        # 1.加载基础信息
        self._sync_basic_info_to_config()
        # 2.加载范围设置
        self._sync_range_to_config()
        # 3.加载对齐设置
        self._sync_alignment_to_config()
        return
    
    # === axisconfig同步自config的函数区域 ===
    def _sync_basic_info_fr_config(self):
        """
        将基础信息从配置对象同步到UI
        
        包括：
        - 轴标签
        - 轴单位
        - 颜色
        """
        self.edit_label.setText(self.axisconfig.str_label)
        # 将UnitValue枚举的.value属性（字符串）设置到下拉框
        self.combo_unit.setCurrentText(self.axisconfig.unit_value.value)
        # 
        self._update_color_button()  # 更新颜色按钮显示
        return

    def _sync_range_fr_config(self):
        """
        将范围设置从配置对象同步到UI
        
        包括：
        - 范围模式（自动/手动）
        - 最小值和最大值（仅手动模式）
        """
        # 设置范围模式
        if self.axisconfig.mode_range == RangeMode.AUTO:
            self.radiobtn_range_auto.setChecked(True)
        else:
            self.radiobtn_range_manual.setChecked(True)
        # 读取最小值和最大值
        self.spin_range_min.setValue(self.axisconfig.lb_range)
        self.spin_range_max.setValue(self.axisconfig.ub_range)
        return

    def _sync_alignment_fr_config(self):
        """
        将对齐设置从配置对象同步到UI
        
        包括：
        - 对齐启用状态
        - 对齐目标轴
        - 对齐模式
        - 对齐参数（根据模式）
        """
        if not self.axisconfig.bol_is_prim_axis:
            # 更新可用轴列表进入下拉框
            self._update_axis_combo_align_to_axis(self.lst_name_axis_avail)
            
            # 如果配置了对齐
            if self.axisconfig.mode_align != AlignmentMode.NONE:
                self.checkbox_align_enable.setChecked(True)
                # 设置对齐目标轴
                if self.axisconfig.str_name_axis_align:
                    self.combo_align_to_axis.setCurrentText(self.axisconfig.str_name_axis_align)
        return
    
    def load_config_to_ui(self):
        """
        从配置对象加载数据到UI
        
        在面板初始化时调用, 将配置对象中存储的值填充到UI控件中。
        这样用户看到的是之前保存的配置，而不是空白或默认值。
        
        加载的配置项包括：
        - 基础信息：标签、单位、颜色
        - 范围设置：模式和数值
        - 对齐设置：启用状态、目标轴、对齐模式等
        """
        # 1.加载基础信息
        self._sync_basic_info_fr_config()
        # 2.加载范围设置
        self._sync_range_fr_config()
        # 3.加载对齐设置
        self._sync_alignment_fr_config()
        return
