#!/usr/bin/env python3

from contextlib import contextmanager
from typing import Generator, Dict, List, Any, Optional, Callable
from abc import ABC, ABCMeta, abstractmethod
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QStatusBar
from copy import deepcopy
import logging


class QABCMeta(type(QObject), ABCMeta):
    """组合元类，解决QObject和ABC的元类冲突"""
    pass


class AbstractManager(QObject, ABC, metaclass=QABCMeta):
    """
    抽象管理器基类
    
    提供所有管理器的基础功能和接口,包括:
    - 统一的信号管理
    - 统一的日志和用户消息输出
    - 子类信号注册机制
    
    Attributes:
        dic_signals: 管理器信号字典 {str_signal_name: Signal}
        logger: 日志记录器
        
    User Message Signals (用户可见消息):
        sig_info: 一般信息提示
        sig_warning: 警告信息
        sig_error: 错误信息
        sig_success: 成功信息
    """
    
    # ============================================================
    # 用户消息信号 - 所有Manager共享
    # ============================================================
    sig_info = Signal(str)      # 一般信息
    sig_warning = Signal(str)   # 警告
    sig_error = Signal(str)     # 错误
    sig_success = Signal(str)   # 成功
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化抽象管理器
        
        Args:
            parent: 父对象 (可选)
        """
        super().__init__(parent)
        
        # 初始化日志记录器
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 子类特定信号字典 (由子类在_init_signals中填充)
        self.dic_signals: Dict[str, Signal] = {}
        self.dic_signals_msg: Dict[str, Signal] = {}
        
        # 初始化信号
        self._init_signals()
        
        # 将用户消息信号加入字典
        self._register_msg_signals()
        pass
    
    def _register_msg_signals(self):
        """
        注册通用户消息信号到字典
        """
        self.dic_signals_msg.update({
            "sig_info": self.sig_info,
            "sig_warning": self.sig_warning,
            "sig_error": self.sig_error,
            "sig_success": self.sig_success,
        })
        pass

    # ============================================================
    # 抽象方法 - 子类必须实现
    # ============================================================
    
    @abstractmethod
    def _init_signals(self):
        """
        初始化子类特定的信号
        
        子类应在此方法中:
        1. 定义类级别的信号
        2. 将信号注册到 self.dic_signals
        
        Example:
            def _init_signals(self):
                self.dic_signals = {
                    "sig_curve_added": self.sig_curve_added,
                    "sig_curve_removed": self.sig_curve_removed,
                }
        """
        pass

    @abstractmethod
    def _connect_signals(self):
        """
        连接下游的信号
        
        子类应在此方法中连接需要监听的下游管理器信号
        """
        pass
    
    @abstractmethod
    def _get_state_snapshot(self) -> Dict[str, Any]:
        """
        获取当前状态快照（子类实现）
        
        Returns:
            状态字典，用于回滚
        """
        pass
    
    @abstractmethod
    def _restore_state_snapshot(self, dic_snapshot: Dict[str, Any]):
        """
        恢复状态快照（子类实现）
        
        Args:
            dic_snapshot: 之前保存的状态字典
        """
        pass


    # ============================================================
    # 原子操作管理器
    # ============================================================

    @contextmanager
    def _atomic_operation(self) -> Generator[None, None, None]:
        """
        通用原子操作上下文管理器
        
        自动保存状态快照，失败时自动回滚
        
        Usage:
            with self._atomic_operation():
                # 进行一系列操作
                # 如果抛出异常，自动回滚
        """
        # 保存状态快照（调用子类实现）
        dic_snapshot = self._get_state_snapshot()
        
        try:
            yield  # 执行操作
            # 成功，不需要回滚
        except Exception as e:
            # 失败，回滚到快照状态（调用子类实现）
            self._restore_state_snapshot(dic_snapshot)
            self._error(f"操作失败，已回滚: {e}")
            raise  # 重新抛出异常
        return
    
    # ============================================================
    # 信号管理 - 公共接口
    # ============================================================
    
    def _connect_signals_to_slot(self, slot: Slot):
        """
        连接所有子类信号到指定的槽函数
        """
        for name, signal in self.dic_signals.items():
            signal.connect(slot)
        return

    def get_signal(self, str_name_signal: str) -> Signal:
        """
        获取指定名称的信号
        
        Args:
            str_name_signal: 信号名称
            
        Returns:
            对应的 Signal 实例
            
        Raises:
            KeyError: 如果信号名称不存在
        """
        if str_name_signal not in self.dic_signals:
            self._error(f"Signal '{str_name_signal}' not found in {self.__class__.__name__}.")
        return self.dic_signals[str_name_signal]
    
    def get_signal_all(self) -> Dict[str, Signal]:
        """
        获取所有信号的字典
        
        Returns:
            信号字典 (包括子类信号和通用消息信号)
        """
        return self.dic_signals
    
    def get_lst_name_signals(self) -> List[str]:
        """
        获取所有信号的名称列表
        
        Returns:
            信号名称列表
        """
        return list(self.dic_signals.keys())

    # ============================================================
    # 用户消息输出 - 统一接口
    # ============================================================
    
    def _info(self, message: str, bol_log: bool = True):
        """
        显示一般信息
        
        Args:
            message: 消息内容
            bol_log: 是否同时记录到日志
        """
        if bol_log:
            self.logger.info(message)
        self.sig_info.emit(message)
        return
    
    def _warning(self, message: str, bol_log: bool = True):
        """
        显示警告信息
        
        Args:
            message: 消息内容
            bol_log: 是否同时记录到日志
        """
        if bol_log:
            self.logger.warning(message)
        self.sig_warning.emit(message)
        return
    
    def _error(self, message: str, bol_log: bool = True):
        """
        显示错误信息
        
        Args:
            message: 消息内容
            bol_log: 是否同时记录到日志
        """
        if bol_log:
            self.logger.error(message)
        self.sig_error.emit(message)
        return
    
    def _success(self, message: str, bol_log: bool = True):
        """
        显示成功信息
        
        Args:
            message: 消息内容
            bol_log: 是否同时记录到日志
        """
        if bol_log:
            self.logger.info(f"SUCCESS: {message}")
        self.sig_success.emit(message)
        return
    
    # ============================================================
    # 调试日志 - 仅记录不发送信号
    # ============================================================
    
    def _log_debug(self, message: str):
        """调试日志 (不发送用户信号)"""
        self.logger.debug(message)
        return
    
    def _log_info(self, message: str):
        """信息日志 (不发送用户信号)"""
        self.logger.info(message)
        return
    
    def _log_warning(self, message: str):
        """警告日志 (不发送用户信号)"""
        self.logger.warning(message)
        return
    
    def _log_error(self, message: str):
        """错误日志 (不发送用户信号)"""
        self.logger.error(message)
        return

    # ============================================================
    # 便捷方法 - 连接用户消息信号到UI
    # ============================================================
    
    def connect_to_statusbar(self, statusbar:QStatusBar):
        """
        连接用户消息信号到状态栏
        
        Args:
            statusbar: QStatusBar 实例
            
        Example:
            manager.connect_to_statusbar(self.statusBar())
        """
        self.sig_info.connect(lambda msg: statusbar.showMessage(msg, 3000))
        self.sig_success.connect(lambda msg: statusbar.showMessage(f"✓ {msg}", 3000))
        self.sig_warning.connect(lambda msg: statusbar.showMessage(f"⚠ {msg}", 5000))
        self.sig_error.connect(lambda msg: statusbar.showMessage(f"✗ {msg}", 5000))
        return
    
    def connect_to_message_handler(self, handler: Callable[[str, str], None]):
        """
        连接用户消息信号到自定义处理器
        
        Args:
            handler: 消息处理函数 handler(message: str, level: str)
            
        Example:
            def my_handler(message, level):
                print(f"[{level}] {message}")
            
            manager.connect_to_message_handler(my_handler)
        """
        self.sig_info.connect(lambda msg: handler(msg, "info"))
        self.sig_warning.connect(lambda msg: handler(msg, "warning"))
        self.sig_error.connect(lambda msg: handler(msg, "error"))
        self.sig_success.connect(lambda msg: handler(msg, "success"))
