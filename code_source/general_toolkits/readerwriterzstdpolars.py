#!/usr/bin/python3

import os
from pathlib import Path
from typing import Optional, Union, List
import polars as pl
import pickle
import tarfile
import zstandard as zstd
import io

class ReaderWriterZstdPolars():
    """
    处理 zstd 压缩的 tar 包的读写操作，特别是与 Polars 数据框相关的操作
    """
    def __init__(self):
        pass

    @staticmethod
    def save_df_pl_to_parquet(
        df_pl : Union[pl.DataFrame, pl.LazyFrame],
        str_path_file : str = None,
        compression_level: int = 11,
        **kwargs
    ):
        """将 Polars DataFrame 压缩为 parquet 格式的 zstd 字节流
        
        Args:
            df_pl: Polars DataFrame 对象
            compression_level: zstd 压缩级别，默认为 3
            str_path_file: 可选的保存路径，如果提供则保存为文件，否则返回字节数据
        """
        # 如果指定了保存路径，则直接保存为文件
        if str_path_file is None:
            str_path_cwd = os.getcwd()
            str_path_file = os.path.join(str_path_cwd, 'data.parquet')
        # 保存为 parquet 文件，使用 zstd 压缩
        df_pl.write_parquet(
            str_path_file,
            compression='zstd',
            compression_level=compression_level,
            **kwargs
        )
        return

    @staticmethod
    def read_df_pl_from_parquet(
        str_path_file: str,
        columns: Optional[Union[List[int], List[str], None]] = None,
        bol_lazy: bool = False,
        **kwargs
    ) -> pl.DataFrame:
        """读取 zstd 压缩的 parquet 字节流为 Polars DataFrame
        
        Args:
            str_path_file: zstd 压缩的 parquet 文件路径
            columns: 要读取的列，可以是列索引列表或列名列表，默认为 None，表示读取所有列
        
        Returns:
            解压后的 Polars DataFrame
        """
        # 读取为 Polars DataFrame
        if bol_lazy:
            lf_pl = pl.scan_parquet(
                str_path_file,
                **kwargs
            )
            # 如果指定了列，进行选择
            if columns is not None:
                lf_pl = lf_pl.select(columns)
            return lf_pl 
        else:
            df_pl = pl.read_parquet(
                str_path_file,
                columns=columns,
                **kwargs
            )
            return df_pl
    
    @staticmethod
    def save_df_pl_to_csv(
        df_pl : Union[pl.DataFrame, pl.LazyFrame],
        str_path_file : str = None,
        lst_name_col_timestamp: Optional[list]=None,
        str_format_timestamp: str="%Y-%m-%d %H:%M:%S",
        **kwargs
    ):
        """将 Polars DataFrame 保存为 CSV 格式的文件
        
        Args:
            df_pl: Polars DataFrame 对象
            str_path_file: 可选的保存路径，如果提供则保存为文件，否则返回字节数据
        """
        # 如果指定了保存路径，则直接保存为文件
        if str_path_file is None:
            str_path_cwd = os.getcwd()
            str_path_file = os.path.join(str_path_cwd, 'data.csv')
        # 将指定列转换解析为字符串格式, 以便保存为 CSV
        if lst_name_col_timestamp is not None:
            for str_col in lst_name_col_timestamp:
                # 检查列是否存在（对于 LazyFrame 需要特殊处理）
                if isinstance(df_pl, pl.LazyFrame):
                    # LazyFrame 使用 columns 属性
                    if str_col in df_pl.columns:
                        df_pl = df_pl.with_columns(
                            pl.col(str_col).dt.strftime(str_format_timestamp)
                        )
                else:
                    # pl dataframe
                    if str_col in df_pl.columns:
                        df_pl = df_pl.with_columns(
                            pl.col(str_col).dt.strftime(str_format_timestamp)
                        )
        
        # 如果是 LazyFrame，先执行计算
        if isinstance(df_pl, pl.LazyFrame):
            df_pl = df_pl.collect()
        
        # 保存为 CSV 文件
        df_pl.write_csv(
            str_path_file,
            **kwargs
        )
        return
    
    @staticmethod
    def read_df_pl_from_csv(
        str_path_file: str,
        columns: Optional[Union[List[int], List[str], None]] = None,
        bol_lazy: bool = False,
        **kwargs
    ) -> pl.DataFrame:
        """读取 CSV 文件为 Polars DataFrame
        
        Args:
            str_path_file: CSV 文件路径
            columns: 要读取的列，可以是列索引列表或列名列表，默认为 None，表示读取所有列
        
        Returns:
            读取的 Polars DataFrame
        """
        if bol_lazy:
            # 使用 lazy reading
            lf = pl.scan_csv(
                str_path_file,
                **kwargs
            )
            # 如果指定了列，进行选择
            if columns is not None:
                lf = lf.select(columns)
            return lf
        else:
            # 读取为 Polars DataFrame
            df_pl = pl.read_csv(
                str_path_file,
                columns=columns,
                **kwargs
            )
            return df_pl
            