#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 PySide6 安装是否正常
"""

import sys

def test_pyside6_import():
    """测试 PySide6 模块导入"""
    print("=" * 60)
    print("测试 PySide6 安装")
    print("=" * 60)
    
    print(f"\nPython 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    
    # 测试基本导入
    try:
        import PySide6
        print(f"\n✓ PySide6 导入成功")
        print(f"  版本: {PySide6.__version__}")
        print(f"  位置: {PySide6.__file__}")
    except ImportError as e:
        print(f"\n✗ PySide6 导入失败: {e}")
        return False
    
    # 测试 QtCore
    try:
        from PySide6.QtCore import QTranslator, QLocale, QLockFile
        print(f"✓ QtCore 导入成功")
    except ImportError as e:
        print(f"✗ QtCore 导入失败: {e}")
        return False
    
    # 测试 QtWidgets
    try:
        from PySide6.QtWidgets import QApplication
        print(f"✓ QtWidgets 导入成功")
    except ImportError as e:
        print(f"✗ QtWidgets 导入失败: {e}")
        return False
    
    # 测试 shiboken6
    try:
        import shiboken6
        print(f"✓ shiboken6 导入成功")
        print(f"  版本: {shiboken6.__version__}")
    except ImportError as e:
        print(f"✗ shiboken6 导入失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_pyside6_import()
    sys.exit(0 if success else 1)
