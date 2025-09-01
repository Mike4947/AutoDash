import multiprocessing as mp, time, math

def _worker(stop, intensity=1.0):
    # Busy loop; do light math to avoid compiler optimization
    while not stop.is_set():
        x = 0.0
        for i in range(int(5e5 * intensity)):
            x += math.sqrt((i % 137) + 0.1)
        if intensity < 1.0:
            time.sleep(0.01)

class CPUStressor:
    def __init__(self):
        self.procs = []
        self.stop_event = None

    def start(self, workers=None, intensity=1.0):
        if self.procs: return
        if workers is None:
            workers = max(1, mp.cpu_count()-1)
        self.stop_event = mp.Event()
        self.procs = [mp.Process(target=_worker, args=(self.stop_event, intensity)) for _ in range(workers)]
        for p in self.procs: p.start()

    def stop(self):
        if not self.procs: return
        self.stop_event.set()
        for p in self.procs:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        self.procs = []
        self.stop_event = None
