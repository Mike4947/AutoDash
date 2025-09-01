import sys, os, time
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSequentialAnimationGroup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QGroupBox, QProgressBar, QPushButton, QTabWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QCheckBox, QSpinBox)
import pyqtgraph as pg

from .gauge import Gauge
from .monitor import Monitor
from .processes import list_processes, kill_process
from .logging_utils import CSVLogger
from .themes import apply_dark, apply_light
from .hud import HUD
from .stress import CPUStressor

def human_bytes(n):
    if n is None: return "--"
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0: return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def human_bps(n):
    if n is None: return "--"
    for unit in ["B/s","KB/s","MB/s","GB/s","TB/s"]:
        if n < 1024.0: return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB/s"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoDash Monitor")
        self.resize(1200, 800)
        self.monitor = Monitor(history_len=600)
        self.logger = CSVLogger(log_dir="logs")
        self.hud = None
        self.stressor = CPUStressor()

        # Alerts thresholds
        self.temp_threshold = 85
        self.cpu_threshold = 95
        self.ram_threshold = 95

        self._make_ui()
        self._engine_start_animation()
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1000)

    # ---------------- UI ----------------
    def _make_ui(self):
        tabs = QTabWidget(self)
        self.setCentralWidget(tabs)

        # Overview tab
        self.overview = QWidget(); tabs.addTab(self.overview, "Overview")
        ov_layout = QVBoxLayout(self.overview)

        # Top gauges
        gbox = QGroupBox("Live Gauges")
        gl = QGridLayout(gbox)
        self.cpu_gauges = []
        cpu_cores = max(1, len(self.monitor.snapshot()["cpu_per_core"]))
        for i in range(min(cpu_cores, 8)):
            g = Gauge(label=f"CPU Core {i+1}")
            self.cpu_gauges.append(g)
            gl.addWidget(g, i//4, i%4)
        self.gpu_gauge = Gauge(label="GPU Load")
        gl.addWidget(self.gpu_gauge, 2, 0)
        self.cpu_total_gauge = Gauge(label="CPU Total")
        gl.addWidget(self.cpu_total_gauge, 2, 1)
        self.ram_bar = QProgressBar(); self.ram_bar.setFormat("RAM %p%")
        gl.addWidget(self.ram_bar, 2, 2, 1, 2)
        ov_layout.addWidget(gbox)

        # Middle stats
        stats = QGroupBox("System Stats")
        sl = QGridLayout(stats)
        self.label_gpu = QLabel("GPU: --")
        sl.addWidget(self.label_gpu, 0, 0)
        self.label_vram = QLabel("VRAM: --")
        sl.addWidget(self.label_vram, 0, 1)
        self.label_net = QLabel("NET: --")
        sl.addWidget(self.label_net, 1, 0)
        self.label_disk = QLabel("DISK: --")
        sl.addWidget(self.label_disk, 1, 1)
        self.label_batt = QLabel("Battery: --")
        sl.addWidget(self.label_batt, 2, 0)
        ov_layout.addWidget(stats)

        # Temperature map
        tgroup = QGroupBox("Temperature Map")
        tl = QVBoxLayout(tgroup)
        self.temp_labels = []
        self.temp_container = QWidget()
        self.temp_layout = QGridLayout(self.temp_container)
        tl.addWidget(self.temp_container)
        ov_layout.addWidget(tgroup)

        # Graphs tab
        self.graphs = QWidget(); tabs.addTab(self.graphs, "Graphs")
        glay = QGridLayout(self.graphs)
        pg.setConfigOptions(antialias=True)
        self.plot_net = pg.PlotWidget(title="Network (dl/ul)")
        self.plot_disk = pg.PlotWidget(title="Disk (read/write)")
        self.plot_cpu = pg.PlotWidget(title="CPU Total (%)")
        self.plot_gpu = pg.PlotWidget(title="GPU Load/Temp")
        for pl in [self.plot_net, self.plot_disk, self.plot_cpu, self.plot_gpu]:
            pl.showGrid(x=True, y=True, alpha=0.2)
        self.cur_net_down = self.plot_net.plot(pen=pg.mkPen(width=2))
        self.cur_net_up = self.plot_net.plot(pen=pg.mkPen(style=Qt.DashLine,width=2))
        self.cur_disk_r = self.plot_disk.plot(pen=pg.mkPen(width=2))
        self.cur_disk_w = self.plot_disk.plot(pen=pg.mkPen(style=Qt.DashLine,width=2))
        self.cur_cpu = self.plot_cpu.plot(pen=pg.mkPen(width=2))
        self.cur_gpu = self.plot_gpu.plot(pen=pg.mkPen(width=2))
        self.cur_gpu_t = self.plot_gpu.plot(pen=pg.mkPen(style=Qt.DashLine,width=2))
        glay.addWidget(self.plot_net, 0, 0)
        glay.addWidget(self.plot_disk, 0, 1)
        glay.addWidget(self.plot_cpu, 1, 0)
        glay.addWidget(self.plot_gpu, 1, 1)

        # Processes tab
        self.proc = QWidget(); tabs.addTab(self.proc, "Processes")
        pl = QVBoxLayout(self.proc)
        self.table = QTableWidget(0, 4, self.proc)
        self.table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "MEM %"])
        pl.addWidget(self.table)
        row = QHBoxLayout()
        self.btn_kill = QPushButton("Kill Selected")
        self.btn_kill.clicked.connect(self.kill_selected)
        row.addWidget(self.btn_kill)
        row.addStretch(1)
        pl.addLayout(row)

        # Tools tab
        self.tools = QWidget(); tabs.addTab(self.tools, "Tools")
        tl2 = QGridLayout(self.tools)
        self.btn_hud = QPushButton("Toggle HUD")
        self.btn_hud.clicked.connect(self.toggle_hud)
        self.theme_toggle = QCheckBox("Day Mode")
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        self.btn_stress_start = QPushButton("Start CPU Stress")
        self.btn_stress_stop = QPushButton("Stop CPU Stress")
        self.btn_stress_start.clicked.connect(self.start_stress)
        self.btn_stress_stop.clicked.connect(self.stop_stress)
        tl2.addWidget(self.btn_hud, 0, 0)
        tl2.addWidget(self.theme_toggle, 0, 1)
        tl2.addWidget(self.btn_stress_start, 1, 0)
        tl2.addWidget(self.btn_stress_stop, 1, 1)

        # Alerts
        arow = QHBoxLayout()
        arow.addWidget(QLabel("Temp alert °C>"))
        self.spin_temp = QSpinBox(); self.spin_temp.setRange(40, 110); self.spin_temp.setValue(self.temp_threshold)
        self.spin_temp.valueChanged.connect(lambda v: setattr(self, "temp_threshold", v))
        arow.addWidget(self.spin_temp)
        arow.addWidget(QLabel("CPU %>"))
        self.spin_cpu = QSpinBox(); self.spin_cpu.setRange(50, 100); self.spin_cpu.setValue(self.cpu_threshold)
        self.spin_cpu.valueChanged.connect(lambda v: setattr(self, "cpu_threshold", v))
        arow.addWidget(self.spin_cpu)
        arow.addWidget(QLabel("RAM %>"))
        self.spin_ram = QSpinBox(); self.spin_ram.setRange(50, 100); self.spin_ram.setValue(self.ram_threshold)
        self.spin_ram.valueChanged.connect(lambda v: setattr(self, "ram_threshold", v))
        arow.addWidget(self.spin_ram)
        arow.addStretch(1)
        tl2.addLayout(arow, 2, 0, 1, 2)

    # ---------------- Engine Start Animation ----------------
    def _engine_start_animation(self):
        # Rev up and back down sequentially per gauge
        self._anim_groups = []  # keep refs so GC doesn't stop animations
        for g in self.cpu_gauges + [self.gpu_gauge, self.cpu_total_gauge]:
            up = QPropertyAnimation(g, b"value", self)
            up.setDuration(1200)
            up.setStartValue(0)
            up.setEndValue(100)

            down = QPropertyAnimation(g, b"value", self)
            down.setDuration(700)
            down.setStartValue(100)
            down.setEndValue(0)

            seq = QSequentialAnimationGroup(self)
            seq.addAnimation(up)
            seq.addAnimation(down)
            seq.start()
            self._anim_groups.append(seq)

    # ---------------- Refresh ----------------
    def refresh(self):
        s = self.monitor.snapshot()
        # Gauges
        for i, val in enumerate(s["cpu_per_core"][:len(self.cpu_gauges)]):
            self.cpu_gauges[i].setValue(val)
        self.cpu_total_gauge.setValue(s["cpu_total"])
        if s["gpu"]["load"] is not None:
            self.gpu_gauge.setValue(s["gpu"]["load"])
            self.gpu_gauge.setLabel("GPU Load")
        else:
            self.gpu_gauge.setLabel("GPU Load (n/a)")

        # Bars/labels
        self.ram_bar.setValue(int(s["ram_percent"]))
        gpu = s["gpu"]
        self.label_gpu.setText(f"GPU: {gpu.get('name') or 'N/A'} | Load: {gpu.get('load') and int(gpu['load']) or 0}% | Temp: {gpu.get('temp') or '--'}°C")
        vram_used = gpu.get("vram_used"); vram_total = gpu.get("vram_total")
        if vram_total:
            self.label_vram.setText(f"VRAM: {human_bytes(vram_used)} / {human_bytes(vram_total)}")
        else:
            self.label_vram.setText("VRAM: N/A")

        self.label_net.setText(f"NET: ↓ {human_bps(s['net_down_bps'])} ↑ {human_bps(s['net_up_bps'])}")
        self.label_disk.setText(f"DISK: R {human_bps(s['disk_read_bps'])} W {human_bps(s['disk_write_bps'])}")
        batt = s["battery"]
        if batt:
            stat = "Charging" if batt.power_plugged else "On battery"
            self.label_batt.setText(f"Battery: {int(batt.percent)}% ({stat})")
        else:
            self.label_batt.setText("Battery: N/A")

        # Temperature map
        # Clear layout
        while self.temp_layout.count():
            item = self.temp_layout.takeAt(0)
            w = item.widget()
            if w: w.setParent(None)
        r = c = 0
        for name, entries in s["temps"].items():
            group = QGroupBox(name)
            vl = QVBoxLayout(group)
            for e in entries:
                lab = QLabel(f"{e['label']}: {e['current']} °C"); 
                # Color by temp
                t = e['current'] or 0
                color = "#3795ff" if t < 60 else ("#ffb037" if t < 80 else "#ff4d4d")
                lab.setStyleSheet(f"QLabel {{ background: #0f151d; border: 1px solid #1e2a36; padding: 6px 8px; border-radius: 8px; color: {color}; }}")
                vl.addWidget(lab)
            self.temp_layout.addWidget(group, r, c)
            c += 1
            if c >= 2:
                r += 1; c = 0

        # Graphs
        x = list(range(len(self.monitor.history["net_down"])))
        self.cur_net_down.setData(x, list(self.monitor.history["net_down"]))
        self.cur_net_up.setData(x, list(self.monitor.history["net_up"]))
        self.cur_disk_r.setData(x, list(self.monitor.history["disk_read"]))
        self.cur_disk_w.setData(x, list(self.monitor.history["disk_write"]))
        self.cur_cpu.setData(x, list(self.monitor.history["cpu_total"]))
        self.cur_gpu.setData(x, list(self.monitor.history["gpu_load"]))
        self.cur_gpu_t.setData(x, list(self.monitor.history["gpu_temp"]))

        # Processes
        procs = list_processes(limit=40)
        self.table.setRowCount(len(procs))
        for i, p in enumerate(procs):
            for j, k in enumerate(["pid","name","cpu","mem"]):
                item = QTableWidgetItem(str(int(p[k]) if isinstance(p[k], float) else p[k]))
                if j in (2,3): item.setText(f"{float(p[k]):.1f}")
                self.table.setItem(i, j, item)

        # Logging
        self.logger.log(s)

        # Alerts
        if self.monitor.history["gpu_temp"] and self.monitor.history["gpu_temp"][-1] and self.monitor.history["gpu_temp"][-1] > self.temp_threshold:
            self._warn(f"GPU temperature high: {int(self.monitor.history['gpu_temp'][-1])}°C")
        if s["cpu_total"] > self.cpu_threshold:
            self._warn(f"CPU usage high: {int(s['cpu_total'])}%")
        if s["ram_percent"] > self.ram_threshold:
            self._warn(f"RAM usage high: {int(s['ram_percent'])}%")

    def _warn(self, msg):
        # Lightweight inline warning – could be expanded to tray notifications
        self.statusBar().showMessage(msg, 3000)

    # ---------------- Actions ----------------
    def kill_selected(self):
        rows = set([idx.row() for idx in self.table.selectedIndexes()])
        if not rows: return
        for r in rows:
            pid_item = self.table.item(r, 0)
            if not pid_item: continue
            pid = int(pid_item.text())
            ok, err = kill_process(pid)
            if not ok:
                QMessageBox.warning(self, "Kill failed", f"Could not kill PID {pid}: {err}")
        self.refresh()

    def toggle_hud(self):
        if self.hud and self.hud.isVisible():
            self.hud.close(); self.hud = None
        else:
            self.hud = HUD(self.monitor, self); self.hud.show()

    def toggle_theme(self, state):
        if state == Qt.Checked:
            apply_light(QApplication.instance())
        else:
            apply_dark(QApplication.instance())

    def start_stress(self):
        try:
            self.stressor.start()
            self.statusBar().showMessage("CPU stress started", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Stress", f"Could not start stress: {e}")

    def stop_stress(self):
        try:
            self.stressor.stop()
            self.statusBar().showMessage("CPU stress stopped", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Stress", f"Could not stop stress: {e}")

def main():
    app = QApplication(sys.argv)
    apply_dark(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
