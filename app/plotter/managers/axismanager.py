#!/usr/bin/env python3

from __future__ import annotations
from typing import List, Dict, Set, Any, Optional, TYPE_CHECKING, override
from PySide6.QtCore import QObject, Signal
from copy import deepcopy

if TYPE_CHECKING:
    # 只在类型检查时导入,运行时不导入
    from app.plotter.managers.subplotmanager import SubplotManager

from app.plotter.graphconfigs.axisconfig import AxisConfig
from app.plotter.managers.abstractmanager import AbstractManager

from code_source.general_toolkits.fptoolkit import aggregate_info_iterable, aggregator_list


class AxisManager(AbstractManager):
    """
    Y轴管理器, 每个子图都有独立的 AxisManager 实例。
    
    管理单个子图中的所有Y轴，包括：
    - Y轴配置的增删改查
    - 主轴（左侧默认轴）的管理
    - 次轴（右侧额外轴）的管理
    
    每个子图都有独立的 AxisManager 实例。
    
    Attributes:
        dic_axisconfig: Y轴配置字典 {str_name_axis: AxisConfig}
        set_axis_added: 当前已添加的轴名称集合
        str_name_axis_main: 主Y轴的名称（通常为 'main'）
        
    Signals:
        sig_axis_added: 轴添加信号 (str_name_axis)
        sig_axis_removed: 轴删除信号 (str_name_axis)
        sig_axis_changed: 轴配置变更信号 (str_name_axis)
        sig_axes_batch_added: 批量轴添加信号
        sig_axes_batch_removed: 批量轴删除信号
        sig_axes_batch_changed: 批量轴变更信号
    """
    
    # 信号定义
    sig_axis_added = Signal(str)     # 轴添加时发射，参数为轴名称
    sig_axis_removed = Signal(str)   # 轴删除时发射，参数为轴名称
    sig_axis_changed = Signal(str)   # 轴配置变更时发射，参数为轴名称
    sig_axes_batch_added = Signal(list)    # 批量轴添加时发射，避免多次刷新
    sig_axes_batch_removed = Signal(list)  # 批量轴删除时发射，避免多次刷新
    sig_axes_batch_changed = Signal(list)  # 批量轴变更时发射，避免多次刷新
    
    def __init__(self,
        parent: SubplotManager,
        idx_subplot: int = 0,
        str_name_axis_main: str = 'main',
    ):
        """初始化Y轴管理器"""
        super().__init__(parent)

        # 初始化属性
        self.dic_axisconfig: Dict[str, AxisConfig] = {}
        self.set_axis_added: Set[str] = set()

        # 初始化
        self.manager_subplot: SubplotManager = parent
        self.idx_subplot: int = idx_subplot
        self.str_name_axis_main = str_name_axis_main
        
        # 初始化轴存储
        self._init_axis()
        return
    
    def _init_axis(self):
        """初始化子图的轴存储"""
        # 创建主轴
        axisconfig_main = AxisConfig(
            str_name_axis=self.str_name_axis_main,
            bol_is_prim_axis=True
        )
        # 初始化y轴配置字典
        self.dic_axisconfig: Dict[str, AxisConfig] = {
            # 加入主y轴(左)
            self.str_name_axis_main: axisconfig_main
        }
        # 标记主轴已添加
        self.set_axis_added.add(self.str_name_axis_main)
        return

    @override
    def _init_signals(self):
        """初始化信号"""
        self.dic_signals = {
            "sig_axis_added": self.sig_axis_added,
            "sig_axis_removed": self.sig_axis_removed,
            "sig_axis_changed": self.sig_axis_changed,
            "sig_axes_batch_added": self.sig_axes_batch_added,
            "sig_axes_batch_removed": self.sig_axes_batch_removed,
            "sig_axes_batch_changed": self.sig_axes_batch_changed,
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
            'dic_axisconfig': {k: deepcopy(v) for k, v in self.dic_axisconfig.items()},
            'set_axis_added': self.set_axis_added.copy(),
            'str_name_axis_main': self.str_name_axis_main,
        }
    
    @override
    def _restore_state_snapshot(self, dic_snapshot: Dict[str, Any]):
        """恢复轴管理器的状态快照"""
        self.dic_axisconfig = dic_snapshot['dic_axisconfig']
        self.set_axis_added = dic_snapshot['set_axis_added']
        self.str_name_axis_main = dic_snapshot['str_name_axis_main']
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
    # 轴操作
    # ============================================================

    def _add_axis_by_config(self,
        axisconfig: AxisConfig,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        添加轴配置到字典中，更新集合并发射信号
        
        使用已有的 AxisConfig 对象。如果轴已存在则返回 False。
        
        Args:
            axisconfig: Y轴配置对象
            bol_emit_signal: 是否发射信号，批量操作时可设为 False
        """
        # 获取轴名称
        str_name_axis = axisconfig.str_name_axis

        # 检查主轴
        if self.is_axis_primary(str_name_axis):
            self._warning(f"警告: 主轴名称必须为 '{self.str_name_axis_main}'，无法添加")
            return False
        
        # 检查轴名称是否已存在
        if self.is_axis_initialized(str_name_axis):
            self._info(f"轴 '{str_name_axis}' 已存在，覆盖原有配置")
            self._update_axisconfig(axisconfig)
        else:
            self._add_axisconfig(axisconfig)
        
        # 添加轴配置到集合
        self._add_axis_to_set(str_name_axis)
        
        # 发射信号
        if bol_emit_signal:
            self.sig_axis_added.emit(str_name_axis)
        return True

    def _add_axis_by_name(self,
        str_name_axis: str,
        bol_is_prim_axis: bool = False,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        根据轴名添加轴配置
        """
        # 创建新轴配置
        axisconfig = self._create_axisconfig(
            str_name_axis=str_name_axis,
            bol_is_prim_axis=bol_is_prim_axis
        )
        # 调用 _add_axis_by_config 添加配置
        return self._add_axis_by_config(
            axisconfig,
            bol_emit_signal=bol_emit_signal)

    def _remove_axis(self,
        str_name_axis: str,
        bol_remove_config: bool = False,
        bol_emit_signal: bool = True
    ) -> bool:
        """
        删除Y轴
        
        注意：主轴不允许删除
        
        Args:
            str_name_axis: 要删除的轴名称
            bol_remove_config: 是否同时删除配置
            bol_emit_signal: 是否发射信号，批量操作时可设为 False
        """
        # 检查主轴, 不允许删除
        if self.is_axis_primary(str_name_axis):
            self._warning(f"警告: 主轴 '{str_name_axis}' 不允许删除")
            return False
        
        # 检查轴是否存在
        if not self.is_axis_initialized(str_name_axis):
            self._warning(f"警告: 轴配置 '{str_name_axis}' 不存在")
            return False
        
        # 检查是否去除添加的轴但保留配置, 此时轴却没有在已添加集合中
        if not bol_remove_config and not self.is_axis_added(str_name_axis):
            self._warning(f"警告: 轴'{str_name_axis}'没有被添加, 无法删除")
            return False
        
        # 从在线集合中移除
        if self.is_axis_added(str_name_axis):
            self._remove_axis_from_set(str_name_axis)
        
        # 删除轴配置
        if bol_remove_config:
            self._remove_axisconfig(str_name_axis)
        
        # 发射信号
        if bol_emit_signal:
            self.sig_axis_removed.emit(str_name_axis)
        return True

    def _switch_axis_main_atomic(self,
        axisconfig_main_old: AxisConfig,
        axisconfig_main_new: AxisConfig,
    ) -> bool:
        """ 原子化切换主轴操作, 包含快照和异常处理
        """
        try:
            with self._atomic_operation():
                # 更新axisconfig主轴标识
                axisconfig_main_old.bol_is_prim_axis = False
                axisconfig_main_new.bol_is_prim_axis = True

                # 从added中去除旧主轴，添加新主轴
                self.set_axis_added.discard(axisconfig_main_old.str_name_axis)
                self.set_axis_added.add(axisconfig_main_new.str_name_axis)               
                # 更新主轴名称
                self.str_name_axis_main = axisconfig_main_new.str_name_axis
        except Exception as e:
            self._error(f"错误: 切换主轴失败: {e}")
            return False
        return True

    def _switch_axis_main(self,
        str_name_axis_main: str
    ) -> bool:
        """
        切换主轴
        
        Args:
            str_name_axis_main: 新主轴名称
            
        Returns:
            成功返回 True, 如果新主轴不存在则返回 False
        """
        # 检查新主轴是否存在
        if not self.is_axis_initialized(str_name_axis_main):
            self._warning(f"警告: 轴 '{str_name_axis_main}' 不存在，无法切换为主轴")
            return False
        
        # 获取当前主轴配置
        axisconfig_main_old = self.get_axisconfig(self.str_name_axis_main)
        if axisconfig_main_old is None:
            self._error(f"错误: 当前主轴 '{self.str_name_axis_main}' 配置不存在")
            return False
        # 获取新主轴配置
        axisconfig_main_new = self.get_axisconfig(str_name_axis_main)
        if axisconfig_main_new is None:
            self._error(f"错误: 新主轴 '{str_name_axis_main}' 配置不存在")
            return False
        
        # 带有原子操作的切换主轴
        bol_success = self._switch_axis_main_atomic(
            axisconfig_main_old,
            axisconfig_main_new
        )
        if not bol_success:
            return False
        # 发射信号
        self.sig_axes_batch_changed.emit([
            axisconfig_main_old.str_name_axis,
            axisconfig_main_new.str_name_axis])
        return True

    # 批量轴操作
    def _add_axes_batch(self,
        lst_name_axis: List[str]
    ) -> bool:
        """
        批量添加轴
        
        批量操作优化：完成所有添加后只发射一次批量添加信号，避免多次刷新图形。
        """
        # 创建轴
        lst_name_axis_added = []
        bol_has_changes = False
        for str_name_axis in lst_name_axis:
            if self._add_axis_by_name(str_name_axis, bol_emit_signal=False):
                bol_has_changes = True
                lst_name_axis_added.append(str_name_axis)
        
        # 只发射一次批量添加信号
        if bol_has_changes:
            self.sig_axes_batch_added.emit(lst_name_axis_added)
        
        return bol_has_changes

    def _remove_axes_batch(self,
        lst_name_axis: List[str],
        bol_remove_config: bool = False
    ) -> bool:
        """
        批量删除轴
        
        批量操作优化：完成所有删除后只发射一次批量删除信号，避免多次刷新图形。
        """
        # 删除轴
        lst_name_axis_removed = []
        bol_has_changes = False
        for str_name_axis in lst_name_axis:
            if self._remove_axis(str_name_axis, bol_remove_config=bol_remove_config, bol_emit_signal=False):
                bol_has_changes = True
                lst_name_axis_removed.append(str_name_axis)
        
        # 只发射一次批量删除信号
        if bol_has_changes:
            self.sig_axes_batch_removed.emit(lst_name_axis_removed)
        return bol_has_changes

    def _clear_secondary_axes(self) -> bool:
        """
        清除所有次轴，保留主轴
        """
        lst_name_axis_secondary = self.get_lst_name_axis_secondary()
        bol_has_changes = self._remove_axes_batch(
            lst_name_axis_secondary,
            bol_remove_config=False)
        return bol_has_changes
    
    # ============================================================
    # axisconfig 操作
    # ============================================================

    def _create_axisconfig(self,
        str_name_axis: str,
        bol_is_prim_axis: bool = False,
        **kwargs
    ) -> AxisConfig:
        """
        初始化轴配置对象（不添加到字典中）
        """
        # 创建轴配置对象
        axisconfig = AxisConfig(
            str_name_axis=str_name_axis,
            bol_is_prim_axis=bol_is_prim_axis,
            **kwargs
        )
        return axisconfig

    def _add_axisconfig(self,
        axisconfig: AxisConfig
    ) -> bool:
        """
        添加轴配置对象到字典中
        
        如果轴已存在则返回 False。
        """
        str_name_axis = axisconfig.str_name_axis
        if str_name_axis in self.dic_axisconfig:
            self._warning(f"警告: 轴 '{str_name_axis}' 已存在，无法添加")
            return False
        self.dic_axisconfig[str_name_axis] = axisconfig
        return True

    def _remove_axisconfig(self,
        str_name_axis: str
    ) -> bool:
        """
        从字典中删除轴配置对象
        """
        if str_name_axis not in self.dic_axisconfig:
            self._warning(f"警告: 轴配置 '{str_name_axis}' 不存在，无法删除")
            return False
        del self.dic_axisconfig[str_name_axis]
        return True
    
    def _update_axisconfig(self,
        str_name_axis: str,
        axisconfig: AxisConfig
    ) -> bool:
        """
        更新轴配置
        
        Args:
            str_name_axis: 轴名称
            axisconfig: 新的轴配置对象
        """
        if str_name_axis not in self.dic_axisconfig:
            self._warning(f"警告: 轴 '{str_name_axis}' 不存在，无法更新")
            return False
        # 更新配置
        self.dic_axisconfig[str_name_axis] = axisconfig
        # 发射信号
        self.sig_axis_changed.emit(str_name_axis)
        return True

    def _clear_axisconfig(self) -> bool:
        """
        清空所有轴配置
        """
        self.dic_axisconfig.clear()
        return True
    
    # ============================================================
    # set_axis_added 操作
    # ============================================================
    def _add_axis_to_set(self,
        str_name_axis: str
    ) -> bool:
        """
        将轴名称添加到当前使用集合中
        """
        self.set_axis_added.add(str_name_axis)
        return True

    def _remove_axis_from_set(self,
        str_name_axis: str
    ) -> bool:
        """
        将轴名称从当前使用集合中移除
        """
        self.set_axis_added.discard(str_name_axis)
        return True

    def _clear_axis_set(self) -> bool:
        """
        清空当前使用的轴名称集合
        """
        self.set_axis_added.clear()
        return True
    
    # ============================================================
    # 信息获取
    # ============================================================

    ## axisconfig getter
    def get_axisconfig(self, str_name_axis: str) -> Optional[AxisConfig]:
        """
        获取指定轴的配置
        
        Args:
            str_name_axis: 轴名称
            
        Returns:
            AxisConfig 对象，如果不存在则返回 None
        """
        return self.dic_axisconfig.get(str_name_axis)
    
    def get_lst_axisconfig_all_initialized(self) -> List[AxisConfig]:
        """
        获取所有已经存在配置的轴配置列表
        
        Returns:
            轴配置列表
        """
        return list(self.dic_axisconfig.values())

    def get_lst_axisconfig_all_added(self) -> List[AxisConfig]:
        """
        获取所有正在使用的轴配置列表
        
        Returns:
            轴配置列表
        """
        return [
            self.dic_axisconfig[name]
            for name in self.set_axis_added
        ]

    ## 轴名getter
    def get_lst_name_axis_all_added(self) -> List[str]:
        """
        获取所有轴的名称列表
        
        Returns:
            轴名称列表
        """
        return list(self.set_axis_added)
    
    def get_lst_name_axis_all_initialized(self) -> List[str]:
        """
        获取所有已经初始化的轴名称列表
        
        Returns:
            轴名称列表
        """
        return list(self.dic_axisconfig.keys())
    
    def get_dic_axisconfig_all_added(self) -> Dict[str, AxisConfig]:
        """
        获取所有轴配置的字典
        
        Returns:
            轴配置字典的引用（注意：返回的是引用，不是副本）
        """
        return self.dic_axisconfig
    
    def get_lst_name_axis_secondary(self) -> List[str]:
        """
        获取所有次轴（非主轴）的名称列表
        """
        return [
            str_name_axis
            for str_name_axis in self.set_axis_added
            if str_name_axis != self.str_name_axis_main
        ]
    
    def get_name_axis_main(self) -> str:
        """
        获取主轴的名称
        """
        return self.str_name_axis_main

    ## 状态查询
    def is_axis_initialized(self, str_name_axis: str) -> bool:
        """
        检查指定轴是否存在dic_axisconfig中
        """
        return str_name_axis in self.dic_axisconfig
    
    def is_axis_added(self, str_name_axis: str) -> bool:
        """
        检查指定轴是否在当前使用集合中
        """
        return str_name_axis in self.set_axis_added

    def is_axis_primary(self, str_name_axis: str) -> bool:
        """
        检查指定轴是否为主轴
        """
        axisconfig = self.get_axisconfig(str_name_axis)
        if axisconfig is None:
            self._warning(f"警告: 轴 '{str_name_axis}' 不存在，无法判断是否为主轴")
            return False
        # 检查 主轴标记和主轴名称是否一致
        bol_is_prim_axis = axisconfig.bol_is_prim_axis
        bol_is_align_prime_name = (str_name_axis == self.str_name_axis_main)
        if bol_is_prim_axis != bol_is_align_prime_name:
            self._warning(f"警告: 轴 '{str_name_axis}' 主轴标记与名称不一致")
        return bol_is_prim_axis


    def count_axis_initialized(self) -> int:
        """
        获取已经初始化的轴总数
        """
        return len(self.dic_axisconfig)
    
    def count_axis_added(self) -> int:
        """
        获取当前加入使用的轴总数
        """
        return len(self.set_axis_added)

    # ============================================================
    # 公共API方法
    # ============================================================
    
    def add_axis(self, axisconfig: AxisConfig) -> bool:
        """
        添加新的Y轴（公共API，向后兼容）
        
        推荐使用 _add_axis_by_config 或 _add_axis_by_name
        
        Args:
            axisconfig: Y轴配置对象
            
        Returns:
            成功返回 True，如果轴名称已存在则返回 False
        """
        return self._add_axis_by_config(axisconfig, bol_emit_signal=True)
    
    def remove_axis(self, str_name_axis: str) -> bool:
        """
        删除Y轴（公共API，向后兼容）
        
        注意：主轴不允许删除
        推荐使用 _remove_axis
        
        Args:
            str_name_axis: 要删除的轴名称
            
        Returns:
            成功返回 True，如果是主轴或轴不存在则返回 False
        """
        return self._remove_axis(str_name_axis, bol_remove_config=False, bol_emit_signal=True)
    
    def get_axis_config(self, str_name_axis: str) -> Optional[AxisConfig]:
        """
        获取指定轴的配置（向后兼容）
        
        推荐使用 get_axisconfig
        """
        return self.get_axisconfig(str_name_axis)
    
    def get_all_axis_names(self) -> List[str]:
        """
        获取所有轴的名称列表（向后兼容）
        
        推荐使用 get_lst_name_axis_all_added
        """
        return self.get_lst_name_axis_all_added()
    
    def get_all_axis_configs(self) -> Dict[str, AxisConfig]:
        """
        获取所有轴配置的字典（向后兼容）
        
        推荐使用 get_dic_axisconfig_all_added
        """
        return self.get_dic_axisconfig_all_added()
    
    def has_axis(self, str_name_axis: str) -> bool:
        """
        检查指定轴是否存在（向后兼容）
        
        推荐使用 is_axis_added
        """
        return self.is_axis_added(str_name_axis)
    
    def count_yaxis(self) -> int:
        """
        获取Y轴总数（向后兼容）
        
        推荐使用 count_axis_added
        """
        return self.count_axis_added()
    
    def get_yaxis(self, bol_only_secondary: bool = False) -> List[str]:
        """
        获取所有轴或次轴的名称（向后兼容）
        
        推荐使用 get_lst_name_axis_all_added 或 get_lst_name_axis_secondary
        """
        if bol_only_secondary:
            return self.get_lst_name_axis_secondary()
        else:
            return self.get_lst_name_axis_all_added()
    
    def get_yaxis_main(self) -> str:
        """
        获取主轴的名称（向后兼容）
        
        推荐使用 get_name_axis_main
        """
        return self.get_name_axis_main()
    
    def get_secondary_axes(self) -> List[str]:
        """
        获取所有次轴的名称（向后兼容）
        
        推荐使用 get_lst_name_axis_secondary
        """
        return self.get_lst_name_axis_secondary()
    
    def update_axis_config(self, str_name_axis: str, axisconfig: AxisConfig) -> bool:
        """
        更新轴配置（向后兼容）
        
        推荐使用 _update_axisconfig
        """
        return self._update_axisconfig(str_name_axis, axisconfig)
