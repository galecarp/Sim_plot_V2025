#!/usr/bin/env python3
"""
生成翻译文件的脚本

用法：
1. 提取所有待翻译文本: python generate_translations.py extract
2. 编辑 translations/*.ts 文件进行翻译
3. 编译翻译文件: python generate_translations.py compile
"""

import subprocess
import sys
from pathlib import Path


def extract_translations():
    """
    提取待翻译的文本，生成 .ts 文件
    """
    # 项目根目录
    project_dir = Path(__file__).parent.parent
    
    # 翻译文件输出目录
    translations_dir = project_dir / 'i18n' / 'translations'
    translations_dir.mkdir(parents=True, exist_ok=True)
    
    # 要扫描的Python文件
    source_files = list(project_dir.glob('**/*.py'))
    source_files_str = ' '.join(str(f) for f in source_files)
    
    # 支持的语言
    languages = ['en', 'ja']  # 英文、日文
    
    for lang in languages:
        ts_file = translations_dir / f'pyqtcurveplotter_{lang}.ts'
        
        # 使用 pylupdate6 提取翻译
        cmd = f'pylupdate6 {source_files_str} -ts {ts_file}'
        
        print(f"正在生成 {lang} 翻译文件...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 成功生成: {ts_file}")
        else:
            print(f"✗ 失败: {result.stderr}")
    
    print(f"\n请使用 Qt Linguist 编辑 {translations_dir}/*.ts 文件进行翻译")


def compile_translations():
    """
    编译 .ts 文件为 .qm 文件
    """
    translations_dir = Path(__file__).parent.parent / 'i18n' / 'translations'
    
    if not translations_dir.exists():
        print(f"翻译目录不存在: {translations_dir}")
        return
    
    ts_files = list(translations_dir.glob('*.ts'))
    
    if not ts_files:
        print("没有找到 .ts 文件")
        return
    
    for ts_file in ts_files:
        qm_file = ts_file.with_suffix('.qm')
        
        # 使用 lrelease 编译
        cmd = f'lrelease {ts_file} -qm {qm_file}'
        
        print(f"正在编译 {ts_file.name}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 成功编译: {qm_file}")
        else:
            print(f"✗ 失败: {result.stderr}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python generate_translations.py extract   # 提取待翻译文本")
        print("  python generate_translations.py compile   # 编译翻译文件")
        return
    
    action = sys.argv[1]
    
    if action == 'extract':
        extract_translations()
    elif action == 'compile':
        compile_translations()
    else:
        print(f"未知操作: {action}")


if __name__ == '__main__':
    main()
