import psutil

def list_processes(limit=50):
    procs = []
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info.get("name") or "Unknown",
                "cpu": info.get("cpu_percent") or 0.0,
                "mem": info.get("memory_percent") or 0.0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: (x["cpu"], x["mem"]), reverse=True)
    return procs[:limit]

def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=2)
        except psutil.TimeoutExpired:
            p.kill()
        return True, None
    except Exception as e:
        return False, str(e)
