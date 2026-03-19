# ⚡ IIoT Sentinel

> **Real-time Industrial IoT Sensor Dashboard** — Built with FastAPI, WebSockets, SQLite & Chart.js

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![WebSockets](https://img.shields.io/badge/WebSockets-Live-6366f1?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-Logging-003B57?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A production-grade IIoT dashboard that monitors **6 industrial sensors** in real time, detects anomalies using **3 algorithms**, logs everything to SQLite, and streams live data via **WebSockets** to a dark-themed web dashboard.

---

## Features

| Feature | Details |
|---|---|
| **6 Sensor Streams** | Temperature, Humidity, Pressure, Vibration, Power, Flow Rate |
| **Real-Time WebSocket** | Sub-second live updates pushed to all connected dashboards |
| **3-Algorithm Anomaly Detection** | Threshold breach + Z-score + Rate-of-change spike detection |
| **SQLite Data Logging** | Every reading and alert stored with timestamp |
| **Live Charts** | Scrolling time-series with 1m/5m/10m window |
| **Alert Feed** | Real-time severity-coded alert stream |
| **CSV Export** | Download all sensor history via one click |
| **Physics-Based Simulation** | Realistic drift, noise, and random fault injection |

---

## Project Structure

```
iiot-sentinel/
├── main.py          # FastAPI app + WebSocket broadcast loop
├── sensors.py       # Physics-based sensor simulation engine
├── anomaly.py       # Multi-algorithm anomaly detector
├── database.py      # SQLite logging + REST data layer
├── dashboard/
│   └── index.html   # Single-file live dashboard (no build step)
├── requirements.txt
└── README.md
```

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/iiot-sentinel.git
cd iiot-sentinel

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py

# 4. Open browser
# → http://localhost:8000
```

---

## How Anomaly Detection Works

IIoT Sentinel uses **three independent detection algorithms** running in parallel:

1. **Threshold Breach** — Static `warning` and `critical` bounds per sensor. Instant, reliable.
2. **Z-Score Outlier** — Flags readings that deviate more than **2.5 standard deviations** from the rolling 60-second mean. Catches subtle drifts.
3. **Rate-of-Change Spike** — Flags readings where the per-step change is **3× the typical change rate**. Catches sudden faults.

---

## REST API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Live dashboard HTML |
| `/ws` | WS | WebSocket stream |
| `/api/history?sensor=temperature&limit=60` | GET | Sensor history |
| `/api/alerts?limit=20` | GET | Recent alerts |
| `/api/summary` | GET | Aggregate stats |
| `/api/export` | GET | Download CSV |

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, asyncio, WebSockets
- **Database**: SQLite (zero-config, embedded)
- **Frontend**: Vanilla JS, Chart.js 4, CSS Variables
- **Simulation**: Physics-based sensor model (low-pass filter + Gaussian noise + fault injection)

---

## Author

**Sudhanshu Yembadwar** — B.Tech IIoT, SVPCET Nagpur  
*"Machines talk in data. I make them speak in intelligence."*

---

## License

MIT — free to use, learn from, and build on.
