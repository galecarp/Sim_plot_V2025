import asyncio
import argparse
import os.path
import sys

from PySide6.QtCore import QTranslator, QLocale, QLockFile
from qasync import QApplication, run

from app.builtin.gitlab_updater import GitlabUpdater
from app.builtin.locale import detect_system_ui_language
from app.main_window import MainWindow
from qdarktheme import enable_hi_dpi


async def task():
    app_close_event = asyncio.Event()
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()
    await main_window.async_init()
    await app_close_event.wait()
    
    # Give asyncio a chance to clean up pending tasks
    await asyncio.sleep(0)


def main(enable_updater: bool = True, language: str = None):
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='PySide6 Template Application')
    parser.add_argument('--lang', '--language', 
                       dest='language',
                       type=str,
                       default=language,
                       help='Language code (e.g., zh_CN, en_US). If not specified, uses system language.')
    
    # 只解析已知参数，保留其他参数给 QApplication
    args, remaining = parser.parse_known_args()
    
    # init updater, updater will remove some arguments
    # and do update logic
    # updater = GithubUpdater()
    # updater.project_name = "SHIINASAMA/pyside_template"
    updater = GitlabUpdater()
    updater.base_url = "https://gitlab.mikumikumi.xyz"
    updater.project_name = "kaoru/pyside_template"
    updater.is_enable = enable_updater

    # check if the app is already running
    lock_file = QLockFile("App.lock")
    if not lock_file.lock():
        sys.exit(0)

    if os.path.exists("updater.json"):
        updater.load_from_file_and_override("updater.json")

    # enable hdpi
    enable_hi_dpi()

    # init QApplication (使用剩余参数)
    sys.argv = [sys.argv[0]] + remaining
    app = QApplication(sys.argv)

    # i18n - 加载应用翻译
    translator_app = QTranslator()
    lang_code = args.language if args.language else detect_system_ui_language()
    
    # 加载主应用翻译文件
    if translator_app.load(f":/i18n/{lang_code}.qm"):
        app.installTranslator(translator_app)
        print(f"已加载应用翻译: {lang_code}")
    
    # 加载 plotter 模块翻译文件（如果存在）
    translator_plotter = QTranslator()
    plotter_ts_path = f"app/plotter/i18n/plotter_{lang_code}.qm"
    if os.path.exists(plotter_ts_path):
        if translator_plotter.load(plotter_ts_path):
            app.installTranslator(translator_plotter)
            print(f"已加载 Plotter 翻译: {lang_code}")
    
    # 将语言代码保存到应用属性，供其他模块使用
    app.setProperty("language_code", lang_code)

    # start event loop
    try:
        run(task())
    except RuntimeError as e:
        # Suppress "Event loop stopped before Future completed" error on exit
        if "Event loop stopped before Future completed" not in str(e):
            raise


def main_no_updater():
    main(enable_updater=False)


def run_module():
    main()


if __name__ == "__main__":
    main()
