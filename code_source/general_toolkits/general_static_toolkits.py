#!/usr/bin/env python3

import os
import sys
import copy
import pandas as pd

class General_Static_Toolkits():
    """静态方法集合

    """

    @staticmethod
    def _update_key_from_other_dict(self,
            dic_update_to=None,
            dic_update_from=None,
            bol_create_new_key=False,
            bol_replace_dict=False,
            **kwargs
        ):
            """把dic_update_from中的key-value更新到dic_update_to中

            Args
            ----
            dic_update_to : dict
                被更新的字典
            dic_update_from : dict
                更新的字典的信息来源
            bol_create_new_key : bool
                如果为True, 则如果dic_update_from中的某个key在dic_update_to中不存在, 则创建新的key
                如果为False, 则多出的新key会报错
            bol_replace_dict : bool
                如果为True, 则用dic_update_from直接替换dic_update_to
                如果为False, 则更新key而非替换

            """
            # 复制来源字典
            dic_update_from = copy.deepcopy(dic_update_from)
            if bol_replace_dict:
                # 直接替换
                dic_update_to.clear()
                dic_update_to.update(dic_update_from)
            else:
                if dic_update_from is not None:
                    for key_from, val_from in dic_update_from.items():
                        if not bol_create_new_key and key_from not in dic_update_to:
                            raise ValueError(
                                f'输出字典中有要更新字典中不带有的新key, 输入key为{key_from}\n'+\
                                '但设置bol_create_new_key为False, 不允许创建新的key'
                            )
                        else:
                            # 更新已有的key
                            dic_update_to.update({key_from : val_from})
            return
    
    @staticmethod
    def _get_dir_base(self,
        n_level=2):
        """获取项目根目录

        """
        # 定位项目根目录
        dir_current = os.getcwd()
        n_level = 2
        dir_base = dir_current
        for i in range(n_level):    
            dir_base= os.path.dirname(dir_base)
        sys.path.insert(0, dir_base)
        print('获得的项目根目录为: {}', dir_base)
        return dir_base
