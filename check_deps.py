#!/usr/bin/env python3
"""快速测试依赖"""
import sys

try:
    import PySide6
    print("✅ PySide6")
except ImportError:
    print("❌ PySide6")

try:
    import qasync
    print("✅ qasync")
except ImportError:
    print("❌ qasync")

try:
    import httpx
    print("✅ httpx")
except ImportError:
    print("❌ httpx")

try:
    import polars
    print("✅ polars")
except ImportError:
    print("❌ polars")

try:
    import pyqtgraph
    print("✅ pyqtgraph")
except ImportError:
    print("❌ pyqtgraph")

try:
    from code_source.polars_toolkits.datetime_toolkits.utilpolarsdatetime import get_timestamp_min_max
    print("✅ code_source (polars_toolkits)")
except ImportError as e:
    print(f"❌ code_source - {e}")

print("\n程序可以启动：", end="")
try:
    import PySide6
    import qasync
    import httpx
    print("是 ✅")
except ImportError:
    print("否 ❌")
