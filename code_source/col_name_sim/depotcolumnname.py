#!/usr/bin/python3

import os
from typing import Dict, Any
import polars as pl
from typing import Dict, Any, List, Optional, Union

from code_source.general_toolkits.dicttoolkit import _update_key_from_other_dict


class DepotColumnName():
    """
    用于管理和存储列名的类
    """
    def __init__(self):
        """初始化列名字典
        """
        self._init_dic_domain()
        self._init_dic_name_col()
        super().__init__()
        pass

    def _init_dic_domain(self,
    ):
        """ 初始化领域字典

        """
        self.dic_init_domain = {
            "GEN": self._init_dic_name_col_gen,
            "WTPV": self._init_dic_name_col_wtpv,
            "USER": self._init_dic_name_col_user,
            "GT": self._init_dic_name_col_gt,
            "PG": self._init_dic_name_col_pg,
            "BESS": self._init_dic_name_col_bess,
            "H2": self._init_dic_name_col_h2,
            "CH4": self._init_dic_name_col_ch4,
            "NH3": self._init_dic_name_col_nh3,
            "STM": self._init_dic_name_col_stm,
            "OTHER": self._init_dic_name_col_other,
        }
        pass

    def _init_dic_name_col(self,
    ):
        """初始化列名字典

        Args:
            dic_name_col_global: 列名字典，格式为 { "logical_name": "actual_column_name" }
        """
        # 扁平化全局列名字典
        self.dic_name_col_global = {}
        # 分领域初始化列名字典
        self.dic_name_col_domain = {}
        # 初始化所有领域的列名
        for str_name_domain, func_init in self.dic_init_domain.items():
            func_init()
        pass

    def _init_dic_name_col_gen(self,
        dic_name_col=None
    ):
        """初始化通用列名字典

        """
        # 默认
        str_name_domain = 'GEN'
        dic_name_col_general_default = {
            'str_key_ts_TimeStamp_GEN_begin_slice' : 'ts_TimeStamp_{GEN,time,begin,slice}',
            'str_key_flt_Power_GEN_balance_slice' : 'flt_Power_{GEN,CALC,balance,slice}',
            'str_key_flt_Energy_GEN_balance_slice' : 'flt_Energy_{GEN,CALC,balance,slice}',
            'str_key_flt_Temp_GEN_ENV_slice' : 'flt_Temp_{GEN,ENV,temperature,slice}',
            'str_key_flt_TimeInterval_slice': 'flt_TimeInterval_{GEN,time,slice}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_general_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_wtpv(self,
        dic_name_col=None
    ):
        """初始化WT&PV列名字典
        """
        # 默认
        str_name_domain = 'WTPV'
        dic_name_col_wtpv_default = {
            # 功率
            'str_key_flt_Power_WT_elec_output_slice' : 'flt_Power_{WTPV,WT,elec-output,slice}',
            'str_key_flt_Power_PV_elec_output_slice' : 'flt_Power_{WTPV,PV,elec-output,slice}',
            'str_key_flt_Power_WTPV_elec_output_slice' : 'flt_Power_{WTPV,WTPV,elec-output,slice}',
            'str_key_flt_Power_WTPV_demand_elec_to_slice' : 'flt_Power_{WTPV,WTPV,demand,elec-to_real,slice}',
            'str_key_flt_Power_WTPV_BESS_elec_to_avail_slice' : 'flt_Power_{WTPV,WTPV,BESS,elec-to_real_avail,slice}',
            'str_key_flt_Power_WTPV_BESS_elec_to_real_slice' : 'flt_Power_{WTPV,WTPV,BESS,elec-to_real,slice}',
            'str_key_flt_Power_WTPV_ELY_elec_to_avail_slice' : 'flt_Power_{WTPV,WTPV,ELY,elec-to_avail,slice}',
            'str_key_flt_Power_WTPV_ELY_elec_to_real_slice' : 'flt_Power_{WTPV,WTPV,ELY,elec-to_real,slice}',
            'str_key_flt_Power_WTPV_EB_elec_to_avail_slice' : 'flt_Power_{WTPV,WTPV,EB,elec-to_avail,slice}',
            'str_key_flt_Power_WTPV_EB_elec_to_real_slice' : 'flt_Power_{WTPV,WTPV,EB,elec-to_real,slice}',
            'str_key_flt_Power_WTPV_waste_elec_to_real_slice' : 'flt_Power_{WTPV,WTPV,waste,elec-to_real,slice}',
            # 能量
            'str_key_flt_Energy_WT_elec_output_slice' : 'flt_Energy_{WTPV,WT,elec-output,slice}',
            'str_key_flt_Energy_PV_elec_output_slice' : 'flt_Energy_{WTPV,PV,elec-output,slice}',
            'str_key_flt_Energy_WTPV_elec_output_slice' : 'flt_Energy_{WTPV,WTPV,elec-output,slice}',
            'str_key_flt_Energy_WTPV_demand_elec_to_slice' : 'flt_Energy_{WTPV,WTPV,demand,elec-to_real,slice}',
            'str_key_flt_Energy_WTPV_BESS_elec_to_avail_slice' : 'flt_Energy_{WTPV,WTPV,BESS,elec-to_avail,slice}',
            'str_key_flt_Energy_WTPV_BESS_elec_to_real_slice' : 'flt_Energy_{WTPV,WTPV,BESS,elec-to_real,slice}',
            'str_key_flt_Energy_WTPV_ELY_elec_to_avail_slice' : 'flt_Energy_{WTPV,WTPV,ELY,elec-to_avail,slice}',
            'str_key_flt_Energy_WTPV_ELY_elec_to_real_slice' : 'flt_Energy_{WTPV,WTPV,ELY,elec-to_real,slice}',
            'str_key_flt_Energy_WTPV_EB_elec_to_avail_slice' : 'flt_Energy_{WTPV,WTPV,EB,elec-to_avail,slice}',
            'str_key_flt_Energy_WTPV_EB_elec_to_real_slice' : 'flt_Energy_{WTPV,WTPV,EB,elec-to_real,slice}',
            'str_key_flt_Energy_WTPV_waste_elec_to_real_slice' : 'flt_Energy_{WTPV,WTPV,waste,elec-to_real,slice}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_wtpv_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_user(self,
        dic_name_col=None
    ):
        """初始化USER列名字典
        """
        # 默认
        str_name_domain = 'USER'
        dic_name_col_user_default = {
            # 功率
            'str_key_flt_Power_USER_elec_consume_slice' : 'flt_Power_{USER,user,elec-consume,slice}',
            # 能量
            'str_key_flt_Energy_USER_elec_consume_slice' : 'flt_Energy_{USER,user,elec-consume,slice}',
            'str_key_flt_Energy_USER_user_WTPV_elec_from_slice' : 'flt_Energy_{USER,user,WTPV,elec-from,slice}',
            'str_key_flt_Energy_USER_user_BESS_elec_from_slice' : 'flt_Energy_{USER,user,BESS,elec-from,slice}',
            'str_key_flt_Energy_USER_user_GT_elec_from_slice' : 'flt_Energy_{USER,user,GT,elec-from,slice}',
            'str_key_flt_Energy_USER_user_PG_elec_from_slice' : 'flt_Energy_{USER,user,PG,elec-from,slice}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_user_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_gt(self,
        dic_name_col=None
    ):
        """初始化gt列名字典
        """
        # 默认
        str_name_domain = 'GT'
        dic_name_col_gt_default = {
            # 功率
            ## 总和
            'str_key_flt_Power_GT_elec_output_slice' : 'flt_Power_{GT,GT,elec-output,slice}',
            ## 给用户
            'str_key_flt_Power_GT_demand_elec_to_real_slice' : 'flt_Power_{GT,GT,demand,elec-to_real,slice}',
            ## 给BESS
            'str_key_flt_Power_GT_BESS_elec_to_avail_slice' : 'flt_Power_{GT,GT,BESS,elec-to_avail,slice}',
            'str_key_flt_Power_GT_BESS_elec_to_real_slice' : 'flt_Power_{GT,GT,BESS,elec-to_real,slice}',
            ## 给H2的ELY
            'str_key_flt_Power_GT_ELY_elec_to_avail_slice' : 'flt_Power_{GT,GT,ELY,elec-to_avail,slice}',
            'str_key_flt_Power_GT_ELY_elec_to_real_slice' : 'flt_Power_{GT,GT,ELY,elec-to_real,slice}',
            ## 给EB
            'str_key_flt_Power_GT_EB_elec_to_avail_slice' : 'flt_Power_{GT,GT,EB,elec-to_avail,slice}',
            'str_key_flt_Power_GT_EB_elec_to_real_slice' : 'flt_Power_{GT,GT,EB,elec-to_real,slice}',
            ## 给浪费
            'str_key_flt_Power_GT_waste_elec_to_real_slice' : 'flt_Power_{GT,GT,waste,elec-to_real,slice}',
            
            # 其他
            'str_key_idx_Tank_GT_FuelTank_use_slice' : 'idx_Tank_{GT,FuelTank,use,slice}',
            
            # 能量
            ## 给用户
            'str_key_flt_Energy_GT_demand_elec_to_real_slice' : 'flt_Energy_{GT,GT,demand,elec-to_real,slice}',
            'str_key_flt_Energy_GT_demand_H2_elec_to_real_slice' : 'flt_Energy_{GT,GT,demand,H2,elec-to_real,slice}',
            'str_key_flt_Energy_GT_demand_NH3_elec_to_real_slice' : 'flt_Energy_{GT,GT,demand,NH3,elec-to_real,slice}',
            'str_key_flt_Energy_GT_demand_CH4_elec_to_real_slice' : 'flt_Energy_{GT,GT,demand,CH4,elec-to_real,slice}',
            ## 给BESS
            'str_key_flt_Energy_GT_BESS_elec_to_avail_slice' : 'flt_Energy_{GT,GT,BESS,elec-to_avail,slice}',
            'str_key_flt_Energy_GT_BESS_elec_to_real_slice' : 'flt_Energy_{GT,GT,BESS,elec-to_real,slice}',
            'str_key_flt_Energy_GT_BESS_H2_elec_to_real_slice' : 'flt_Energy_{GT,GT,BESS,H2,elec-to_real,slice}',
            'str_key_flt_Energy_GT_BESS_NH3_elec_to_real_slice' : 'flt_Energy_{GT,GT,BESS,NH3,elec-to_real,slice}',
            'str_key_flt_Energy_GT_BESS_CH4_elec_to_real_slice' : 'flt_Energy_{GT,GT,BESS,CH4,elec-to_real,slice}',
            ## 给H2的ELY
            'str_key_flt_Energy_GT_ELY_elec_to_avail_slice' : 'flt_Energy_{GT,GT,ELY,elec-to_avail,slice}',
            'str_key_flt_Energy_GT_ELY_elec_to_real_slice' : 'flt_Energy_{GT,GT,ELY,elec-to_real,slice}',
            'str_key_flt_Energy_GT_ELY_H2_elec_to_real_slice' : 'flt_Energy_{GT,GT,ELY,H2,elec-to_real,slice}',
            'str_key_flt_Energy_GT_ELY_NH3_elec_to_real_slice' : 'flt_Energy_{GT,GT,ELY,NH3,elec-to_real,slice}',
            'str_key_flt_Energy_GT_ELY_CH4_elec_to_real_slice' : 'flt_Energy_{GT,GT,ELY,CH4,elec-to_real,slice}',
            ## 给EB
            'str_key_flt_Energy_GT_EB_elec_to_avail_slice' : 'flt_Energy_{GT,GT,EB,elec-to_avail,slice}',
            'str_key_flt_Energy_GT_EB_elec_to_real_slice' : 'flt_Energy_{GT,GT,EB,elec-to_real,slice}',
            'str_key_flt_Energy_GT_EB_H2_elec_to_real_slice' : 'flt_Energy_{GT,GT,EB,H2,elec-to_real,slice}',
            'str_key_flt_Energy_GT_EB_NH3_elec_to_real_slice' : 'flt_Energy_{GT,GT,EB,NH3,elec-to_real,slice}',
            'str_key_flt_Energy_GT_EB_CH4_elec_to_real_slice' : 'flt_Energy_{GT,GT,EB,CH4,elec-to_real,slice}',
            ## 给浪费
            'str_key_flt_Energy_GT_waste_elec_to_real_slice' : 'flt_Energy_{GT,GT,waste,elec-to_real,slice}',
            'str_key_flt_Energy_GT_waste_H2_elec_to_real_slice' : 'flt_Energy_{GT,GT,waste,H2,elec-to_real,slice}',
            'str_key_flt_Energy_GT_waste_NH3_elec_to_real_slice' : 'flt_Energy_{GT,GT,waste,NH3,elec-to_real,slice}',
            'str_key_flt_Energy_GT_waste_CH4_elec_to_real_slice' : 'flt_Energy_{GT,GT,waste,CH4,elec-to_real,slice}',
            # 能量输入整合
            'str_key_flt_Energy_GT_Fuel_fuel_consume_slice' : 'flt_Energy_{GT,GT,Fuel,fuel-consume,slice}',
            'str_key_flt_Energy_GT_Fuel_H2_from_real_slice' : 'flt_Energy_{GT,GT,Fuel,H2-from_real,slice}',
            'str_key_flt_Energy_GT_Fuel_NH3_from_real_slice' : 'flt_Energy_{GT,GT,Fuel,NH3-from_real,slice}',
            'str_key_flt_Energy_GT_Fuel_CH4_from_real_slice' : 'flt_Energy_{GT,GT,Fuel,CH4-from_real,slice}',
            # output输出整合
            'str_key_flt_Energy_GT_elec_output_slice' : 'flt_Energy_{GT,GT,elec-output,slice}',
            'str_key_flt_Energy_GT_H2_elec_output_slice' : 'flt_Energy_{GT,GT,H2,elec-output,slice}',
            'str_key_flt_Energy_GT_NH3_elec_output_slice' : 'flt_Energy_{GT,GT,NH3,elec-output,slice}',
            'str_key_flt_Energy_GT_CH4_elec_output_slice' : 'flt_Energy_{GT,GT,CH4,elec-output,slice}',
            # 能量损失
            'str_key_flt_Energy_GT_GT_loss_slice' : 'flt_Energy_{GT,GT,loss,slice}',
            'str_key_flt_Energy_GT_GT_H2_loss_slice' : 'flt_Energy_{GT,GT,H2,loss,slice}',
            'str_key_flt_Energy_GT_GT_NH3_loss_slice' : 'flt_Energy_{GT,GT,NH3,loss,slice}',
            'str_key_flt_Energy_GT_GT_CH4_loss_slice' : 'flt_Energy_{GT,GT,CH4,loss,slice}',
            # 开关机布尔
            'str_key_bol_On_GT_Online_slice' : 'bol_On_{GT,GT,Online,slice}',
            'str_key_bol_SwitchOn_GT_Online_slice' : 'bol_SwitchOn_{GT,GT,Online,slice}',
            'str_key_bol_SwitchFuel_GT_Online_slice' : 'bol_SwitchFuel_{GT,GT,Online,slice}',
            ## H2
            'str_key_bol_On_GT_H2_Online_slice' : 'bol_On_{GT,GT,H2,Online,slice}',
            'str_key_bol_SwitchOn_GT_H2_Online_slice' : 'bol_SwitchOn_{GT,GT,H2,Online,slice}',
            'str_key_bol_SwitchFuel_GT_H2_Online_slice' : 'bol_SwitchFuel_{GT,GT,H2,Online,slice}',
            ## NH3
            'str_key_bol_On_GT_NH3_Online_slice' : 'bol_On_{GT,GT,NH3,Online,slice}',
            'str_key_bol_SwitchOn_GT_NH3_Online_slice' : 'bol_SwitchOn_{GT,GT,NH3,Online,slice}',
            'str_key_bol_SwitchFuel_GT_NH3_Online_slice' : 'bol_SwitchFuel_{GT,GT,NH3,Online,slice}',
            ## CH4
            'str_key_bol_On_GT_CH4_Online_slice' : 'bol_On_{GT,GT,CH4,Online,slice}',
            'str_key_bol_SwitchOn_GT_CH4_Online_slice' : 'bol_SwitchOn_{GT,GT,CH4,Online,slice}',
            'str_key_bol_SwitchFuel_GT_CH4_Online_slice' : 'bol_SwitchFuel_{GT,GT,CH4,Online,slice}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_gt_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_pg(self,
        dic_name_col=None
    ):
        """初始化Power Grid列名字典
        """
        # 默认
        str_name_domain = 'PG'
        dic_name_col_pg_default = {
            # 功率
            'str_key_flt_Power_PG_grid_elec_output_slice' : 'flt_Power_{PG,grid,elec-output,slice}',
            'str_key_flt_Power_PG_grid_demand_elec_to_real_slice' : 'flt_Power_{PG,grid,demand,elec-to_real,slice}',
            'str_key_flt_Power_PG_grid_EB_elec_to_avail_slice' : 'flt_Power_{PG,grid,EB,elec-to_avail,slice}',
            'str_key_flt_Power_PG_grid_EB_elec_to_real_slice' : 'flt_Power_{PG,grid,EB,elec-to_real,slice}',
            # 能量
            'str_key_flt_Energy_PG_grid_elec_output_slice' : 'flt_Energy_{PG,grid,elec-output,slice}',
            'str_key_flt_Energy_PG_grid_demand_elec_to_real_slice' : 'flt_Energy_{PG,grid,demand,elec-to_real,slice}',
            'str_key_flt_Energy_PG_grid_EB_elec_to_avail_slice' : 'flt_Energy_{PG,grid,EB,elec-to_avail,slice}',
            'str_key_flt_Energy_PG_grid_EB_elec_to_real_slice' : 'flt_Energy_{PG,grid,EB,elec-to_real,slice}',
            # 电网需量按月累计
            # 'str_key_flt_Capacity_PG_grid_max_power_month_accum' : 'flt_Capacity_{PG,grid,max-power,month,accum}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_pg_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_bess(self,
        dic_name_col=None
    ):
        """初始化BESS列名字典

        """
        # 默认
        str_name_domain = 'BESS'
        dic_name_col_bess_default = {
            # 电能量差
            'str_key_flt_Power_BESS_batt_ext_elec_PN_slice' : 'flt_Power_{BESS,batt,ext,elec-PN,slice}', 
            # 电功率入
            'str_key_flt_Power_BESS_batt_charge_slice' : 'flt_Power_{BESS,batt,charge,slice}',
            # 电功率出
            'str_key_flt_Power_BESS_batt_discharge_slice' : 'flt_Power_{BESS,batt,discharge,slice}',
            'str_key_flt_Power_BESS_batt_demand_elec_to_real_slice' : 'flt_Power_{BESS,batt,demand,elec-to_real,slice}',
            'str_key_flt_Power_BESS_batt_EB_elec_to_avail_slice' : 'flt_Power_{BESS,batt,EB,elec-to_avail,slice}',
            'str_key_flt_Power_BESS_batt_EB_elec_to_real_slice' : 'flt_Power_{BESS,batt,EB,elec-to_real,slice}',
            # 储能量
            'str_key_flt_Energy_BESS_batt_reserves_slice' : 'flt_Energy_{BESS,batt,reserves,slice}',
            # 电能量差
            'str_key_flt_Energy_BESS_batt_ext_elec_PN_slice' : 'flt_Energy_{BESS,batt,ext,elec-PN,slice}',
            # 电能量入
            'str_key_flt_Energy_BESS_batt_charge_slice' : 'flt_Energy_{BESS,batt,charge,slice}',
            'str_key_flt_Energy_BESS_batt_WTPV_elec_from_slice' : 'flt_Energy_{BESS,batt,WTPV,elec-from,slice}',
            'str_key_flt_Energy_BESS_batt_GT_elec_from_slice' : 'flt_Energy_{BESS,batt,GT,elec-from,slice}',
            'str_key_flt_Energy_BESS_batt_GT_H2_elec_from_slice' : 'flt_Energy_{BESS,batt,GT,H2,elec-from,slice}',
            'str_key_flt_Energy_BESS_batt_GT_NH3_elec_from_slice' : 'flt_Energy_{BESS,batt,GT,NH3,elec-from,slice}',
            'str_key_flt_Energy_BESS_batt_GT_CH4_elec_from_slice' : 'flt_Energy_{BESS,batt,GT,CH4,elec-from,slice}',
            # 电能量出
            'str_key_flt_Energy_BESS_batt_discharge_slice' : 'flt_Energy_{BESS,batt,discharge,slice}',
            'str_key_flt_Energy_BESS_batt_demand_elec_to_real_slice' : 'flt_Energy_{BESS,batt,demand,elec-to_real,slice}',
            'str_key_flt_Energy_BESS_batt_EB_elec_to_avail_slice' : 'flt_Energy_{BESS,batt,EB,elec-to_avail,slice}',
            'str_key_flt_Energy_BESS_batt_EB_elec_to_real_slice' : 'flt_Energy_{BESS,batt,EB,elec-to_real,slice}',
            # 能量损耗
            'str_key_flt_Energy_BESS_batt_loss_slice' : 'flt_Energy_{BESS,batt,loss,slice}',
            # 开关机布尔
            'str_key_bol_SwitchOn_BESS_batt_charge_slice' : 'bol_SwitchOn_{BESS,batt,charge,slice}',
            'str_key_bol_SwitchOn_BESS_batt_discharge_slice' : 'bol_SwitchOn_{BESS,batt,discharge,slice}',
        }

        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_bess_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_h2(self,
        dic_name_col=None
    ):
        """初始化H2列名字典

        """
        # 默认
        str_name_domain = 'H2'
        dic_name_col_h2_default = {
            # Fuel质量出
            'str_key_flt_Mass_H2_Fuel_GT_H2_to_real_slice' : 'flt_Mass_{H2,Fuel,GT,H2-to_real,slice}',
            # Fuel质量入, 注意这里缺少从燃机来的电力部分
            'str_key_flt_Mass_H2_ELY_Fuel_WTPV_H2_from_real_slice' : 'flt_Mass_{H2,ELY,Fuel,WTPV,H2-from_real,slice}',
            # Fuel质量差
            'str_key_flt_Mass_H2_H2Tank_Fuel_diff_slice' : 'flt_Mass_{H2,H2Tank,Fuel,diff,slice}',
            # Fuel质量浪费
            'str_key_flt_Mass_H2_Fuel_waste_H2_to_real_slice' : 'flt_Mass_{H2,Fuel,waste,H2-to_real,slice}',
            # FUEL功率入
            'str_key_flt_Power_H2_ELY_WTPV_elec_from_slice' : 'flt_Power_{H2,ELY,WTPV,elec-from,slice}',
            'str_key_flt_Power_H2_ELY_GT_elec_from_slice' : 'flt_Power_{H2,ELY,GT,elec-from,slice}',
            # 储量
            'str_key_flt_Mass_H2_H2Tank_Fuel_reserves_slice' : 'flt_Mass_{H2,H2Tank,Fuel,reserves,slice}',
            'str_key_flt_Energy_H2_H2Tank_Fuel_reserves_slice' : 'flt_Energy_{H2,H2Tank,Fuel,reserves,slice}',
            # 其他
            'str_key_flt_Temp_H2_H2Tank_K_slice' : 'flt_Temp_{H2,H2Tank,K,slice}',
            'str_key_flt_Effi_H2_ELY_slice' : 'flt_Effi_{H2,ELY,slice}',
            # Fuel能量出
            'str_key_flt_Energy_H2_Fuel_GT_H2_to_real_slice' : 'flt_Energy_{H2,Fuel,GT,H2-to_real,slice}',
            # Fuel能量入
            'str_key_flt_Energy_H2_ELY_Fuel_produce_slice' : 'flt_Energy_{H2,ELY,Fuel,produce,slice}',
            'str_key_flt_Energy_H2_ELY_Fuel_WTPV_H2_from_real_slice' : 'flt_Energy_{H2,ELY,Fuel,WTPV,H2-from_real,slice}',
            'str_key_flt_Energy_H2_ELY_Fuel_GT_H2_from_real_slice' : 'flt_Energy_{H2,ELY,Fuel,GT,H2-from_real,slice}',
            # Fuel能量差
            'str_key_flt_Energy_H2_H2Tank_Fuel_diff_slice' : 'flt_Energy_{H2,H2Tank,Fuel,diff,slice}',
            # Fuel 质量浪费
            'str_key_flt_Energy_H2_Fuel_waste_H2_to_real_slice' : 'flt_Energy_{H2,Fuel,waste,H2-to_real,slice}',
            # ELY能量入
            'str_key_flt_Energy_H2_ELY_WTPV_elec_from_slice' : 'flt_Energy_{H2,ELY,WTPV,elec-from,slice}',
            'str_key_flt_Energy_H2_ELY_GT_elec_from_slice' : 'flt_Energy_{H2,ELY,GT,elec-from,slice}',
            # 能量整合
            'str_key_flt_Energy_H2_ELY_elec_consume_slice' : 'flt_Energy_{H2,ELY,elec-consume,slice}',
            'str_key_flt_Energy_H2_Comp_elec_consume_slice' : 'flt_Energy_{H2,Comp,elec-consume,slice}',
            # 能量损失
            'str_key_flt_Energy_H2_H2_loss_slice' : 'flt_Energy_{H2,H2,loss,slice}',
            'str_key_flt_Energy_H2_ELY_loss_slice' : 'flt_Energy_{H2,ELY,loss,slice}',
            # H2 开始时刻
            ## H2 制氢 开始时刻
            'str_key_bol_On_H2_ELY_H2_produce_slice' : 'bol_On_{H2,ELY,H2-produce,slice}',
            'str_key_bol_SwitchOn_H2_ELY_H2_produce_slice' : 'bol_SwitchOn_{H2,ELY,H2-produce,slice}',
            ## H2 用氢 开始时刻
            'str_key_bol_On_H2_ELY_H2_consume_slice' : 'bol_On_{H2,GT,H2-consume,slice}',
            'str_key_bol_SwitchOn_H2_ELY_H2_consume_slice' : 'bol_SwitchOn_{H2,ELY,H2-consume,slice}',
        }

        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_h2_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_ch4(self,
        dic_name_col=None
    ):
        """初始化CH4天然气列名字典

        """
        # 默认
        str_name_domain = 'CH4'
        dic_name_col_ch4_default = {
            # 质量差
            'str_key_flt_Mass_CH4_CH4Tank_Fuel_diff_slice' : 'flt_Mass_{CH4,CH4Tank,Fuel,diff,slice}',
            # 储量
            'str_key_flt_Mass_CH4_CH4Tank_Fuel_reserves_slice' : 'flt_Mass_{CH4,CH4Tank,Fuel,reserves,slice}',
            'str_key_flt_Energy_CH4_CH4Tank_Fuel_reserves_slice' : 'flt_Energy_{CH4,CH4Tank,Fuel,reserves,slice}',
            # 其他
            'str_key_flt_Temp_CH4_CH4Tank_K_slice' : 'flt_Temp_{CH4,CH4Tank,K,slice}',
            # 能量差
            'str_key_flt_Energy_CH4_CH4Tank_Fuel_diff_slice' : 'flt_Energy_{CH4,CH4Tank,Fuel,diff,slice}',
            # Fuel能量出
            'str_key_flt_Energy_CH4_Fuel_GT_CH4_to_real_slice' : 'flt_Energy_{CH4,Fuel,GT,CH4-to_real,slice}',
        }

        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_ch4_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_nh3(self,
        dic_name_col=None
    ):
        """初始化NH3列名字典

        """
        # 默认
        str_name_domain = 'NH3'
        dic_name_col_nh3_default = {
            # Fuel质量差
            'str_key_flt_Mass_NH3_NH3Tank_Fuel_diff_slice' : 'flt_Mass_{NH3,NH3Tank,Fuel,diff,slice}',
            # Fuel储量
            'str_key_flt_Mass_NH3_NH3Tank_Fuel_reserves_slice' : 'flt_Mass_{NH3,NH3Tank,Fuel,reserves,slice}',
            'str_key_flt_Energy_NH3_NH3Tank_Fuel_reserves_slice' : 'flt_Energy_{NH3,NH3Tank,Fuel,reserves,slice}',
            # 其他
            'str_key_flt_Temp_NH3_NH3Tank_K_slice' : 'flt_Temp_{NH3,NH3Tank,K,slice}',
            # Fuel能量差
            'str_key_flt_Energy_NH3_NH3Tank_Fuel_diff_slice' : 'flt_Energy_{NH3,NH3Tank,Fuel,diff,slice}', 
            # Fuel能量出
            'str_key_flt_Energy_NH3_Fuel_GT_NH3_to_real_slice' : 'flt_Energy_{NH3,Fuel,GT,NH3-to_real,slice}',
        }

        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_nh3_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_stm(self,
        dic_name_col=None
    ):
        """初始化steam列名字典
        """
        # 默认
        str_name_domain = 'STM'
        dic_name_col_stm_default = {
            # 功率: EB可以使用
            'str_key_flt_Power_STM_EB_elec_wanted_slice' : 'flt_Power_{STM,EB,elec-wanted,slice}',
            # 能量: EB可以使用
            'str_key_flt_Power_STM_EB_elec_wanted_slice' : 'flt_Power_{STM,EB,elec-wanted,slice}',
            # 能量EB - elec来源
            'str_key_flt_Energy_STM_EB_elec_consume_slice' : 'flt_Energy_{STM,EB,elec-consume,slice}',
            'str_key_flt_Energy_STM_EB_WTPV_elec_from_slice' : 'flt_Energy_{STM,EB,WTPV,elec-from,slice}',
            'str_key_flt_Energy_STM_EB_BESS_elec_from_slice' : 'flt_Energy_{STM,EB,BESS,elec-from,slice}',
            'str_key_flt_Energy_STM_EB_GT_elec_from_slice' : 'flt_Energy_{STM,EB,GT,elec-from,slice}',
            'str_key_flt_Energy_STM_EB_PG_elec_from_slice' : 'flt_Energy_{STM,EB,PG,elec-from,slice}',

            # 能量 - Steam消耗
            'str_key_flt_Energy_STM_STM_steam_consume_slice' : 'flt_Energy_{STM,STM,steam-consume,slice}',

            # 能量EB - 输出
            'str_key_flt_Energy_STM_EB_demand_steam_to_real_slice' : 'flt_Energy_{STM,EB,demand,steam-to_real,slice}',
            # 能量HRSG - 输出
            'str_key_flt_Energy_STM_HRSG_demand_steam_to_avail_slice' : 'flt_Energy_{STM,HRSG,demand,steam-to_avail,slice}',
            'str_key_flt_Energy_STM_HRSG_demand_steam_to_real_slice' : 'flt_Energy_{STM,HRSG,demand,steam-to_real,slice}',
            # 能量 HRSG - waste
            'str_key_flt_Energy_STM_HRSG_waste_steam_to_real_slice' : 'flt_Energy_{STM,HRSG,waste,steam-to_real,slice}',
            # 其他
            'str_key_flt_Ratio_STM_HRSG_GT_equiv_to_full_slice' : 'flt_Ratio_{STM,HRSG,GT,equiv-to_full,slice}',
        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_stm_default,
            dic_name_col_user = dic_name_col
        )
        pass

    def _init_dic_name_col_other(self,
        dic_name_col=None
    ):
        """初始化steam列名字典
        """
        # 默认
        str_name_domain = 'OTHER'
        dic_name_col_stm_default = {
            # 当燃机和风光重叠能量, 当燃机开时, 风光-> (充电池, 制氢, 弃电)的总和
            'str_key_flt_Energy_OTHER_WTPV_GT_overlap_slice' : 'flt_Energy_{OTHER,WTPV,GT,overlap,slice}',

        }
        # 更新
        self._update_domain_dict(
            str_name_domain = str_name_domain,
            dic_name_col_default = dic_name_col_stm_default,
            dic_name_col_user = dic_name_col
        )
        pass  

    def _update_domain_dict(self,
        str_name_domain:str,
        dic_name_col_default:Dict[str, str],
        dic_name_col_user:Dict[str, str],
    ):
        """更新领域列名字典

        Args:
            dic_name_col_domain: 领域列名字典，格式为 { "logical_name": "actual_column_name" }
        """
        # 读取扁平化全局列名字典
        dic_name_col_global = self.dic_name_col_global
        # 读取领域列名字典
        dic_name_col_domain = self.dic_name_col_domain
        # 检查default是否为None
        if dic_name_col_default is None or not isinstance(dic_name_col_default, dict):
            raise ValueError("dic_name_col_default 不能为None")
        # 检查Domain名字是否存在
        if str_name_domain not in dic_name_col_domain:
            dic_name_col_domain[str_name_domain] = {}
        dic_name_col_domain_single = dic_name_col_domain[str_name_domain]

        # 更新扁平化领域默认
        _update_key_from_other_dict(
            dic_update_to = dic_name_col_domain_single,
            dic_update_from = dic_name_col_default,
            bol_create_new_key=True,
            bol_ignore_new_key=False
        )
        # 更新扁平化领域用户提供的
        if dic_name_col_user is not None:
            _update_key_from_other_dict(
                dic_update_to =dic_name_col_domain_single,
                dic_update_from = dic_name_col_user,
                bol_create_new_key=False,
                bol_ignore_new_key=False
            )
        # 更新扁平化全局默认
        _update_key_from_other_dict(
            dic_update_to = dic_name_col_global,
            dic_update_from = dic_name_col_domain_single,
            bol_create_new_key=True,
            bol_ignore_new_key=False
        )
        pass

    def get_name_col(self,
        str_key_col : str,
        bol_must_have: bool = True
    ) -> str:
        """获取实际列名
        """
        if bol_must_have and str_key_col not in self.dic_name_col_global:
            raise KeyError(f"列名 '{str_key_col}' 在列名字典中未找到")
        return self.dic_name_col_global.get(str_key_col, None)
            
    def get_col(self,
        lf: pl.LazyFrame,
        col_keys: Optional[Union[str, List[str]]] = None,
        expr_filter: Optional[pl.Expr] = None
    ) -> pl.DataFrame:
        """查看当前 LazyFrame 状态（不执行操作）
        
        Returns:
            当前的 LazyFrame
        """
        # 通过输入的keys
        if isinstance(col_keys, str):
            col_keys = [col_keys]
        if col_keys is None:
            raise ValueError("请提供要查看的列的键列表")
        # filter
        if expr_filter is not None:
            lf = lf.filter(expr_filter)
        # 生成列名列表
        lst_name_col = [
            self.get_name_col(key) for key in col_keys
        ]
        lf = lf.select(lst_name_col)
        return lf.collect()