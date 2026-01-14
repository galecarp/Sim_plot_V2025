#!/usr/bin/env python3
"""
生成示例数据用于测试 Plotter 模块

运行此脚本将生成一个包含时序数据的 Parquet 文件
"""

import polars as pl
import numpy as np
from pathlib import Path


def generate_example_data(
    n_points: int = 1000,
    output_file: str = "example_timeseries.parquet"
):
    """
    生成示例时序数据
    
    Args:
        n_points: 数据点数量
        output_file: 输出文件路径
    """
    # 生成时间序列（小时）
    time = np.linspace(0, 100, n_points)
    
    # 生成不同的数据序列
    data = {
        "时间": time,
        "温度": 20 + 5 * np.sin(2 * np.pi * time / 24) + np.random.randn(n_points) * 0.5,
        "压力": 100 + 10 * np.cos(2 * np.pi * time / 12) + np.random.randn(n_points) * 1.0,
        "流量": 50 + 15 * np.sin(2 * np.pi * time / 48) + np.random.randn(n_points) * 2.0,
        "功率": 1000 + 200 * np.sin(2 * np.pi * time / 36) + np.random.randn(n_points) * 20,
        "效率": 80 + 10 * np.cos(2 * np.pi * time / 24) + np.random.randn(n_points) * 2.0,
    }
    
    # 创建 DataFrame
    df = pl.DataFrame(data)
    
    # 保存为 Parquet
    output_path = Path(output_file)
    df.write_parquet(output_path)
    
    print(f"✅ 示例数据已生成: {output_path.absolute()}")
    print(f"   数据点数: {n_points}")
    print(f"   时间范围: {time[0]:.2f} ~ {time[-1]:.2f} 小时")
    print(f"   列数: {len(df.columns)}")
    print(f"\n数据预览:")
    print(df.head(5))
    
    return output_path


if __name__ == "__main__":
    generate_example_data()
