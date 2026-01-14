#!/usr/bin/python3

import os
from pathlib import Path
import json
from typing import Dict

class ReaderWriterJSONConfig:
    """一个用于读取和写入JSON配置文件的工具类。
    """
    
    def __init__(self):
        pass

    @staticmethod
    def read_configs_from_folder(
        str_path_folder_config: str
    ) -> Dict[str, any]:
        """读取配置文件夹下的所有json配置文件，返回字典，键为文件名（不含扩展名），值为json内容转换的字典

        Args:
            str_path_folder_config (str): 配置文件夹的完整路径
        Returns:
            dict: 配置字典
        """
        # 初始化
        dic_config_rename_col = {}
        path_folder_config = Path(str_path_folder_config)
        # 读取文件夹下的所有json文件
        for str_path_folder_root, lst_str_path_dir, lst_str_name_file in path_folder_config.walk():
            for str_name_file in lst_str_name_file:
                str_name_file_1st_part, str_file_ext = os.path.splitext(str_name_file)
                if str_file_ext == ".json":
                    # 验证是否包含@
                    if '@' not in str_name_file:
                        print(f"Warning: 文件名 {str_name_file} 不包含 '@'，跳过该文件。")
                        continue
                    # 提取键名
                    str_name_file_after_at = str_name_file_1st_part.split('@')[-1]
                    path_file = Path(str_path_folder_root) / str_name_file
                    # 读取json文件
                    dic_single_JSON = ReaderWriterJSONConfig.read_config(
                        str_path_file=path_file,
                        mode='r', encoding='utf-8')
                    dic_config_rename_col[str_name_file_after_at] = dic_single_JSON
        return dic_config_rename_col

    @staticmethod
    def read_config(
        str_path_file: str,
        **kwargs
    ) -> dict:
        """读取JSON配置文件。
        
        参数:
            str_path_file (str): JSON配置文件的路径。
        
        返回:
            dict: 读取的配置字典。
        """
        with open(str_path_file, **kwargs) as file:
            dic_single_config = json.load(file)
        return dic_single_config

    @staticmethod
    def write_config(str_path_file: str, dic_config: Dict[str, any]) -> None:
        """写入JSON配置文件。
        
        参数:
            str_path_file (str): JSON配置文件的路径。
            dic_config (dict): 要写入的配置字典。
        """
        with open(str_path_file, 'w', encoding='utf-8') as file:
            json.dump(dic_config, file, ensure_ascii=False, indent=4)
        return