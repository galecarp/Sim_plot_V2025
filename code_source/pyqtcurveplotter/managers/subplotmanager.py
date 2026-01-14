#!/usr/bin/env python3

from typing import List, Dict, Optional, Union, Any, Callable, Iterable, TYPE_CHECKING, override
from functools import partial, reduce
from operator import add
from PyQt6.QtCore import QObject, pyqtSignal

from code_source.general_toolkits.fptoolkit import aggregate_info_iterable, aggregator_list

from code_source.pyqtcurveplotter.managers.curvemanager import CurveManager
from code_source.pyqtcurveplotter.managers.axismanager import AxisManager
from code_source.pyqtcurveplotter.managers.abstractmanager import AbstractManager

if TYPE_CHECKING:
    # 只在类型检查时导入,运行时不导入
    from code_source.pyqtcurveplotter.managers.columnmetadatamanager import ColumnMetadataManager


class SubplotManager(AbstractManager):
    """
    子图管理器
    
    管理多个子图，每个子图包含独立的曲线管理器和轴管理器。
    提供对所有子图的统一管理接口。
    
    Architecture:
        SubplotManager
          ├── Subplot[0]
          │     ├── CurveManager (管理该子图的曲线)
          │     └── AxisManager (管理该子图的Y轴)
          ├── Subplot[1]
          │     ├── CurveManager
          │     └── AxisManager
          └── ...
    
    Attributes:
        n_subplot: 子图总数
        str_name_axis_main: 主Y轴的名称（所有子图共享）
        dic_curvemanager: 曲线管理器字典 {idx_subplot: CurveManager}
        dic_axismanager: 轴管理器字典 {idx_subplot: AxisManager}
        str_name_axis_main: 主Y轴的名称（所有子图共享）
        
    Signals:
        sig_subplot_config_changed: 子图配置变更信号 (idx_subplot)
    """
    
    # 信号定义
    sig_subplot_config_changed = pyqtSignal(int)  # 子图配置变更，参数为子图索引
    
    def __init__(self, 
        n_subplot: int = 3, 
        manager_columnmetadata: Optional["ColumnMetadataManager"] = None
    ):
        """
        初始化子图管理器
        
        Args:
            n_subplot: 子图数量
            str_name_axis_main: 主Y轴的名称，默认为 'main'
        """
        super().__init__()
        # 初始化属性
        self.dic_curvemanager: Dict[int, CurveManager] = {}
        self.dic_axismanager: Dict[int, AxisManager] = {}

        # 初始化属性
        self.n_subplot = n_subplot
        self.manager_columnmetadata = manager_columnmetadata

        # 初始化信号连接
        
        # 初始化子图管理器
        self._init_subplot_managers()
        self._connect_signals()
        pass
    
    def _init_subplot_managers(self):
        """初始化所有子图的管理器"""
        for idx_subplot in range(self.n_subplot):
            # 1.创建子图的曲线管理器
            self.dic_curvemanager[idx_subplot] = CurveManager(
                parent=self,
                idx_subplot=idx_subplot,
                str_name_axis_main=self.str_name_axis_main
            )
            
            # 2.创建子图的轴管理器
            self.dic_axismanager[idx_subplot] = AxisManager(
                parent=self,
                idx_subplot=idx_subplot,
                str_name_axis_main=self.str_name_axis_main
            )
        return
    
    @override
    def _init_signals(self):
        """初始化信号"""
        self.dic_signals = {
            "sig_subplot_config_changed": self.sig_subplot_config_changed,
        }
        pass

    # 信号处理
    @override
    def _connect_signals(self):
        """
        连接到下游的信号
        """
        # 定义槽函数模板
        def slot_template(signal_arg, idx_subplot):
            self.sig_subplot_config_changed.emit(idx_subplot)
        # 1.连接 columnmetadata manager 的信号
        slot = partial(slot_template, idx_subplot=-1)
        self.manager_columnmetadata._connect_signals_to_slot(
            slot=slot
        )
        
        for idx_subplot in range(self.n_subplot):
            # 使用 partial 填入具体的 idx_subplot 值
            slot = partial(slot_template, idx_subplot=idx_subplot)
            # 2.curve manager
            curve_manager = self.dic_curvemanager[idx_subplot]
            curve_manager._connect_signals_to_slot(
                slot=slot
            )
            # 3.axis manager
            axis_manager = self.dic_axismanager[idx_subplot]
            axis_manager._connect_signals_to_slot(
                slot=slot
            )
        return
    
    # 列名便捷转换
    def get_name_col_actual(self,
        str_name_col_display: str
    ) -> str:
        """
        将显示列名转换为实际列名
        """
        if not self.manager_columnmetadata:
            self._error("ColumnMetadataManager 未设置，无法转换列名")
        return self.manager_columnmetadata.func_get_actual_name(
            str_name_col_display)
    
    def get_name_col_display(self,
        str_name_col_actual: str
    ) -> str:
        """
        将显示列名转换为实际列名
        """
        if not self.manager_columnmetadata:
            self._error("ColumnMetadataManager 未设置，无法转换列名")
        return self.manager_columnmetadata.func_get_display_name(
            str_name_col_actual)

    # Subplot的操作
    def clear_subplot(self, idx_subplot: int) -> bool:
        """
        清空指定子图的所有内容, 但不删除曲线配置
        
        TODO:清除该子图的所有曲线和次轴，保留主轴
        
        Args:
            idx_subplot: 子图索引
        """
        if not self.is_valid_subplot_index(idx_subplot):
            self._warning(f"警告: 子图索引 {idx_subplot} 无效")
            return False
        bol_success = True
        # 清空曲线管理器
        curve_manager = self.get_curve_manager(idx_subplot)
        if curve_manager:
            bol_success &= curve_manager.remove_all_curves()
        
        # 清空轴管理器
        axis_manager = self.get_axis_manager(idx_subplot)
        if axis_manager:
            bol_success &= axis_manager.clear_secondary_axes()
        return bol_success
    
    def clear_all_subplots(self):
        """
        清空所有子图的内容
        """
        return aggregate_info_iterable(
            iter_tgt=range(self.n_subplot),
            extractors=self.clear_subplot,
            aggregator=all
        )

    # subplot的信息查询
    def has_curve_in_any_subplot(self, str_name_col_actual: str) -> bool:
        """
        检查某列是否在任意子图中显示
        """
        def extractor(mgr: CurveManager) -> bool:
            return mgr.is_curve_added(str_name_col_actual) 
        return aggregate_info_iterable(
            iter_tgt=self.dic_curvemanager.values(),
            extractors=extractor,
            aggregator=any
        )
    
    def get_idx_subplot_added_curve(self, str_name_col_actual: str) -> List[int]:
        """
        获取包含指定曲线的所有子图索引
        """
        def extractor(mgr: CurveManager) -> int:
            return mgr.idx_subplot
        def filter_pre(mgr: CurveManager) -> bool:
            return mgr.is_curve_added(str_name_col_actual)
        return aggregate_info_iterable(
            iter_tgt=self.dic_curvemanager.values(),
            extractors=extractor,
            filter_pre=filter_pre,
            aggregator=aggregator_list
        )
    
    # 统计信息
    def count_sum_subplots(self,
        dic_manager : Dict[int, AbstractManager],
        str_method : str
    ) -> int:
        """
        计算所有子图的某个统计值之和
        """
        def extractor(mgr: CurveManager) -> bool:
            return getattr(mgr, str_method)()
        return aggregate_info_iterable(
            iter_tgt=dic_manager.values(),
            extractors=extractor,
            aggregator=sum
        )

    def count_curve_initialized(self) -> int:
        """
        获取所有子图被初始化的曲线数量
        """
        return self.count_sum_subplots(
            self.dic_curvemanager,
            "count_curve_initialized")

    def count_curve_added(self) -> int:
        """
        获取所有子图被添加的曲线数量
        """
        return self.count_sum_subplots(
            self.dic_curvemanager,
            "count_curve_added")
    
    def count_yaxis_all_subplots(self) -> int:
        """
        获取所有子图的Y轴总数, 包含左轴和右轴
        """
        return self.count_sum_subplots(
            self.dic_axismanager,
            "count_yaxis")

    def count_subplot(self) -> int:
        """
        获取子图总数
        """
        return self.n_subplot

    def is_valid_subplot_index(self, idx_subplot: int) -> bool:
        """
        检查子图索引是否有效
        """
        return 0 <= idx_subplot < self.n_subplot
    
    # Getters for manager
    def get_curve_manager(self, idx_subplot: int) -> Optional[CurveManager]:
        """
        获取指定子图的曲线管理器
        """
        return self.dic_curvemanager[idx_subplot]
    
    def get_axis_manager(self, idx_subplot: int) -> Optional[AxisManager]:
        """
        获取指定子图的轴管理器
        
        Args:
            idx_subplot: 子图索引
            
        Returns:
            AxisManager 对象，如果索引无效则返回 None
        """
        return self.dic_axismanager[idx_subplot]
