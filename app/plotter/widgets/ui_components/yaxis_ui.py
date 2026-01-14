#!/usr/bin/env python3

"""Y轴管理 UI 组件"""
from typing import Optional, Dict, Callable, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QPushButton, QGroupBox

from app.plotter.managers.axismanager import AxisManager

from .base import BaseUIComponents

if TYPE_CHECKING:
    from app.plotter.widgets.axisconfigpanel import AxisConfigPanel


class YAxisUIComponents(BaseUIComponents):
    """
    Y轴管理相关的 UI 组件容器
    
    管理多个 Y轴配置面板的布局和交互：
    - Y轴容器和布局
    - 添加轴按钮
    - 轴配置面板字典
    
    Attributes:
        container: Y轴容器 Widget
        layout: Y轴容器的布局
        groupbox: Y轴管理的分组框
        btn_add_axis: 添加轴的按钮
        dic_axis_panels: 轴名称到配置面板的映射
    """
    
    def __init__(self,
        parent: Optional[QWidget],
        manager_axis: AxisManager
    ):
        # 初始化父类
        super().__init__()
        # 初始值
        self.container: Optional[QWidget] = None
        self.layout: Optional[QVBoxLayout] = None
        self.groupbox: Optional[QGroupBox] = None
        self.btn_add_axis: Optional[QPushButton] = None
        self.dic_axis_panels: Dict[str, 'AxisConfigPanel'] = {}
        # 初始化
        self.manager_axis = manager_axis
        pass
    
    def create_widgets(self,
        parent: Optional[QWidget] = None,
        name_prefix: str = "yaxis",
        tr_func: Optional[Callable[[str, str], str]] = None,
        **kwargs) -> 'YAxisUIComponents':
        """
        创建Y轴管理UI组件
        
        Args:
            parent: 父widget
            name_prefix: 组件名称前缀
            tr_func: 翻译函数
            
        Returns:
            self，支持链式调用
        """
        tr = tr_func or (lambda text, ctx='': text)
        
        # 创建分组框
        self.groupbox = QGroupBox(tr("Y轴配置", 'f_config_yaxes'), parent)
        self.groupbox.setObjectName(f"{name_prefix}_groupbox")
        boxlayout_manager = QVBoxLayout()
        
        # 创建添加轴按钮
        self.btn_add_axis = QPushButton(tr("+ 添加右侧Y轴", 'f_add_yaxis'))
        self.btn_add_axis.setObjectName(f"{name_prefix}_btn_add")
        boxlayout_manager.addWidget(self.btn_add_axis)
        
        # 创建轴列表容器
        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.container.setLayout(self.layout)
        boxlayout_manager.addWidget(self.container)
        
        self.groupbox.setLayout(boxlayout_manager)
        return self
    
    def connect_signals(self, **callbacks) -> 'YAxisUIComponents':
        """
        连接信号到回调函数
        
        Args:
            **callbacks: 支持以下回调:
                - on_add_axis: 点击添加轴按钮时的回调
                
        Returns:
            self，支持链式调用
        """
        if on_add_axis := callbacks.get('on_add_axis'):
            if self.btn_add_axis:
                self.btn_add_axis.clicked.connect(on_add_axis)
        
        return self
    
    def get_main_widget(self) -> Optional[QWidget]:
        """获取主widget（分组框）"""
        return self.groupbox
    
    def add_axis_panel(self, 
        str_name_axis: str, 
        panel: 'AxisConfigPanel',
        bol_add_separator: bool = True
    ) -> bool:
        """
        添加轴配置面板
        
        Args:
            str_name_axis: 轴名称
            panel: 轴配置面板实例
            add_separator: 是否添加分隔线（主轴不需要）
            
        Returns:
            是否成功添加
        """
        if not self.layout:
            return False
        
        # 添加分隔线（非主轴）
        if bol_add_separator and self.manager_axis.is_axis_primary(str_name_axis):
            separator = self._create_separator()
            self.layout.addWidget(separator)
        
        # 添加面板
        self.layout.addWidget(panel)
        self.dic_axis_panels[str_name_axis] = panel
        return True
    
    def remove_axis_panel(self, str_name_axis: str) -> bool:
        """
        移除轴配置面板
        
        Args:
            str_name_axis: 轴名称
            
        Returns:
            是否成功移除
        """
        if str_name_axis not in self.dic_axis_panels:
            return False
        
        panel = self.dic_axis_panels[str_name_axis]
        
        if self.layout:
            # 查找并移除面板及其前置分隔线
            panel_index = self._find_widget_index(panel)
            if panel_index >= 0:
                # 移除面板
                self.layout.removeWidget(panel)
                panel.deleteLater()
                
                # 移除前置分隔线
                if panel_index > 0:
                    prev_widget = self.layout.itemAt(panel_index - 1).widget()
                    if isinstance(prev_widget, QFrame):
                        self.layout.removeWidget(prev_widget)
                        prev_widget.deleteLater()
        
        del self.dic_axis_panels[str_name_axis]
        return True
    
    def get_axis_panel(self, str_name_axis: str) -> Optional['AxisConfigPanel']:
        """获取指定轴的配置面板"""
        return self.dic_axis_panels.get(str_name_axis)
    
    def has_axis(self, str_name_axis: str) -> bool:
        """检查是否存在指定轴"""
        return str_name_axis in self.dic_axis_panels
    
    def get_axis_count(self) -> int:
        """获取轴的数量"""
        return len(self.dic_axis_panels)
    
    def clear_all_panels(self):
        """清空所有轴配置面板（保留主轴）"""
        axes_to_remove = [
            name for name in self.dic_axis_panels.keys() 
            if name != 'main'
        ]
        for name in axes_to_remove:
            self.remove_axis_panel(name)
    
    def _find_widget_index(self, widget: QWidget) -> int:
        """查找 widget 在布局中的索引"""
        if not self.layout:
            return -1
        for i in range(self.layout.count()):
            if self.layout.itemAt(i).widget() == widget:
                return i
        return -1
    
    @staticmethod
    def _create_separator() -> QFrame:
        """创建水平分隔线"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
