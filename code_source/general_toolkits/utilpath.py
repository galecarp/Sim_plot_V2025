#!/usr/bin/python3

import os
from pathlib import Path

class UtilPath:
    """一个用于处理灵活驱动器字母的工具类。
    """
    
    def __init__(self):
        pass

    @staticmethod
    def get_drive_letter(str_path: str) -> str:
        """获取路径中的驱动器字母。
        
        参数:
            str_path (str): 文件或目录的路径。
        
        返回:
            str: 驱动器字母（例如 'C:'），如果没有驱动器字母则返回空字符串。
        """
        path = Path(str_path)
        str_drive = path.drive
        return str_drive

    @staticmethod
    def change_drive_letter(
        str_path: str,
        str_drive: str
    ) -> str:
        """更改路径中的驱动器字母。
        
        参数:
            str_path (str): 原始路径。
            str_drive (str): 新的驱动器字母（例如 'D:'）。
        
        返回:
            str: 更改后的路径。
        """
        # 检查str_drive格式是否正确
        if not str_drive.endswith(':'):
            str_drive += ':'
        path = Path(str_path)
        str_rest = path.relative_to(path.anchor)
        path_changed = Path(str_drive + os.sep) / str_rest
        return str(path_changed)
    
    @staticmethod
    def get_path_file_local_global(
        str_path_local : str,
        str_path_global : str,
        str_name_folder : str,
        str_name_file : str,
        str_drive : str=None,
    ):
        """ 检验本地文件路径是否存在，若不存在则返回全局路径。
        如果提供了 str_drive，则将路径更改为指定的驱动器字母。
        """
        bol_local = True
        ## 先从本地variant路径读取
        path_file_local = Path(str_path_local) / str_name_folder / str_name_file
        ### 更改盘符
        if str_drive:
            str_path_file_local = UtilPath.change_drive_letter(
                str_path = path_file_local,
                str_drive=str_drive
            )
        ### 检查文件是否存在
        if not Path(str_path_file_local).is_file():
            bol_local = False
            ## 再从全局配置路径读取
            path_file_global = Path(str_path_global) / str_name_folder / str_name_file
            ### 更改盘符
            if str_drive:
                str_path_file_global = UtilPath.change_drive_letter(
                    str_path = path_file_global,
                    str_drive=str_drive
                )
            ### 检查文件是否存在
            if not Path(str_path_file_global).is_file():
                raise FileNotFoundError(
                    f"全局和局部都未找到列配置文件"+\
                    f"本地路径: {str_path_file_local}"+\
                    f"全局路径: {str_path_file_global}"
                )
        # 返回路径
        if bol_local:
            return str_path_file_local
        else:
            return str_path_file_global
    