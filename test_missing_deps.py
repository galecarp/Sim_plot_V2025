#!/usr/bin/env python3
"""
演示：如何模拟缺少依赖的情况
这个脚本会临时隐藏某些模块来测试应用的优雅降级
"""

import sys
import builtins

# 保存原始的 __import__
_original_import = builtins.__import__

def mock_import(name, *args, **kwargs):
    """模拟缺失的模块"""
    # 模拟缺失的模块列表
    blocked_modules = [
        # 'polars',  # 取消注释以模拟缺少polars
        # 'pyqtgraph',  # 取消注释以模拟缺少pyqtgraph
        # 'code_source.polars_toolkits',  # 取消注释以模拟缺少code_source
    ]
    
    for blocked in blocked_modules:
        if name == blocked or name.startswith(blocked + '.'):
            raise ImportError(f"模拟缺失模块: {name}")
    
    return _original_import(name, *args, **kwargs)

def test_with_missing_modules():
    """测试在缺少模块时的行为"""
    print("=" * 60)
    print("测试模式：模拟缺少可选依赖")
    print("=" * 60)
    print("\n修改 blocked_modules 列表来模拟不同的缺失场景\n")
    
    # 替换 __import__
    builtins.__import__ = mock_import
    
    try:
        # 导入并运行应用
        from app.__main__ import main
        print("\n启动应用...\n")
        main(enable_updater=False)
    finally:
        # 恢复原始 __import__
        builtins.__import__ = _original_import

if __name__ == '__main__':
    test_with_missing_modules()
