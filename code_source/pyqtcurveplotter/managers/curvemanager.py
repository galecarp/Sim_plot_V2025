#!/usr/bin/env python3

from typing import List, Dict, Set, Optional, Any, TYPE_CHECKING, override
from PyQt6.QtCore import QObject, pyqtSignal
from copy import deepcopy

from code_source.general_toolkits.fptoolkit import aggregate_info_iterable, aggregator_list

from code_source.pyqtcurveplotter.managers.abstractmanager import AbstractManager
from code_source.pyqtcurveplotter.graphconfigs.curveconfig import CurveConfig

if TYPE_CHECKING:
    # 只在类型检查时导入,运行时不导入
    from code_source.pyqtcurveplotter.managers.subplotmanager import SubplotManager

class CurveManager(AbstractManager):
    """
    曲线管理器, 每个子图都有独立的 CurveManager 实例。
    
    管理单个子图中的所有曲线，包括：
    - 曲线配置的增删改查
    - 正在显示的列名集合管理
    - 曲线与轴的关联关系管理
    
    每个子图都有独立的 CurveManager 实例。
    
    Attributes:
        dic_curveconfig: 曲线配置字典 {str_name_col_actual: CurveConfig}
        set_added_cols: 当前正在显示的列名集合
        
    Signals:
        sig_curve_added: 曲线添加信号 (str_name_col_actual)
        sig_curve_removed: 曲线删除信号 (str_name_col_actual)
        sig_curve_changed: 曲线配置变更信号 (str_name_col_actual)
        sig_curves_batch_added: 批量曲线添加信号
        sig_curves_batch_removed: 批量曲线删除信号
        sig_curves_batch_changed: 批量曲线变更信号
    """
    
    # 信号定义
    sig_curve_added = pyqtSignal(str)     # 曲线添加时发射，参数为列名
    sig_curve_removed = pyqtSignal(str)   # 曲线删除时发射，参数为列名
    sig_curve_changed = pyqtSignal(str)   # 曲线配置变更时发射，参数为列名
    sig_curves_batch_added = pyqtSignal(list)    # 批量曲线添加时发射，避免多次刷新
    sig_curves_batch_removed = pyqtSignal(list)  # 批量曲线删除时发射，避免多次刷新
    sig_curves_batch_changed = pyqtSignal(list)  # 批量曲线变更时发射，避免多次刷新

    def __init__(self,
        parent: SubplotManager,
        idx_subplot: int = 0,
        str_name_axis_main: str = 'main',
    ):
        """初始化曲线管理器"""
        super().__init__(parent)

        # 初始化属性
        self.dic_curveconfig: Dict[str, CurveConfig] = {}
        self.set_added_cols: Set[str] = set()

        # 初始化
        self.manager_subplot: SubplotManager = parent
        self.idx_subplot: int = idx_subplot
        self.str_name_axis_main = str_name_axis_main
        return
    
    @override
    def _init_signals(self):
        """初始化信号"""
        self.dic_signals = {
            "sig_curve_added": self.sig_curve_added,
            "sig_curve_removed": self.sig_curve_removed,
            "sig_curve_changed": self.sig_curve_changed,
            "sig_curves_batch_added": self.sig_curves_batch_added,
            "sig_curves_batch_removed": self.sig_curves_batch_removed,
            "sig_curves_batch_changed": self.sig_curves_batch_changed,
        }
        pass

    # ============================================================
    # 信号处理
    # ============================================================

    @override
    def _connect_signals(self):
        """连接到下游的信号"""
        pass

  
    # ============================================================
    # 原子操作管理器
    # ============================================================

    @override
    def _get_state_snapshot(self) -> Dict[str, Any]:
        """获取轴管理器的状态快照"""
        return {
            'dic_curveconfig': {k: deepcopy(v) for k, v in self.dic_curveconfig.items()},
            'set_added_cols': self.set_added_cols.copy(),
        }
    
    @override
    def _restore_state_snapshot(self, dic_snapshot: Dict[str, Any]):
        """恢复轴管理器的状态快照"""
        self.dic_curveconfig = dic_snapshot['dic_curveconfig']
        self.set_added_cols = dic_snapshot['set_added_cols']
        self._warning("State restored from snapshot")
        return


    # ============================================================
    # 列名转化的便捷函数
    # ============================================================

    def get_name_col_actual(self, str_name_col_display: str) -> Optional[str]:
        """
        根据显示列名获取实际列名
        """
        return self.manager_subplot.manager_columnmetadata.func_get_actual_name(
            str_name_col_display)
    
    def get_name_col_display(self, str_name_col_actual: str) -> Optional[str]:
        """
        根据实际列名获取显示列名
        """
        return self.manager_subplot.manager_columnmetadata.func_get_display_name(
            str_name_col_actual)

    def get_name_col_actual_batch(self,
        lst_name_col_display: List[str]
    ) -> List[str]:
        """
        根据显示列名列表获取实际列名列表
        """
        return [
            self.get_name_col_actual(name)
            for name in lst_name_col_display
            if name is not None
        ]
    
    def get_name_col_display_batch(self,
        lst_name_col_actual: List[str]
    ) -> List[str]:
        """
        根据实际列名列表获取显示列名列表
        """
        return [
            self.get_name_col_display(name)
            for name in lst_name_col_actual
            if name is not None
        ]
    
    # ============================================================
    # 曲线操作
    # ============================================================

    def _add_curve_by_config(self,
        curveconfig: CurveConfig,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        添加曲线配置到字典中，更新集合并发射信号
        
        使用已有的 CurveConfig 对象。如果曲线已存在则返回 False。
        
        Args:
            curveconfig: 曲线配置对象
            bol_emit_signal: 是否发射信号，批量操作时可设为 False
        """
        str_name_col_actual = curveconfig.str_name_curve
        
        # 检查曲线是否已存在
        if str_name_col_actual in self.dic_curveconfig:
            self._warning(f"警告: 曲线 '{str_name_col_actual}' 已存在，无法添加")
            return False
        
        # 添加/替换配置
        self._add_curveconfig(curveconfig)
        
        # 添加曲线配置到集合
        self.set_added_cols.add(str_name_col_actual)
        
        # 发射信号
        if bol_emit_signal:
            self.sig_curve_added.emit(str_name_col_actual)
        return True

    def _add_curve_by_col(self,
        str_name_col_actual : str = None,
        str_name_col_display: str = None,
        str_name_axis: str = None,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        根据列名添加曲线配置
        
        如果曲线已存在则返回 False; 否则创建新配置并添加。
        """
        if str_name_col_actual is None:
            str_name_col_actual = self.get_name_col_actual(
                str_name_col_display)
        if str_name_col_actual in self.dic_curveconfig:
            # 曲线已存在
            return False
        
        # 创建新曲线配置
        curveconfig = self._create_curveconfig(
            str_name_col_actual=str_name_col_actual,
            str_name_axis=str_name_axis
        )
        # 调用 _add_curve_by_config 添加配置
        return self._add_curve_by_config(curveconfig, bol_emit_signal=bol_emit_signal)

    def _remove_curve(self,
        str_name_col_actual: str,
        bol_remove_config: bool = False,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        删除曲线
        
        Args:
            str_name_col_actual: 实际列名
            bol_remove_config: 是否同时删除配置
            bol_emit_signal: 是否发射信号，批量操作时可设为 False
        """
        # 检查曲线是否存在
        if str_name_col_actual not in self.set_added_cols:
            self._warning(f"警告: 曲线 '{str_name_col_actual}' 不存在")
            return False
        # 从在线集合中移除
        if str_name_col_actual in self.set_added_cols:
            self.set_added_cols.discard(str_name_col_actual)
        # 删除曲线配置
        if bol_remove_config:
            self._remove_curveconfig(str_name_col_actual)
        # 发射信号
        if bol_emit_signal:
            self.sig_curve_removed.emit(str_name_col_actual)
        return True
    
    def _move_curve_to_axis(self,
        str_name_col_actual: str,
        str_name_axis_new: str,
        str_name_col_display: str = None,
        bol_emit_signal: bool = True,
    ) -> bool:
        """
        将某个轴上的某曲线重新分配到另一个轴, 可以更改并未选中的列
        
        当删除Y轴时, 需要将该轴上的曲线移动到其他轴上
        
        Args:
            str_name_col_actual: 实际列名
            str_name_axis_new: 新Y轴名称
            str_name_col_display: 显示列名（可选）
            bol_emit_signal: 是否发射信号，批量操作时可设为 False 避免信号拥堵
        """
        # 获取真实列名
        if str_name_col_actual is None:
            str_name_col_actual = self.get_name_col_actual(str_name_col_display)
        # 检查曲线是否存在
        if str_name_col_actual not in self.dic_curveconfig:
            self._warning(f"警告: 曲线配置 '{str_name_col_actual}' 不存在，无法移动")
            return False
        # 获取曲线配置
        curveconfig = self.dic_curveconfig[str_name_col_actual]
        # 更新轴名称
        curveconfig.str_name_axis = str_name_axis_new
        # 发射信号
        if bol_emit_signal:
            self.sig_curve_changed.emit(curveconfig.str_name_curve)
        return True

    # 批量曲线操作
    def _move_all_curves_to_axis(self,
        str_name_axis_old: str,
        str_name_axis_new: str,
    ) -> bool:
        """
        将某个轴上的所有曲线重新分配到另一个轴, 可以更改并未选中的列
        
        当删除Y轴时, 需要将该轴上的曲线移动到其他轴上。
        批量操作优化：完成所有移动后只发射一次批量变更信号，避免多次刷新图形。
        
        Args:
            str_name_axis_old: 原Y轴名称
            str_name_axis_new: 新Y轴名称
        """
        # 批量移动
        bol_has_changes = False
        lst_name_col_moved = []
        for curveconfig in self.dic_curveconfig.values():
            if curveconfig.str_name_axis == str_name_axis_old:
                if self._move_curve_to_axis(
                    str_name_col_actual=curveconfig.str_name_curve,
                    str_name_axis_new=str_name_axis_new,
                    bol_emit_signal=False  # 批量操作时禁用单次信号
                ):
                    bol_has_changes = True
                    lst_name_col_moved.append(curveconfig.str_name_curve)
        
        # 只发射一次批量变更信号
        if bol_has_changes:
            self.sig_curves_batch_changed.emit(lst_name_col_moved)
        
        return True

    def _add_curves_by_col_batch(self,
        lst_name_col: List[str],
        bol_is_display_name: bool = False
    ) -> bool:
        """
        批量添加曲线
        
        批量操作优化：完成所有添加后只发射一次批量添加信号，避免多次刷新图形。
        """
        # 获取实际列名列表
        if bol_is_display_name:
            lst_name_col_actual = self.get_name_col_actual_batch(lst_name_col)
        else:
            lst_name_col_actual = lst_name_col
        # 创建曲线
        lst_name_col_added = []
        bol_has_changes = False
        for str_name_col_actual in lst_name_col_actual:
            if self._add_curve_by_col(str_name_col_actual, bol_emit_signal=False):
                bol_has_changes = True
                lst_name_col_added.append(str_name_col_actual)
        
        # 只发射一次批量添加信号
        if bol_has_changes:
            self.sig_curves_batch_added.emit(lst_name_col_added)
        
        return bol_has_changes

    def _remove_curves_batch(self,
        lst_name_col: List[str],
        bol_is_display_name: bool = False,
        bol_remove_config: bool = False
    ) -> bool:
        """
        批量删除曲线
        
        批量操作优化：完成所有删除后只发射一次批量删除信号，避免多次刷新图形。
        """
        # 获取实际列名列表
        if bol_is_display_name:
            lst_name_col_actual = self.get_name_col_actual_batch(lst_name_col)
        else:
            lst_name_col_actual = lst_name_col
        # 删除曲线
        lst_name_col_removed = []
        bol_has_changes = False
        for str_name_col in lst_name_col_actual:
            if self._remove_curve(str_name_col, bol_remove_config=bol_remove_config, bol_emit_signal=False):
                bol_has_changes = True
                lst_name_col_removed.append(str_name_col)
        
        # 只发射一次批量删除信号
        if bol_has_changes:
            self.sig_curves_batch_removed.emit(lst_name_col_removed)
        return bol_has_changes

    def remove_all_curves(self) -> bool:
        """
        清除所有曲线, 但不删除曲线配置
        """
        lst_name_col = list(self.dic_curveconfig.keys())
        bol_has_changes = self._remove_curves_batch(
            lst_name_col,
            bol_remove_config=False)
        return bol_has_changes
    
    # ============================================================
    # curveconfig 操作
    # ============================================================

    def _create_curveconfig(self,
        str_name_col_actual : str,
        str_name_axis: str = None,
        **kwargs
    ) -> CurveConfig:
        """
        初始化曲线配置对象（不添加到字典中）
        """
        if not str_name_axis:
            # 默认主轴
            str_name_axis = self.manager_subplot.str_name_axis_main
        # 创建曲线配置对象
        curveconfig = CurveConfig(
            str_name_curve=str_name_col_actual,
            str_name_axis=str_name_axis,
            **kwargs
        )
        return curveconfig

    def _add_curveconfig(self,
        curveconfig: CurveConfig
    ) -> bool:
        """
        添加曲线配置对象到字典中
        
        如果曲线已存在则返回 False。
        """
        str_name_col_actual = curveconfig.str_name_curve
        if str_name_col_actual in self.dic_curveconfig:
            self._warning(f"警告: 曲线 '{str_name_col_actual}' 已存在，无法添加")
            return False
        self.dic_curveconfig[str_name_col_actual] = curveconfig
        return True

    def _remove_curveconfig(self,
        str_name_col_actual: str,
        str_name_col_display: str = None
    ) -> bool:
        """
        从字典中删除曲线配置对象
        """
        if str_name_col_actual is None:
            str_name_col_actual = self.get_name_col_actual(str_name_col_display)     
        if str_name_col_actual not in self.dic_curveconfig:
            self._warning(f"警告: 曲线配置 '{str_name_col_actual}' 不存在，无法删除")
            return False
        del self.dic_curveconfig[str_name_col_actual]
        return True
    
    def _update_curveconfig(self,
        str_name_col_actual: str,
        curveconfig: CurveConfig
    ) -> bool:
        """
        更新曲线配置
        
        Args:
            str_name_col_actual: 列名（实际列名）
            curveconfig: 新的曲线配置对象
        """
        if str_name_col_actual not in self.dic_curveconfig:
            self._warning(f"警告: 曲线 '{str_name_col_actual}' 不存在，无法更新")
            return False
        # 更新配置
        self.dic_curveconfig[str_name_col_actual] = curveconfig
        # 发射信号
        self.sig_curve_changed.emit(str_name_col_actual)
        return True

    # ============================================================
    # 信息获取
    # ============================================================

    ## curveconfig getter
    def get_curveconfig(self, str_name_col_actual: str) -> Optional[CurveConfig]:
        """
        获取指定曲线的配置
        
        Args:
            str_name_col_actual: 列名（实际列名）
            
        Returns:
            CurveConfig 对象，如果不存在则返回 None
        """
        return self.dic_curveconfig.get(str_name_col_actual)
    
    def get_lst_curveconfig_all_initialized(self) -> List[CurveConfig]:
        """
        获取所有已经存在配置的曲线配置列表
        
        Returns:
            曲线配置列表
        """
        return list(self.dic_curveconfig.values())

    def get_lst_curveconfig_all_added(self) -> List[CurveConfig]:
        """
        获取所有正在显示的曲线配置列表
        
        Returns:
            曲线配置列表
        """
        return [
            self.dic_curveconfig[name]
            for name in self.set_added_cols
        ]

    ## 列名getter
    def get_lst_name_col_all_added(self) -> List[str]:
        """
        获取所有曲线的真实列名列表
        
        Returns:
            列名列表
        """
        return list(self.set_added_cols)
    
    def get_lst_name_col_all_initialized(self) -> List[str]:
        """
        获取所有已经初始化的曲线真实列名列表
        
        Returns:
            列名列表
        """
        return list(self.dic_curveconfig.keys())
    
    def get_dic_curveconfig_all_added(self) -> Dict[str, CurveConfig]:
        """
        获取所有曲线配置的字典
        
        Returns:
            曲线配置字典的引用（注意：返回的是引用，不是副本）
        """
        return self.dic_curveconfig
    
    def get_lst_name_col_by_axis(self, str_name_axis: str) -> List[str]:
        """
        获取指定Y轴上的所有初始化的曲线名字
        """
        return [
            curveconfig.str_name_curve
            for curveconfig in self.dic_curveconfig.values()
            if curveconfig.str_name_axis == str_name_axis
        ]

    ## 状态查询
    def is_curve_initialized(self, str_name_col_actual: str) -> bool:
        """
        检查指定曲线是否存在dic_curveconfig中
        """
        return str_name_col_actual in self.dic_curveconfig
    
    def is_curve_added(self, str_name_col_actual: str) -> bool:
        """
        检查指定曲线是否在当前显示集合中
        """
        return str_name_col_actual in self.set_added_cols

    def count_curve_initialized(self) -> int:
        """
        获取已经初始化的曲线总数
        """
        return len(self.dic_curveconfig)
    
    def count_curve_added(self) -> int:
        """
        获取当前加入显示的曲线总数
        """
        return len(self.set_added_cols)

    # curve getter
    def get_visible_curves(self) -> List[CurveConfig]:
        """
        获取所有可见的曲线
        
        Returns:
            可见曲线配置列表（bol_show=True）
        """
        return [
            config for config in self.dic_curveconfig.values()
            if config.bol_show
        ]
    
    def get_hidden_curves(self) -> List[CurveConfig]:
        """
        获取所有隐藏的曲线
        
        Returns:
            隐藏曲线配置列表（bol_show=False）
        """
        return [
            config for config in self.dic_curveconfig.values()
            if not config.bol_show
        ]

    # ============================================================
    # 公共API方法
    # ============================================================
    
    def add_curve(self,
        str_name_col: str,
        bol_is_display_name: bool = False,
        str_name_axis: str = None
    ) -> bool:
        """
        公共API: 添加单个曲线
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_is_display_name: 是否为显示列名
            str_name_axis: 指定Y轴名称，默认为主轴
            
        Returns:
            是否成功添加
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self._add_curve_by_col(
            str_name_col_actual=str_name_col_actual,
            str_name_axis=str_name_axis,
            bol_emit_signal=True
        )
    
    def add_curves(self,
        lst_name_col: List[str],
        bol_is_display_name: bool = False
    ) -> bool:
        """
        公共API: 批量添加曲线
        
        Args:
            lst_name_col: 列名列表
            bol_is_display_name: 是否为显示列名
            
        Returns:
            是否有曲线被成功添加
        """
        return self._add_curves_by_col_batch(
            lst_name_col=lst_name_col,
            bol_is_display_name=bol_is_display_name
        )
    
    def remove_curve(self,
        str_name_col: str,
        bol_is_display_name: bool = False,
        bol_remove_config: bool = False
    ) -> bool:
        """
        公共API: 删除单个曲线
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_is_display_name: 是否为显示列名
            bol_remove_config: 是否同时删除配置
            
        Returns:
            是否成功删除
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self._remove_curve(
            str_name_col_actual=str_name_col_actual,
            bol_remove_config=bol_remove_config,
            bol_emit_signal=True
        )
    
    def remove_curves(self,
        lst_name_col: List[str],
        bol_is_display_name: bool = False,
        bol_remove_config: bool = False
    ) -> bool:
        """
        公共API: 批量删除曲线
        
        Args:
            lst_name_col: 列名列表
            bol_is_display_name: 是否为显示列名
            bol_remove_config: 是否同时删除配置
            
        Returns:
            是否有曲线被成功删除
        """
        return self._remove_curves_batch(
            lst_name_col=lst_name_col,
            bol_is_display_name=bol_is_display_name,
            bol_remove_config=bol_remove_config
        )
    
    def clear_all_curves(self) -> bool:
        """
        公共API: 清除所有曲线（保留配置）
        
        Returns:
            是否成功清除
        """
        return self.remove_all_curves()
    
    def move_curve_to_axis(self,
        str_name_col: str,
        str_name_axis_new: str,
        bol_is_display_name: bool = False
    ) -> bool:
        """
        公共API: 将曲线移动到指定Y轴
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            str_name_axis_new: 新Y轴名称
            bol_is_display_name: 是否为显示列名
            
        Returns:
            是否成功移动
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self._move_curve_to_axis(
            str_name_col_actual=str_name_col_actual,
            str_name_axis_new=str_name_axis_new,
            bol_emit_signal=True
        )
    
    def get_curve_config(self, str_name_col: str, bol_is_display_name: bool = False) -> Optional[CurveConfig]:
        """
        公共API: 获取曲线配置
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_is_display_name: 是否为显示列名
            
        Returns:
            曲线配置对象，不存在则返回None
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self.get_curveconfig(str_name_col_actual)
    
    def get_all_added_curves(self) -> List[str]:
        """
        公共API: 获取所有正在显示的曲线列名
        
        Returns:
            曲线列名列表（实际列名）
        """
        return self.get_lst_name_col_all_added()
    
    def get_all_initialized_curves(self) -> List[str]:
        """
        公共API: 获取所有已初始化的曲线列名
        
        Returns:
            曲线列名列表（实际列名）
        """
        return self.get_lst_name_col_all_initialized()
    
    def get_curves_by_axis(self, str_name_axis: str) -> List[str]:
        """
        公共API: 获取指定Y轴上的所有曲线
        
        Args:
            str_name_axis: Y轴名称
            
        Returns:
            曲线列名列表（实际列名）
        """
        return self.get_lst_name_col_by_axis(str_name_axis)
    
    def is_curve_exists(self, str_name_col: str, bol_is_display_name: bool = False) -> bool:
        """
        公共API: 检查曲线是否已初始化
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_is_display_name: 是否为显示列名
            
        Returns:
            是否存在
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self.is_curve_initialized(str_name_col_actual)
    
    def is_curve_showing(self, str_name_col: str, bol_is_display_name: bool = False) -> bool:
        """
        公共API: 检查曲线是否正在显示
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_is_display_name: 是否为显示列名
            
        Returns:
            是否正在显示
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        return self.is_curve_added(str_name_col_actual)
    
    def get_curve_count(self) -> tuple[int, int]:
        """
        公共API: 获取曲线统计信息
        
        Returns:
            (已初始化曲线数, 正在显示曲线数)
        """
        return (self.count_curve_initialized(), self.count_curve_added())
    
    def set_curve_visibility(self,
        str_name_col: str,
        bol_visible: bool,
        bol_is_display_name: bool = False
    ) -> bool:
        """
        公共API: 设置曲线可见性
        
        Args:
            str_name_col: 列名（可以是实际列名或显示列名）
            bol_visible: 是否可见
            bol_is_display_name: 是否为显示列名
            
        Returns:
            是否成功设置
        """
        if bol_is_display_name:
            str_name_col_actual = self.get_name_col_actual(str_name_col)
        else:
            str_name_col_actual = str_name_col
        
        curveconfig = self.get_curveconfig(str_name_col_actual)
        if curveconfig is None:
            return False
        
        curveconfig.bol_show = bol_visible
        self.sig_curve_changed.emit(str_name_col_actual)
        return True
    
    def get_visible_curve_list(self) -> List[str]:
        """
        公共API: 获取所有可见曲线的列名
        
        Returns:
            可见曲线列名列表（实际列名）
        """
        return [
            config.str_name_curve
            for config in self.get_visible_curves()
        ]
    
    def get_hidden_curve_list(self) -> List[str]:
        """
        公共API: 获取所有隐藏曲线的列名
        
        Returns:
            隐藏曲线列名列表（实际列名）
        """
        return [
            config.str_name_curve
            for config in self.get_hidden_curves()
        ]
    