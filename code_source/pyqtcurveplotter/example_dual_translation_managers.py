#!/usr/bin/env python3
"""
双管理器（UI翻译 + 列名翻译）使用示例

演示如何在 PolarsMultiCurveViewer 中同时使用:
1. UITranslationManager - 管理UI元素（按钮、标签等）的翻译
2. ColNameManager - 管理数据列名的翻译
"""

import sys
import polars as pl
from PyQt6.QtWidgets import QApplication
from code_source.pyqtcurveplotter.polarsmulticurveviewer import PolarsMultiCurveViewer
from code_source.pyqtcurveplotter.enums.languageenum import LanguageEnum


def create_sample_data():
    """创建示例数据"""
    df = pl.DataFrame({
        "timestamp": range(1000),
        "power_generation": [100 + i * 0.1 for i in range(1000)],
        "temperature": [25 + (i % 100) * 0.05 for i in range(1000)],
        "efficiency": [0.85 + (i % 50) * 0.001 for i in range(1000)],
    })
    return df.lazy()


def create_column_name_mapping():
    """
    创建列名的多语言映射
    
    注意：这是用于 ColNameManager 的字典映射
    不同于 Qt 的 .tr() 翻译文件
    """
    return {
        "timestamp": {
            LanguageEnum.CN.value: "时间戳",
            LanguageEnum.EN.value: "Timestamp",
        },
        "power_generation": {
            LanguageEnum.CN.value: "发电功率 [MW]",
            LanguageEnum.EN.value: "Power Generation [MW]",
        },
        "temperature": {
            LanguageEnum.CN.value: "温度 [°C]",
            LanguageEnum.EN.value: "Temperature [°C]",
        },
        "efficiency": {
            LanguageEnum.CN.value: "效率 [%]",
            LanguageEnum.EN.value: "Efficiency [%]",
        },
    }


def main():
    """主函数"""
    print("=" * 80)
    print("双管理器多语言系统示例")
    print("=" * 80)
    
    # 创建 Qt 应用程序
    app = QApplication(sys.argv)
    
    # 创建数据
    lf = create_sample_data()
    
    # 创建列名映射
    column_mapping = create_column_name_mapping()
    
    # 创建可视化窗口
    viewer = PolarsMultiCurveViewer(
        lf=lf,
        str_name_col_timestamp="timestamp",
        dic_map_col_to_display_language=column_mapping,
        str_language_current=LanguageEnum.CN.value  # 初始语言：中文
    )
    
    # 显示窗口
    viewer.show()
    
    # 打印管理器信息
    print("\n管理器信息:")
    print(f"  UI翻译管理器观察者数量: {viewer.manager_ui_translation.get_observer_count()}")
    print(f"  列名管理器观察者数量: {viewer.manager_colname.get_observer_count()}")
    
    print("\n当前设置:")
    print(f"  UI语言: {viewer.manager_ui_translation.get_language()}")
    print(f"  列名语言: {viewer.manager_colname.str_language_current}")
    
    print("\n列名映射示例:")
    for col in ["power_generation", "temperature"]:
        display_name = viewer.get_display_name(col)
        print(f"  {col} → {display_name}")
    
    # 可以通过编程方式切换语言
    # viewer.set_language(LanguageEnum.EN.value)  # 切换到英文
    
    print("\n" + "=" * 80)
    print("提示:")
    print("  1. 窗口标题等UI元素使用 .tr() 方法，由 UITranslationManager 管理")
    print("  2. 数据列名使用字典映射，由 ColNameManager 管理")
    print("  3. 调用 viewer.set_language() 会同时更新两者")
    print("=" * 80)
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
