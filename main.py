"""
IIoT Sentinel — Industrial IoT Real-Time Sensor Dashboard
Author: Sudhanshu Yembadwar
Stack: FastAPI + WebSockets + SQLite + Chart.js
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import Database
from sensors import SensorEngine
from anomaly import AnomalyDetector


# ── Startup / Shutdown ─────────────────────────────────────────────────────────

db = Database("sentinel.db")
engine = SensorEngine()
detector = AnomalyDetector()
connected_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    asyncio.create_task(broadcast_loop())
    print("✅  IIoT Sentinel running → http://localhost:8000")
    yield
    db.close()


app = FastAPI(title="IIoT Sentinel", lifespan=lifespan)


# ── WebSocket broadcast loop ───────────────────────────────────────────────────

async def broadcast_loop():
    """Push live sensor readings to all connected dashboards every second."""
    while True:
        readings = engine.read_all()
        alerts   = detector.check(readings)
        db.log(readings, alerts)

        payload = json.dumps({
            "ts":       datetime.utcnow().isoformat(),
            "readings": readings,
            "alerts":   alerts,
        })

        dead = []
        for ws in connected_clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connected_clients.remove(ws)

        await asyncio.sleep(1)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


# ── REST endpoints ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return Path("dashboard/index.html").read_text()


@app.get("/api/history")
async def history(sensor: str = "temperature", limit: int = 60):
    rows = db.get_history(sensor, limit)
    return JSONResponse(content=rows)


@app.get("/api/alerts")
async def get_alerts(limit: int = 20):
    return JSONResponse(content=db.get_alerts(limit))


@app.get("/api/summary")
async def summary():
    return JSONResponse(content=db.get_summary())


@app.get("/api/export")
async def export_csv():
    """Download all sensor logs as CSV."""
    csv_data = db.export_csv()
    return HTMLResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sentinel_export.csv"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
