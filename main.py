#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from masterblaster_control.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MasterBlaster-Control")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
