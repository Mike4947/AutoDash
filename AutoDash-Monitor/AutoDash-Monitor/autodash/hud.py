from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel

class HUD(QDialog):
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.monitor = monitor
        self.label = QLabel("--", self)
        self.label.setStyleSheet("QLabel { background: rgba(15,21,29,180); color: #9ecfff; padding: 12px 16px; border-radius: 12px; font-size: 14pt; }")
        layout = QVBoxLayout(self); layout.addWidget(self.label)
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1000)
        self.refresh()

    def refresh(self):
        s = self.monitor.snapshot()
        txt = f"CPU {int(s['cpu_total'])}% | RAM {int(s['ram_percent'])}% | NET ↓{int(s['net_down_bps']/1024)} KB/s ↑{int(s['net_up_bps']/1024)} KB/s"
        self.label.setText(txt)
