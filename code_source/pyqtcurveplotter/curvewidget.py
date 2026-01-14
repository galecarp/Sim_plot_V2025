#!/usr/bin/env python3

class CurveConfigWidget(QWidget):
    """单条曲线的配置组件"""
    configChanged = pyqtSignal()
    deleteRequested = pyqtSignal(str)  # curve_name
    
    def __init__(self, curve_config: CurveConfig, available_axes: List[str], parent=None):
        super().__init__(parent)
        self.curve_config = curve_config
        self.available_axes = available_axes
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 启用复选框
        self.enable_check = QCheckBox(self.curve_config.curve_name)
        self.enable_check.stateChanged.connect(self.on_config_changed)
        layout.addWidget(self.enable_check)
        
        # 所属轴选择
        self.axis_combo = QComboBox()
        self.axis_combo.setMinimumWidth(80)
        self.axis_combo.currentTextChanged.connect(self.on_config_changed)
        layout.addWidget(self.axis_combo)
        
        # 颜色按钮
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 20)
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        
        # 线型
        self.style_combo = QComboBox()
        self.style_combo.addItems(['实线', '虚线', '点线', '点划线'])
        self.style_combo.currentIndexChanged.connect(self.on_config_changed)
        layout.addWidget(self.style_combo)
        
        # Step模式
        self.step_check = QCheckBox('Step')
        self.step_check.stateChanged.connect(self.on_config_changed)
        layout.addWidget(self.step_check)
        
        # 删除按钮
        delete_btn = QPushButton('×')
        delete_btn.setFixedSize(25, 20)
        delete_btn.clicked.connect(
            lambda: self.deleteRequested.emit(self.curve_config.curve_name)
        )
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_config(self):
        """加载配置"""
        self.enable_check.setChecked(self.curve_config.enabled)
        self.update_color_button()
        self.step_check.setChecked(self.curve_config.is_step)
        self.update_available_axes(self.available_axes)
        
        # 线型映射
        style_map = {'solid': 0, 'dash': 1, 'dot': 2, 'dashdot': 3}
        self.style_combo.setCurrentIndex(style_map.get(self.curve_config.line_style, 0))
    
    def update_color_button(self):
        """更新颜色按钮"""
        self.color_btn.setStyleSheet(
            f"background-color: {self.curve_config.color.name()}; "
            f"border: 1px solid #888;"
        )
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.curve_config.color, self, "选择曲线颜色")
        if color.isValid():
            self.curve_config.color = color
            self.update_color_button()
            self.on_config_changed()
    
    def on_config_changed(self):
        """配置改变"""
        self.curve_config.enabled = self.enable_check.isChecked()
        self.curve_config.axis_id = self.axis_combo.currentText()
        self.curve_config.is_step = self.step_check.isChecked()
        
        # 线型
        style_map = {0: 'solid', 1: 'dash', 2: 'dot', 3: 'dashdot'}
        self.curve_config.line_style = style_map[self.style_combo.currentIndex()]
        
        self.configChanged.emit()
    
    def update_available_axes(self, axes: List[str]):
        """更新可用轴列表"""
        self.available_axes = axes
        current = self.axis_combo.currentText()
        
        self.axis_combo.clear()
        self.axis_combo.addItems(axes)
        
        if current in axes:
            self.axis_combo.setCurrentText(current)
        elif self.curve_config.axis_id in axes:
            self.axis_combo.setCurrentText(self.curve_config.axis_id)

