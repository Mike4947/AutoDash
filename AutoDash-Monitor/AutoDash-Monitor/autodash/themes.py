from PyQt5.QtGui import QColor, QPalette

DARK_QSS = '''
* { font-family: Inter, Segoe UI, Roboto, Arial; }
QMainWindow, QWidget { background-color: #0b0f14; color: #e6e9ef; }
QGroupBox { border: 1px solid #1e2a36; border-radius: 12px; margin-top: 14px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 4px 8px; color: #9ecfff; }
QPushButton { background: #12202d; border: 1px solid #1f3242; padding: 8px 12px; border-radius: 10px; }
QPushButton:hover { background: #192a3a; }
QPushButton:pressed { background: #0e1821; }
QTabWidget::pane { border: 1px solid #1e2a36; border-radius: 12px; }
QTabBar::tab { background: #0f151d; border: 1px solid #1e2a36; padding: 8px 12px; border-top-left-radius: 10px; border-top-right-radius: 10px; }
QTabBar::tab:selected { background: #14202c; color: #9ecfff; }
QProgressBar { border: 1px solid #1e2a36; border-radius: 8px; text-align: center; }
QProgressBar::chunk { background-color: #3795ff; border-radius: 6px; }
QTableWidget { gridline-color: #1e2a36; selection-background-color: #1a2a40; }
QToolTip { background: #0f151d; color: #e6e9ef; border: 1px solid #1e2a36; }
'''

LIGHT_QSS = '''
* { font-family: Inter, Segoe UI, Roboto, Arial; }
QMainWindow, QWidget { background-color: #f7f9fb; color: #0b0f14; }
QGroupBox { border: 1px solid #d7dfe7; border-radius: 12px; margin-top: 14px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 4px 8px; color: #024b94; }
QPushButton { background: #ffffff; border: 1px solid #d7dfe7; padding: 8px 12px; border-radius: 10px; }
QPushButton:hover { background: #eef6ff; }
QPushButton:pressed { background: #ddeeff; }
QTabWidget::pane { border: 1px solid #d7dfe7; border-radius: 12px; }
QTabBar::tab { background: #ffffff; border: 1px solid #d7dfe7; padding: 8px 12px; border-top-left-radius: 10px; border-top-right-radius: 10px; }
QTabBar::tab:selected { background: #eef6ff; color: #024b94; }
QProgressBar { border: 1px solid #d7dfe7; border-radius: 8px; text-align: center; }
QProgressBar::chunk { background-color: #2a7bdf; border-radius: 6px; }
QTableWidget { gridline-color: #d7dfe7; selection-background-color: #ddeeff; }
QToolTip { background: #ffffff; color: #0b0f14; border: 1px solid #d7dfe7; }
'''

def apply_dark(app):
    app.setStyleSheet(DARK_QSS)

def apply_light(app):
    app.setStyleSheet(LIGHT_QSS)
