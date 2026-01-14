
#!/usr/bin/env python3

from sklearn.base import BaseEstimator, TransformerMixin

import pandas as pd
import copy

from code_source.preprocessing.preprocessing_GTG.generalgtgtransformer import GeneralGTGTransformer

class DictToDataFrameTransformer(BaseEstimator, TransformerMixin, GeneralGTGTransformer):
    """将字典转换为DataFrame的transformer

    """
    def __init__(self,
        dic_config=None,
        **kwargs
    ) -> None:
        super().__init__(
            dic_config=dic_config,
            **kwargs)
        self._init_dic_config(dic_config)
        pass

    def _init_dic_config(self, dic_config=None, **kwargs):
        super()._init_dic_config(dic_config=dic_config, **kwargs)
        dic_config_default = {
            'str_orient_df_from_dict' : 'index',
        }
        # 替换默认配置
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config_default,
            bol_create_new_key=False,
            bol_replace_dict=True,
        )
        # 更新用户输入的配置
        self._update_key_from_other_dict(
            dic_update_to=self._dic_config,
            dic_update_from=dic_config,
            bol_create_new_key=False,
            bol_replace_dict=False,
        )
        pass

    def generate_dataframe_from_2d_dict(self,
        dic_2d_GTG,
        str_orient_df_from_dict=None,):
        """从二维字典生成DataFrame

        Args
        ----
            dic_2d_GTG : dict
                二维字典
                {
                    pd.timestamp : {
                        str : 值
                    }
                }
        """
        # 读取参数
        str_orient_df_from_dict = self._get_param_with_forced(
            name_param_in_config='str_orient_df_from_dict', val_param=str_orient_df_from_dict)
        # 生成DataFrame
        df_GTG = pd.DataFrame.from_dict(dic_2d_GTG, orient=str_orient_df_from_dict)
        return df_GTG

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = copy.deepcopy(X)
        df_save = self.generate_dataframe_from_2d_dict(X)
        return df_save


