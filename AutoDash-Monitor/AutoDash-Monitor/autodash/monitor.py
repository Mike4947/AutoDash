import time, psutil
from collections import deque

try:
    import GPUtil
except Exception:
    GPUtil = None

class Monitor:
    def __init__(self, history_len=300):
        self.prev_net = psutil.net_io_counters() if hasattr(psutil, "net_io_counters") else None
        self.prev_disk = psutil.disk_io_counters() if hasattr(psutil, "disk_io_counters") else None
        self.prev_time = time.time()
        self.history = {
            "net_up": deque(maxlen=history_len),
            "net_down": deque(maxlen=history_len),
            "disk_read": deque(maxlen=history_len),
            "disk_write": deque(maxlen=history_len),
            "cpu_total": deque(maxlen=history_len),
            "ram_used": deque(maxlen=history_len),
            "gpu_load": deque(maxlen=history_len),
            "gpu_temp": deque(maxlen=history_len),
        }

    def snapshot(self):
        now = time.time()
        dt = max(1e-6, now - self.prev_time)
        cpu_per_core = psutil.cpu_percent(percpu=True)
        cpu_total = psutil.cpu_percent()
        vm = psutil.virtual_memory()
        ram_used = vm.used
        ram_percent = vm.percent

        # Battery
        batt = None
        if hasattr(psutil, "sensors_battery"):
            try: batt = psutil.sensors_battery()
            except Exception: batt = None

        # Temperatures
        temps = {}
        if hasattr(psutil, "sensors_temperatures"):
            try:
                for name, entries in psutil.sensors_temperatures(fahrenheit=False).items():
                    temps[name] = [{"label": e.label or name, "current": e.current} for e in entries]
            except Exception:
                temps = {}

        # GPU
        gpu = {"load": None, "temp": None, "vram_total": None, "vram_used": None, "name": None}
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    gpu["name"] = g.name
                    gpu["load"] = float(g.load) * 100.0
                    gpu["temp"] = float(g.temperature) if g.temperature is not None else None
                    gpu["vram_total"] = float(g.memoryTotal) * 1024**2
                    gpu["vram_used"] = float(g.memoryUsed) * 1024**2
            except Exception:
                pass

        # Network
        up_bps = down_bps = 0.0
        if self.prev_net:
            cur = psutil.net_io_counters()
            up_bps = max(0.0, (cur.bytes_sent - self.prev_net.bytes_sent) / dt)
            down_bps = max(0.0, (cur.bytes_recv - self.prev_net.bytes_recv) / dt)
            self.prev_net = cur

        # Disk
        read_bps = write_bps = 0.0
        if self.prev_disk:
            curd = psutil.disk_io_counters()
            read_bps = max(0.0, (curd.read_bytes - self.prev_disk.read_bytes) / dt)
            write_bps = max(0.0, (curd.write_bytes - self.prev_disk.write_bytes) / dt)
            self.prev_disk = curd

        self.prev_time = now

        # push to history
        self.history["net_up"].append(up_bps)
        self.history["net_down"].append(down_bps)
        self.history["disk_read"].append(read_bps)
        self.history["disk_write"].append(write_bps)
        self.history["cpu_total"].append(cpu_total)
        self.history["ram_used"].append(ram_used)
        if gpu["load"] is not None: self.history["gpu_load"].append(gpu["load"])
        if gpu["temp"] is not None: self.history["gpu_temp"].append(gpu["temp"])

        return {
            "cpu_per_core": cpu_per_core,
            "cpu_total": cpu_total,
            "ram_total": vm.total,
            "ram_used": vm.used,
            "ram_percent": ram_percent,
            "battery": batt,
            "temps": temps,
            "gpu": gpu,
            "net_up_bps": up_bps,
            "net_down_bps": down_bps,
            "disk_read_bps": read_bps,
            "disk_write_bps": write_bps,
        }
