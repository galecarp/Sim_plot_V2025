#!/usr/bin/env python3

from typing import Tuple, Dict, Optional
import pyqtgraph as pg

from app.plotter.enums.modeenum import AlignmentMode, RangeMode
from app.plotter.enums.plotenum import SideAxis, IdxItemGridLayout
from app.plotter.enums.valueenum import UnitValue
from app.plotter.graphconfigs.axisconfig import AxisConfig

class PlotAxisManager:
    """
    单个子图的多Y轴管理器

    Attributes:
        obj_plot (pg.PlotItem):
            关联的PyQtGraph PlotItem对象
        dic_axisconfig (Dict[str, AxisConfig]):
            本图的axis配置字典, key为每个axis的str_name_axis, value为AxisConfig对象
        dic_viewbox (Dict[str, pg.ViewBox]):
            axis对应的ViewBox字典, key为每个axis的str_name_axis, value为对应的ViewBox对象

    * QGraphicsGridLayout布局说明:
        行\列      0          1              2            3
        0    [标题区]    [标题区]        [标题区]      ...
        1    [空]       [顶部X轴]        [空]          ...
        2    [左Y轴]    [ViewBox]       [右Y轴1]      [右Y轴2]   ← 第2行
        3    [空]       [底部X轴]        [空]          ...
    """
    def __init__(self,
        obj_plot: pg.PlotItem
    ):
        self.str_name_axis_left = 'main'  # 主轴名称
        self.obj_plot : pg.PlotItem = obj_plot
        self.dic_axisconfig: Dict[str, AxisConfig] = {}
        self.dic_viewbox: Dict[str, pg.ViewBox] = {}
        # 初始化func_alignment
        self._init_dic_method_alignment()
        # 主轴使用plot自带的ViewBox
        self.viewbox_main = obj_plot.getViewBox()
        # 右侧y轴计数
        self.n_yaxis_right = 0
        # 添加默认主轴, 左侧
        self._init_yaxis_left(self.str_name_axis_left)
        # 连接主轴大小变化信号（只连接一次）
        self.viewbox_main.sigResized.connect(self._sync_viewbox_geometry)
        pass
        
    def _init_dic_method_alignment(self):
        """
        初始化对齐方法字典
        """
        self.dic_method_alignment = {
            AlignmentMode.ZERO: self._align_yaxis_at_zero,
            AlignmentMode.VALUE: self._align_yaxis_at_value,
            AlignmentMode.VALUESCALE: self._align_yaxis_at_value_w_scale,
        }
        pass

    def _init_yaxis_left(self,
        str_name_axis: str = 'main'
    ):
        """
        添加默认主轴
        """
        # 创建主轴配置
        axisconfig_main = AxisConfig(
            str_name_axis=str_name_axis,
            side_axis=SideAxis.LEFT,
            str_label='左Y轴',
            bol_is_prim_axis=True,
            viewbox=self.viewbox_main
        )
        # 加入字典
        self.dic_axisconfig[str_name_axis] = axisconfig_main
        self.dic_viewbox[str_name_axis] = self.viewbox_main
        pass

    # 对齐yaxis的方法
    def _calc_yaxis_range_align(
        flt_lb_range_tgt : float,
        flt_ub_range_tgt: float,
        flt_lb_range_src: Optional[float] = None,
        flt_ub_range_src: Optional[float] = None,
        flt_align_src: Optional[float] = None,
        flt_align_tgt: Optional[float] = None,
        flt_ratio_scale: Optional[float] = None,
        str_name_axis_src: Optional[str] = None,
        str_name_axis_tgt: Optional[str] = None,
        bol_raise_nonexist: bool = False,
    ) -> Tuple[float, float]:
        """
        计算对齐后的Y轴范围

        Args:
            flt_lb_range_tgt: 目标轴下限
            flt_ub_range_tgt: 目标轴上限
            flt_lb_range_src: 源轴下限
            flt_ub_range_src: 源轴上限
            flt_align_src: 源轴对齐值
            flt_align_tgt: 目标轴对齐值
            flt_ratio_scale: 源轴与目标轴的比例缩放
                即 源轴新span = 目标轴span * flt_ratio_scale

        """
        # 计算目标轴的span
        flt_span_range_tgt = flt_ub_range_tgt - flt_lb_range_tgt
        # 计算目标对齐值在tgt的span范围的相对位置
        flt_percentile_align_tgt = (flt_align_tgt - flt_lb_range_tgt) / flt_span_range_tgt
        # 计算源轴的span
        flt_span_range_src = flt_ub_range_src - flt_lb_range_src
        # 验证是否目标范围有问题
        if flt_span_range_tgt <= 0:
            if bol_raise_nonexist:
                raise ValueError(
                    f"Axis {str_name_axis_tgt} 目标轴范围无效"+\
                    f"(LB: {flt_lb_range_tgt}, UB: {flt_ub_range_tgt})"
                )  
            return None, None
        # 如果flt_ratio_scale有值, 则调整源轴span
        if flt_ratio_scale is not None:
            flt_span_range_src = flt_span_range_tgt * flt_ratio_scale
        # 按对齐位置, 计算源轴新范围
        flt_lb_range_new = flt_align_src - flt_percentile_align_tgt * flt_span_range_src
        flt_ub_range_new = flt_align_src + (1 - flt_percentile_align_tgt) * flt_span_range_src
        return flt_lb_range_new, flt_ub_range_new

    def _align_yaxis_at_zero(self,
        str_name_axis_src:str,
        str_name_axis_tgt:str,
        bol_raise_nonexist: bool = False,
        **kwargs
    ):
        """
        零点对齐: 当前y轴 和 目标轴在0的数值位置对齐

        """
        viewbox_tgt = self._get_axis_viewbox(
            str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist)
        viewbox_src = self._get_axis_viewbox(
            str_name_axis_src,
            bol_raise_nonexist=bol_raise_nonexist)
        # 获取目标轴的Y范围
        lst_range_yaxis_tgt = viewbox_tgt.viewRange()[1]
        flt_lb_range_tgt, flt_ub_range_tgt = lst_range_yaxis_tgt
        # 获取源轴的Y范围
        lst_range_yaxis_src = viewbox_src.viewRange()[1]
        flt_lb_range_src, flt_ub_range_src = lst_range_yaxis_src

        # 对齐计算
        flt_lb_range_new, flt_ub_range_new = PlotAxisManager._calc_yaxis_range_align(
            flt_lb_range_tgt =flt_lb_range_tgt,
            flt_ub_range_tgt=flt_ub_range_tgt,
            flt_lb_range_src=flt_lb_range_src,
            flt_ub_range_src=flt_ub_range_src,
            flt_align_src=0.0,
            flt_align_tgt=0.0,
            flt_ratio_scale=None,
            str_name_axis_src=str_name_axis_src,
            str_name_axis_tgt=str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist
        )
        # 应用调整
        viewbox_src.setYRange(flt_lb_range_new, flt_ub_range_new, padding=0)
        return
    
    def _align_yaxis_at_value(self,
        str_name_axis_src:str,
        str_name_axis_tgt:str,
        flt_align_src: float,
        flt_align_tgt: float,
        bol_raise_nonexist: bool = False,
        **kwargs
    ):
        """
        源和目标轴按config指定的值对齐

        源轴的span保持不变, 仅调整对齐位置
        """
        viewbox_tgt = self._get_axis_viewbox(
            str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist)
        viewbox_src = self._get_axis_viewbox(
            str_name_axis_src,
            bol_raise_nonexist=bol_raise_nonexist)
        # 获取目标轴的Y范围
        lst_range_yaxis_tgt = viewbox_tgt.viewRange()[1]
        flt_lb_range_tgt, flt_ub_range_tgt = lst_range_yaxis_tgt
        # 获取源轴的Y范围
        lst_range_yaxis_src = viewbox_src.viewRange()[1]
        flt_lb_range_src, flt_ub_range_src = lst_range_yaxis_src

        # 对齐计算
        flt_lb_range_new, flt_ub_range_new = PlotAxisManager._calc_yaxis_range_align(
            flt_lb_range_tgt =flt_lb_range_tgt,
            flt_ub_range_tgt=flt_ub_range_tgt,
            flt_lb_range_src=flt_lb_range_src,
            flt_ub_range_src=flt_ub_range_src,
            flt_align_src=flt_align_src,
            flt_align_tgt=flt_align_tgt,
            flt_ratio_scale=None,
            str_name_axis_src=str_name_axis_src,
            str_name_axis_tgt=str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist
        )
        # 应用调整
        viewbox_src.setYRange(flt_lb_range_new, flt_ub_range_new, padding=0)
        return True
    
    def _align_yaxis_at_value_w_scale(self,
        str_name_axis_src:str,
        str_name_axis_tgt:str,
        flt_align_src: float,
        flt_align_tgt: float,
        flt_ratio_scale: float=1.0,
        bol_raise_nonexist: bool = False,
        **kwargs
    ):
        """
        源和目标轴按config指定的值对齐, span按比例对比target的span调整

        """
        viewbox_tgt = self._get_axis_viewbox(
            str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist)
        viewbox_src = self._get_axis_viewbox(
            str_name_axis_src,
            bol_raise_nonexist=bol_raise_nonexist)
        # 获取目标轴的Y范围
        lst_range_yaxis_tgt = viewbox_tgt.viewRange()[1]
        flt_lb_range_tgt, flt_ub_range_tgt = lst_range_yaxis_tgt
        # 获取源轴的Y范围
        lst_range_yaxis_src = viewbox_src.viewRange()[1]
        flt_lb_range_src, flt_ub_range_src = lst_range_yaxis_src

        # 对齐计算
        flt_lb_range_new, flt_ub_range_new = PlotAxisManager._calc_yaxis_range_align(
            flt_lb_range_tgt =flt_lb_range_tgt,
            flt_ub_range_tgt=flt_ub_range_tgt,
            flt_lb_range_src=flt_lb_range_src,
            flt_ub_range_src=flt_ub_range_src,
            flt_align_src=flt_align_src,
            flt_align_tgt=flt_align_tgt,
            flt_ratio_scale=flt_ratio_scale,
            str_name_axis_src=str_name_axis_src,
            str_name_axis_tgt=str_name_axis_tgt,
            bol_raise_nonexist=bol_raise_nonexist
        )
        # 应用调整
        viewbox_src.setYRange(flt_lb_range_new, flt_ub_range_new, padding=0)
        return
    
    def _add_yaxis_right(self,
        axisconfig: AxisConfig
    ) -> pg.ViewBox:
        """添加新的Y轴
        """
        # 检查是否已存在
        if axisconfig.str_name_axis in self.dic_axisconfig:
            raise ValueError(f"Axis {axisconfig.str_name_axis} 已存在")
        # 左侧轴只能有一个且为主轴
        if axisconfig.side_axis == SideAxis.LEFT and not axisconfig.bol_is_prim_axis:
            raise ValueError("不支持多个左侧Y轴, 因为左轴为主轴")
        
        # 1.创建新的ViewBox
        viewbox_yaxis = self._add_viewbox(self.obj_plot)
        # 2.创建轴对象
        axisitem_yaxis = self._add_item_axis(
            axisconfig=axisconfig,
            viewbox=viewbox_yaxis
        )
        # 3.添加到Layout（右侧轴位置）
        self._add_yaxis_to_layout(
            obj_plot=self.obj_plot,
            axis_item=axisitem_yaxis
        )
        # 4.把y轴链接到X轴
        viewbox_yaxis.setXLink(self.viewbox_main)
        # 5.保存入配置
        axisconfig.viewbox = viewbox_yaxis
        axisconfig.axisitem = axisitem_yaxis
        # 6.加入manager的字典
        self.dic_axisconfig[axisconfig.str_name_axis] = axisconfig
        self.dic_viewbox[axisconfig.str_name_axis] = viewbox_yaxis
        return viewbox_yaxis
    
    @staticmethod
    def _add_viewbox(self) -> pg.ViewBox:
        """创建并添加新的ViewBox
        """
        obj_plot = self.obj_plot
        viewbox_axis = pg.ViewBox()
        ## 将ViewBox添加到PlotItem的场景中
        if obj_plot:
            obj_plot.scene().addItem(viewbox_axis)
        return viewbox_axis
    
    @staticmethod
    def _add_item_yaxis(self,
        axisconfig: AxisConfig,
    ) -> pg.AxisItem:
        """
        创建并添加新的AxisItem
        """
        viewbox = self.viewbox_main
        # 创建AxisItem
        axis_item = pg.AxisItem(
            orientation=SideAxis.RIGHT.value)
        # 设置标签和颜色
        axis_item.setLabel(
            text=axisconfig.str_label,
            units=axisconfig.unit_value.value,
            color=axisconfig.color
        )
        # 将AxisItem添加到布局
        if viewbox:
            axis_item.linkToView(viewbox)
        return axis_item
    
    def _add_yaxis_to_layout(self,
        obj_plot: pg.PlotItem,
        axisitem: pg.AxisItem,
        idx_row_viewbox: int = 2
    ):
        """将AxisItem添加到PlotItem的布局中

        layout列: 0=左轴, 1=绘图区, 2=第一个右轴, 3=第二个右轴...
        layout行: 0=标题区, 1=顶部X轴, 2=ViewBox所在行, 3=底部X轴
        """
        # 计算添加yaxis在layout布局的位置
        idx_item_layout = IdxItemGridLayout.PLOTITEM.value + self.n_yaxis_right
        obj_plot.layout.addItem(
            axisitem, idx_row_viewbox, idx_item_layout)
        # 更新右轴计数
        self.n_yaxis_right += 1
        return

    def _sync_viewbox_geometry(self):
        """
        同步所有ViewBox的几何形状
        以匹配主ViewBox的几何形状
        """
        # 获取主ViewBox的边界矩形
        geometry = self.viewbox_main.sceneBoundingRect()
        # 更新其他ViewBox的几何形状, 主轴在信号源中已更新
        for str_name_axis, viewbox in self.dic_viewbox.items():
            if str_name_axis != self.str_name_axis_left:
                viewbox.setGeometry(geometry)
        return
    
    def _del_yaxis(self,
        str_name_axis: str,
        bol_raise_nonexist: bool = False
    ):
        """移除Y轴
        """
        # 不能删除主轴
        if str_name_axis == self.str_name_axis_left:
            raise ValueError("不能删除主轴")
        # 检查是否存在
        if str_name_axis not in self.dic_axisconfig:
            if bol_raise_nonexist:
                raise ValueError(f"Axis {str_name_axis} 不存在")
            return
        # 1.获取axisconfig    
        axisconfig_del = self.dic_axisconfig[str_name_axis]
        # 2.移除ViewBox和AxisItem
        if axisconfig_del.viewbox:
            self.obj_plot.scene().removeItem(axisconfig_del.viewbox)
        if axisconfig_del.axis_item:
            self.obj_plot.layout.removeItem(axisconfig_del.axisitem)
        # 3.从manager中删除配置
        del self.dic_axisconfig[str_name_axis]
        del self.dic_viewbox[str_name_axis]
        # 4.重建右轴布局
        self._reset_layout_yaxis()
        return
    
    def _reset_layout_yaxis(self):
        """
        重建在layout中的右侧轴布局
        """
        # 从layout中清除所有右轴item
        for str_name_axis, axisconfig in list(self.dic_axisconfig.items()):
            if axisconfig.side_axis == SideAxis.RIGHT and axisconfig.axisitem:
                self.obj_plot.layout.removeItem(axisconfig.axisitem)
        
        # 向layout中重新添加所有右轴
        self.n_yaxis_right = 0
        for str_name_axis, axisconfig in list(self.dic_axisconfig.items()):
            if axisconfig.side_axis == SideAxis.RIGHT and axisconfig.axisitem:
                # 添加axis到布局
                self._add_yaxis_to_layout(
                    obj_plot=self.obj_plot,
                    axis_item=axisconfig.axisitem
                )
        return

    def _apply_yaxis_range(self,
        str_name_axis: str,
        bol_raise_nonexist: bool = False
    ):
        """
        应用y轴的范围设定
        """
        # 获取轴配置
        axisconfig : AxisConfig = self._get_axisconfig(
            str_name_axis=str_name_axis,
            bol_raise_nonexist=bol_raise_nonexist
        )
        if not axisconfig.viewbox:
            if bol_raise_nonexist:
                raise ValueError(f"Axis {str_name_axis} 无ViewBox")
            return
        # 应用范围设置
        viewbox_axis : pg.ViewBox = axisconfig.viewbox
        if axisconfig.mode_range == RangeMode.MANUAL:
            ## 手动范围
            viewbox_axis.setYRange(
                min=axisconfig.lb_range,
                max=axisconfig.ub_range,
                padding=0
            )
        else:
            # 自动范围
            viewbox_axis.enableAutoRange(axis=pg.ViewBox.YAxis)
        return
    
    def _apply_yaxis_alignment(self,
        str_name_axis: str,
        bol_raise_nonexist: bool = False
    ):
        """
        应用y轴对齐设定
        """
        # 获取轴配置
        axisconfig_src : AxisConfig = self._get_axisconfig(
            str_name_axis=str_name_axis,
            bol_raise_nonexist=bol_raise_nonexist
        )
        # 跳过alignment mode为NONE的情况
        if axisconfig_src.mode_align == AlignmentMode.NONE:
            return
        # 检查对齐目标轴是否存在
        str_name_axis_align = axisconfig_src.str_name_axis_align
        if not str_name_axis_align or str_name_axis_align not in self.dic_axisconfig:
            if bol_raise_nonexist:
                raise ValueError(f"Axis {str_name_axis} 对齐目标轴不存在")
            return
        
        # 获取源轴和目标轴的ViewBox
        str_name_axis_src = str_name_axis
        str_name_axis_tgt = str_name_axis_align
        method_align = self._get_method_align(
            axisconfig_src.mode_align,
            bol_raise_nonexist=bol_raise_nonexist
        )
        # 调用对齐方法调整源轴
        if method_align:
            method_align(
                str_name_axis_src=str_name_axis_src,
                str_name_axis_tgt=str_name_axis_tgt,
                flt_align_src=axisconfig_src.flt_align_src,
                flt_align_tgt=axisconfig_src.flt_align_tgt,
                flt_ratio_align=axisconfig_src.flt_ratio_scale
            )
        return
 
    # 内部getter
    def _get_method_align(self,
        mode_align: AlignmentMode,
        bol_raise_nonexist: bool = False
    ):
        """
        获取对齐方法
        """
        method_align = self.dic_method_alignment.get(mode_align)
        if not method_align and bol_raise_nonexist:
            raise ValueError(f"对齐模式 {mode_align} 不存在对应的方法")
        return method_align

    def _get_axisconfig(self,
        str_name_axis: str,
        bol_raise_nonexist: bool = False
    ) -> Optional[AxisConfig]:
        """
        获取轴配置
        """
        axisconfig = self.dic_axisconfig.get(str_name_axis)
        if not axisconfig and bol_raise_nonexist:
            raise ValueError(f"Axis {str_name_axis} 不存在")
        return axisconfig
    
    def _get_axis_viewbox(self,
        str_name_axis: str,
        bol_raise_nonexist: bool = False
    ) -> Optional[pg.ViewBox]:
        """
        获取轴ViewBox
        """
        viewbox = self.dic_viewbox.get(str_name_axis)
        if not viewbox and bol_raise_nonexist:
            raise ValueError(f"Axis {str_name_axis} 不存在")
        return viewbox

    # getters
    def get_axis(self, str_name_axis: str) -> Optional[AxisConfig]:
        """获取轴配置"""
        return self.dic_axisconfig.get(str_name_axis)
    
    def get_viewbox(self, str_name_axis: str) -> Optional[pg.ViewBox]:
        """获取ViewBox"""
        return self.dic_viewbox.get(str_name_axis)
