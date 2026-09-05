import sys
from PySide6.QtWidgets import QApplication
from .logging.setup import configure_logging
from .paths import ensure_data_directories
from .ui.main_window import MainWindow
def main() -> int:
    ensure_data_directories(); configure_logging(); app=QApplication(sys.argv); window=MainWindow(); window.show(); return app.exec()
