import csv, os, time, datetime

class CSVLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.file_path = self._file_for_today()
        self._ensure_header()

    def _file_for_today(self):
        date = datetime.date.today().isoformat()
        return os.path.join(self.log_dir, f"metrics_{date}.csv")

    def _ensure_header(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["timestamp","cpu_total","ram_percent","net_up_bps","net_down_bps","disk_read_bps","disk_write_bps","gpu_load","gpu_temp"])

    def rotate_if_needed(self):
        path = self._file_for_today()
        if path != self.file_path:
            self.file_path = path
            self._ensure_header()

    def log(self, snap):
        self.rotate_if_needed()
        row = [
            time.time(),
            snap.get("cpu_total"),
            snap.get("ram_percent"),
            snap.get("net_up_bps"),
            snap.get("net_down_bps"),
            snap.get("disk_read_bps"),
            snap.get("disk_write_bps"),
            (snap.get("gpu") or {}).get("load"),
            (snap.get("gpu") or {}).get("temp"),
        ]
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
