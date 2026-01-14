#!/usr/bin/python3
from __future__ import annotations
from typing import Dict, Any, List, Optional, Union
import polars as pl
from enum import Enum, auto



class LazyOperationType(Enum):
    """LazyFrame 操作类型枚举
    """
    RENAME = "rename"
    ALIAS = "alias"
    DROP = "drop"
    CAST = "cast"
    EXPR = "expr"
    COMPUTE = "compute"
    
    def __str__(self):
        return self.value


class LazyFrameOperationManager:
    """用于规范化管理 Polars LazyFrame 的 lazy evaluation 操作
    
    该类提供标准化的接口来记录和执行各种 LazyFrame 操作，包括：
    - 列重命名 (rename)
    - 列删除 (drop)
    - 类型转换 (cast)
    - 表达式操作 (expr)
    - 计算新列 (compute)
    
    Attributes:
        lf: 输入的 LazyFrame
        dic_rename: 存储重命名操作的字典 {old_name: new_name}
        lst_cols_to_drop: 存储要删除的列名列表
        lst_expr: 存储表达式操作的列表
        dic_op_history: 存储所有操作历史的字典（用于调试和追踪）
            {
                行为名 : {
                    'action': LazyOperationType.RENAME / LazyOperationType.DROP / LazyOperationType.EXPR,
                        行为类型, 有限
                    'desc': str,          # 行为描述
                    'expr': pl.Expr,           # 仅当 action 为 EXPR 时存在
                    'str_name_col' : str,    # 仅当 action 为 DROP 时存在
                    'str_name_col_old' : str, # 仅当 action 为 RENAME 时
                    'str_name_col_new' : str, # 仅当 action 为 RENAME 时
                }
            }
    """
    
    def __init__(self, lf: pl.LazyFrame):
        """初始化操作管理器
        
        Args:
            lf: 输入的 LazyFrame
        """
        self.lf = lf
        self.dic_rename: Dict[str, str] = {}
        self.lst_cols_to_drop: List[str] = []
        self.lst_expr: List[pl.Expr] = []
        self.dic_op_history: Dict[str, Dict[str, Any]] = {}
        self.obj_depot_column_name : Any = None
        pass
    
    def add_rename(self,
        str_name_col_old: str, 
        str_name_col_new: str,
        str_operation_name: Optional[str] = None
    ) -> LazyFrameOperationManager:
        """添加列重命名操作
        
        Args:
            str_name_old: 旧列名
            str_name_new: 新列名
            str_operation_name: 操作名称（用于历史记录）
            
        Returns:
            self，支持链式调用
        """
        # 添加到重命名字典
        self.dic_rename[str_name_col_old] = str_name_col_new
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"rename_{str_name_col_old}_to_{str_name_col_new}"
        
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.RENAME,
            'str_name_col_old': str_name_col_old,
            'str_name_col_new': str_name_col_new
        }
        
        return self
    
    def add_drop(self,
        str_name_col: str,
        str_operation_name: Optional[str] = None
    ) -> LazyFrameOperationManager:
        """添加列删除操作
        
        Args:
            str_name_col: 要删除的列名
            str_operation_name: 操作名称（用于历史记录）
            
        Returns:
            self，支持链式调用
        """
        if str_name_col not in self.lst_cols_to_drop:
            self.lst_cols_to_drop.append(str_name_col)
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"drop_{str_name_col}"
        
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.DROP,
            'str_name_col': str_name_col
        }
        return self
    
    def add_expr(self,
        expr: pl.Expr,
        str_operation_name: Optional[str] = None,
        desc: Optional[str] = None
    ) -> 'LazyFrameOperationManager':
        """添加表达式操作（如类型转换、新列计算等）
        
        Args:
            expr: Polars 表达式
            str_operation_name: 操作名称（用于历史记录）
            str_description: 操作描述（用于历史记录）
            
        Returns:
            self，支持链式调用
        """
        self.lst_expr.append(expr)
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"expr_operation_{len(self.lst_expr)}"
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.EXPR,
            'desc': desc or 'Expression operation'
        }
        return self
    
    def add_cast(self,
        str_name_col: str,
        dtype: pl.DataType,
        str_operation_name: Optional[str] = None
    ) -> LazyFrameOperationManager:
        """添加类型转换操作
        
        Args:
            str_name_col: 要转换类型的列名
            dtype: 目标数据类型
            str_operation_name: 操作名称（用于历史记录）
            
        Returns:
            self，支持链式调用
        """
        expr = pl.col(str_name_col).cast(dtype=dtype)
        self.lst_expr.append(expr)
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"cast_{str_name_col}_to_{dtype}"
        
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.CAST,
            'column': str_name_col,
            'dtype': str(dtype)
        }
        return self

    def add_alias(self,
        str_name_col_alias: str,
        str_name_col_src: str,
        str_operation_name: Optional[str] = None,
        desc: Optional[str] = None
    ) -> LazyFrameOperationManager:
        """添加计算新列操作
        
        Args:
            str_name_new_col: 新列名
            expr: 计算表达式（不需要 .alias()）
            str_operation_name: 操作名称（用于历史记录）
            str_description: 操作描述
            
        Returns:
            self，支持链式调用
        """
        self.lst_expr.append(pl.col(str_name_col_src).alias(str_name_col_alias))
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"alias_{str_name_col_src}_to_{str_name_col_alias}"
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.COMPUTE,
            'str_name_col': str_name_col_alias,
            'desc': desc or f'Alias from  {str_name_col_src} to {str_name_col_alias}'
        }
        return self

    def add_compute(self,
        str_name_col: str,
        expr: pl.Expr,
        dtype: Optional[pl.DataType],
        str_operation_name: Optional[str] = None,
        desc: Optional[str] = None
    ) -> LazyFrameOperationManager:
        """添加计算新列操作
        
        Args:
            str_name_new_col: 新列名
            expr: 计算表达式（不需要 .alias()）
            str_operation_name: 操作名称（用于历史记录）
            str_description: 操作描述
            
        Returns:
            self，支持链式调用
        """
        self.lst_expr.append(expr.alias(str_name_col).cast(dtype=dtype))
        
        # 记录到历史
        if str_operation_name is None:
            str_operation_name = f"compute_{str_name_col}"
        self.dic_op_history[str_operation_name] = {
            'action': LazyOperationType.COMPUTE,
            'str_name_col': str_name_col,
            'desc': desc or f'Compute new column {str_name_col}'
        }
        return self

    def execute(self) -> pl.LazyFrame:
        """执行所有记录的操作
        
        操作执行顺序：
        1. 列重命名 (rename)
        2. 表达式操作 (with_columns)
        3. 列删除 (drop)
        
        Returns:
            处理后的 LazyFrame
        """
        lf_result = self.lf
        
        # 1. 执行重命名
        if self.dic_rename:
            lf_result = lf_result.rename(self.dic_rename)
        
        # 2. 执行表达式操作
        if self.lst_expr:
            lf_result = lf_result.with_columns(self.lst_expr)
        
        # 3. 执行删除
        if self.lst_cols_to_drop:
            lf_result = lf_result.drop(self.lst_cols_to_drop)
        
        # 存储结果
        self.lf = lf_result
        return lf_result
    
    def collect(self) -> pl.DataFrame:
        """执行所有操作并收集结果为 DataFrame
        
        Returns:
            处理后的 DataFrame
        """
        lf_result = self.execute()
        return lf_result.collect()
    
    def clear(self) -> 'LazyFrameOperationManager':
        """清空所有记录的操作
        
        Returns:
            self，支持链式调用
        """
        self.dic_rename.clear()
        self.lst_cols_to_drop.clear()
        self.lst_expr.clear()
        self.dic_op_history.clear()
        return self
    
    def get_lf(self) -> pl.LazyFrame:
        """获取当前的 LazyFrame
        
        Returns:
            当前的 LazyFrame
        """
        return self.lf

    def get_summary(self) -> Dict[str, Any]:
        """获取操作摘要
        
        Returns:
            包含操作统计信息的字典
        """
        return {
            'rename_count': len(self.dic_rename),
            'drop_count': len(self.lst_cols_to_drop),
            'expr_count': len(self.lst_expr),
            'total_operations': len(self.dic_op_history),
            'rename_mappings': self.dic_rename.copy(),
            'columns_to_drop': self.lst_cols_to_drop.copy()
        }
    
    def print_summary(self):
        """打印操作摘要"""
        summary = self.get_summary()
        print("=== LazyFrame 操作摘要 ===")
        print(f"重命名操作数: {summary['rename_count']}")
        print(f"删除列数: {summary['drop_count']}")
        print(f"表达式操作数: {summary['expr_count']}")
        print(f"总操作数: {summary['total_operations']}")
        
        if summary['rename_mappings']:
            print("\n重命名映射:")
            for old, new in summary['rename_mappings'].items():
                print(f"  {old} -> {new}")
        
        if summary['columns_to_drop']:
            print(f"\n要删除的列: {', '.join(summary['columns_to_drop'])}")
        return

    def set_depot_column_name(self,
        obj_depot_column_name: Any
    ) -> 'LazyFrameOperationManager':
        """设置用于存储对象的列名
        """
        self.obj_depot_column_name = obj_depot_column_name
        return self
    
    def get_name_col(self,
        str_key: str
    ) -> str:
        """获取存储对象的列名
        
        Args:
            str_key: 对象键名
            
        Returns:
            列名
        """
        # 读取参数
        obj_depot_column_name = self.obj_depot_column_name
        if obj_depot_column_name is None:
            raise ValueError("请先通过 set_depot_column_name() 方法设置列名存储对象")
        return obj_depot_column_name.get_name_col(str_key)

    def look(self,
        col_keys: Optional[Union[str, List[str]]] = None,
        expr_filter: Optional[pl.Expr] = None
    ) -> pl.DataFrame:
        """查看当前 LazyFrame 状态（不执行操作）
        
        Returns:
            当前的 LazyFrame
        """
        # 读取参数
        obj_depot_column_name = self.obj_depot_column_name
        if obj_depot_column_name is None:
            raise ValueError("请先通过 set_depot_column_name() 方法设置列名存储对象")
        return obj_depot_column_name.get_col(
            lf=self.get_lf(),
            col_keys=col_keys,
            expr_filter=expr_filter
        )