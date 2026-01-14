import asyncio
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QMainWindow, QFileDialog
from httpx import HTTPError
from qasync import asyncSlot

import app.resources.resource  # type: ignore
from app.builtin.update_widget import UpdateWidget
from app.resources.main_window_ui import Ui_MainWindow
from qdarktheme import setup_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.click_push_button)

        # ThemeManager.instance().setup_theme("auto")
        self.ui.themeComboBox.addItem(self.tr("Auto"), "auto")
        self.ui.themeComboBox.addItem(self.tr("Light"), "light")
        self.ui.themeComboBox.addItem(self.tr("Dark"), "dark")
        self.ui.themeComboBox.currentIndexChanged.connect(self.change_theme)
        self.ui.themeComboBox.setCurrentIndex(0)
        self.change_theme(0)

        # 检查plotter模块是否可用
        self._plotter_available = self._check_plotter_availability()
        
        # 添加打开Plotter的按钮
        if hasattr(self.ui, 'btnOpenPlotter'):
            self.ui.btnOpenPlotter.clicked.connect(self.open_plotter)
            # 如果plotter不可用，禁用按钮
            if not self._plotter_available:
                self.ui.btnOpenPlotter.setEnabled(False)
                self.ui.btnOpenPlotter.setToolTip(self.tr("数据可视化模块不可用"))

        self.setWindowTitle(self.tr("MainWindow"))
        self.setWindowIcon(QIcon(":/logo.png"))
        
        # 保存plotter窗口引用
        self.plotter_window = None
    
    def _check_plotter_availability(self) -> bool:
        """检查plotter模块及其依赖是否可用"""
        try:
            import polars as pl
            from app.plotter import MultiCurvePlotterWidget, ColumnNameTranslator
            import pyqtgraph as pg
            # 检查code_source模块
            from code_source.polars_toolkits.datetime_toolkits.utilpolarsdatetime import get_timestamp_min_max
            return True
        except ImportError as e:
            print(f"警告: Plotter模块不可用 - {e}")
            return False

    async def async_init(self):
        # from app.builtin.github_updater import GithubUpdater
        from app.builtin.gitlab_updater import GitlabUpdater

        updater = GitlabUpdater()
        if os.getenv("DEBUG", "0") == "1":
            # Debug mode
            pass
        else:
            # Production mode
            await self.check_update(updater)

    async def check_update(self, updater):
        if not updater.is_enable:
            return
        if not updater.is_updated:
            try:
                await updater.fetch()
                if updater.check_for_update():
                    update_widget = UpdateWidget(self, updater)
                    await update_widget.async_show()
                    if update_widget.need_restart:
                        updater.apply_update()
                        self.close()
            except HTTPError:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Failed to check for updates"),
                )
            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("No update files found"),
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Excepted unknown error: {}").format(str(e)),
                )
        else:
            QMessageBox.information(
                self,
                self.tr("Info"),
                self.tr("Update completed"),
            )

    @asyncSlot()
    async def click_push_button(self):
        async def async_task():
            await asyncio.sleep(1)
            QMessageBox.information(self, self.tr("Hello"), self.tr("Hello World!"))

        self.ui.pushButton.setEnabled(False)
        await async_task()
        self.ui.pushButton.setEnabled(True)

    def change_theme(self, index):
        theme = self.ui.themeComboBox.itemData(index)
        setup_theme(theme)

    def open_plotter(self):
        """打开数据可视化窗口"""
        try:
            import polars as pl
            from app.plotter import MultiCurvePlotterWidget, ColumnNameTranslator
            
            # 让用户选择数据文件
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("选择数据文件"),
                "",
                "Parquet Files (*.parquet);;CSV Files (*.csv);;All Files (*.*)"
            )
            
            if not file_path:
                return
            
            # 读取数据
            if file_path.endswith('.parquet'):
                lf = pl.scan_parquet(file_path)
            elif file_path.endswith('.csv'):
                lf = pl.scan_csv(file_path)
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("不支持的文件格式")
                )
                return
            
            # 创建列名翻译器（使用默认上下文 "ColumnNames"）
            column_translator = ColumnNameTranslator()
            
            # 创建并显示plotter窗口
            self.plotter_window = MultiCurvePlotterWidget(
                lf=lf,
                str_name_col_timestamp=None,  # 自动检测第一列为时间列
                column_translator=column_translator
            )
            self.plotter_window.setWindowTitle(self.tr("数据可视化"))
            self.plotter_window.show()
            
        except ImportError as e:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("缺少依赖库: {}").format(str(e))
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("打开数据可视化失败: {}").format(str(e))
            )
