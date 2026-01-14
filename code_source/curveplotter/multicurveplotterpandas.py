#!/usr/bin/python3

import sys
import pandas as pd
import numpy as np
from typing import Optional, Any, List, Dict, Tuple


import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

class MulticurvePlotterPandas:
    """
    Pandas DataFrame 多曲线绘图工具类
    """
    def __init__(self,
        df : pd.DataFrame,
        str_title : str = "Price Chart",
        tup_size : Tuple[int] = (1400, 800)
    ):
        self.df = df
        self.app : QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
        self.win : pg.GraphicsLayoutWidget = pg.GraphicsLayoutWidget(show=True, title=str_title)
        self.win.resize(*tup_size)
        self.plot : Optional[pg.PlotItem] = None
        pass
        
    def plot_columns(self,
        x_column:Optional[str]=None,
        y_columns:Optional[List[str]]=None, 
        xlabel='Index',
        ylabel='Price (€/MWh)',
        dic_colors:Optional[Dict[str, Any]]=None,
        dic_name_col_plot:Optional[Dict[str, str]]=None
    ):
        """
        绘制指定列
        
        参数:
            x_column: X轴列名
            y_columns: Y轴列名列表
            xlabel: X轴标签
            ylabel: Y轴标签
        """
        # 创建绘图区域
        self.plot = self.win.addPlot()
        
        # 准备数据
        if x_column == 'index' or x_column == 'Index':
            x_data = self.df.index.values
        else:
            x_data = self._prepare_x_data(x_column)
        y_columns = self._prepare_y_columns(y_columns, x_column)
        
        # 设置标签和网格
        self.plot.setLabel('left', ylabel)
        self.plot.setLabel('bottom', xlabel)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.addLegend()
        
        # 绘制曲线
        self._plot_curves(
            x_data=x_data,
            y_columns=y_columns,
            dic_colors=dic_colors,
            dic_name_col_plot=dic_name_col_plot
        )
        
        # 添加交互功能
        self._add_crosshair()
        
        return self
    
    def _prepare_x_data(self,
        x_column:Optional[str]=None
    ) -> np.ndarray:
        """准备X轴数据
        """
        if x_column and x_column in self.df.columns:
            x_data = self.df[x_column].values
            # 处理日期类型
            if pd.api.types.is_datetime64_any_dtype(self.df[x_column]):
                x_data = pd.to_numeric(self.df[x_column]) / 10**9
            return x_data
        else:
            return np.arange(len(self.df))
    
    def _prepare_y_columns(self,
        y_columns:Optional[List[str]]=None,
        x_column:Optional[str]=None
    ) -> List[str]:
        """准备Y轴列名"""
        if y_columns is None:
            y_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if x_column in y_columns:
                y_columns.remove(x_column)
        return y_columns
    
    def _plot_curves(self,
        x_data : np.ndarray,
        y_columns: List[str],
        dic_colors:Optional[Dict[str, Any]]=None,
        dic_name_col_plot:Optional[Dict[str, str]]=None
    ):
        """绘制所有曲线
        """
        for idx_col, str_name_col in enumerate(y_columns):
            # 获取颜色和名称
            color_col_plot = dic_colors.get(str_name_col, pg.intColor(idx_col)) if dic_colors else pg.intColor(idx_col)
            str_name_col_plot = dic_name_col_plot.get(str_name_col, str_name_col) if dic_name_col_plot else str_name_col
            # 绘制曲线
            pen = pg.mkPen(color=color_col_plot, width=2)
            self.plot.plot(
                x_data, 
                self.df[str_name_col].values, 
                pen=pen, 
                name=str_name_col_plot
            )
        return
    
    def _add_crosshair(self):
        """添加十字光标"""
        vLine = pg.InfiniteLine(
            angle=90,
            movable=False, 
            pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)
        )
        hLine = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine)
        )
        self.plot.addItem(vLine, ignoreBounds=True)
        self.plot.addItem(hLine, ignoreBounds=True)
        
        # 创建文本标签
        label = pg.TextItem(anchor=(0, 1))
        self.plot.addItem(label)
        
        def mouseMoved(evt):
            pos = evt
            if self.plot.sceneBoundingRect().contains(pos):
                mousePoint = self.plot.vb.mapSceneToView(pos)
                vLine.setPos(mousePoint.x())
                hLine.setPos(mousePoint.y())
                label.setText(f'x={mousePoint.x():.2f}, y={mousePoint.y():.2f}')
                label.setPos(mousePoint)
        
        proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved, 
            rateLimit=60, 
            slot=mouseMoved
        )
    
    def show(self):
        """显示图表并运行应用"""
        sys.exit(self.app.exec())


    # =============== 便捷函数 ===============
    @staticmethod
    def plot_dataframe(
        df : pd.DataFrame,
        x_col:str=None,
        y_cols:List[str]=None,
        str_title="Multi-Line Chart"
    ):
        """
        一行代码绘制 DataFrame
        
        使用示例:
            # 绘制所有数值列
            plot_dataframe(df_price_NG_MWh_LHV)
            
            # 指定列
            plot_dataframe(df_price_NG_MWh_LHV, 
                        y_cols=['Price_A', 'Price_B', 'Price_C'])
            
            # 指定X轴和Y轴
            plot_dataframe(df_price_NG_MWh_LHV, 
                        x_col='Date',
                        y_cols=['Price_A', 'Price_B'])
        """
        plotter = MulticurvePlotterPandas(
            df=df,
            str_title=str_title)
        plotter.plot_columns(
            x_column=x_col,
            y_columns=y_cols
        )
        plotter.show()
        return




