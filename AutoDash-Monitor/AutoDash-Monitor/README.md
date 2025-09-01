# AutoDash Monitor 🚗💻

Futuristic **automotive-style system monitor** for Windows/macOS/Linux built with **Python + PyQt5 + pyqtgraph**.

## Features (v0.1)
- Real-time **CPU usage per core** (speedometer gauges)
- **RAM & VRAM** usage
- **GPU load & temperature** (via GPUtil when available)
- **Network speed** meter with live graph
- **Disk usage** + read/write speed graph
- **Speedometer-style** dials for CPU/GPU
- **Battery / power** status (laptops)
- **Temperature map** for CPU/GPU/board sensors
- **Engine start** animation on launch
- **Night/Day** theme switch
- **Process killer** panel (end tasks quickly)
- **Alerts** (overheating / high usage) with tray notifications
- **Logging & history** (CSV) + in-app history plots
- **Compact HUD** overlay (always-on-top mini widget)
- **Benchmark / stress test** (CPU) to visualize performance

> GPU features fall back gracefully if no NVIDIA GPU / sensors are present.

## Quick Start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Notes
- On Linux, you may need `lm-sensors` (for temps) and to run `sensors-detect`.
- Some GPU temps require vendor tools/drivers. If unavailable, the app will still run.
- Stress test intentionally consumes CPU. Use responsibly and press **Stop** to end.

## License
MIT © 2025 Mikael
