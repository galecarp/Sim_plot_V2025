#!/usr/bin/env python3
"""Multi-curve plotter package for polars data visualization."""

from .viewer import MultiCurvePlotterWidget
from .plotaxismanager import PlotAxisManager
from .translation import StaticTranslationMixin, ColumnNameTranslator

__all__ = [
    'MultiCurvePlotterWidget',
    'PlotAxisManager',
    'StaticTranslationMixin',
    'ColumnNameTranslator',
]
