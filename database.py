"""
database.py — SQLite data layer for IIoT Sentinel
Handles: sensor log, alert log, summary stats, CSV export.
"""

import csv
import io
import sqlite3
from datetime import datetime


class Database:
    def __init__(self, path: str = "sentinel.db"):
        self.path = path
        self.conn: sqlite3.Connection | None = None

    def init(self):
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                sensor    TEXT NOT NULL,
                value     REAL NOT NULL,
                unit      TEXT NOT NULL,
                status    TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                sensor    TEXT NOT NULL,
                method    TEXT NOT NULL,
                severity  TEXT NOT NULL,
                value     REAL NOT NULL,
                message   TEXT NOT NULL
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor ON sensor_log(sensor, ts)")
        self.conn.commit()

    def log(self, readings: dict, alerts: list):
        if not self.conn:
            return
        ts  = datetime.utcnow().isoformat()
        cur = self.conn.cursor()

        for key, r in readings.items():
            cur.execute(
                "INSERT INTO sensor_log (ts, sensor, value, unit, status) VALUES (?,?,?,?,?)",
                (ts, key, r["value"], r["unit"], r["status"]),
            )

        for a in alerts:
            cur.execute(
                "INSERT INTO alert_log (ts, sensor, method, severity, value, message) VALUES (?,?,?,?,?,?)",
                (ts, a["sensor"], a["method"], a["severity"], a["value"], a["message"]),
            )

        self.conn.commit()

    def get_history(self, sensor: str, limit: int = 60) -> list[dict]:
        if not self.conn:
            return []
        cur  = self.conn.cursor()
        rows = cur.execute(
            "SELECT ts, value, status FROM sensor_log WHERE sensor=? ORDER BY id DESC LIMIT ?",
            (sensor, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_alerts(self, limit: int = 20) -> list[dict]:
        if not self.conn:
            return []
        cur  = self.conn.cursor()
        rows = cur.execute(
            "SELECT ts, sensor, severity, message FROM alert_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_summary(self) -> dict:
        if not self.conn:
            return {}
        cur = self.conn.cursor()
        summary = {}

        sensors = cur.execute("SELECT DISTINCT sensor FROM sensor_log").fetchall()
        for row in sensors:
            s = row["sensor"]
            stats = cur.execute("""
                SELECT
                    ROUND(AVG(value), 2) as avg,
                    ROUND(MIN(value), 2) as min,
                    ROUND(MAX(value), 2) as max,
                    COUNT(*) as count
                FROM sensor_log WHERE sensor=?
            """, (s,)).fetchone()
            summary[s] = dict(stats)

        summary["total_alerts"] = cur.execute(
            "SELECT COUNT(*) as c FROM alert_log"
        ).fetchone()["c"]

        summary["critical_alerts"] = cur.execute(
            "SELECT COUNT(*) as c FROM alert_log WHERE severity='CRITICAL'"
        ).fetchone()["c"]

        return summary

    def export_csv(self) -> str:
        if not self.conn:
            return ""
        cur  = self.conn.cursor()
        rows = cur.execute(
            "SELECT ts, sensor, value, unit, status FROM sensor_log ORDER BY id DESC LIMIT 5000"
        ).fetchall()

        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["timestamp", "sensor", "value", "unit", "status"])
        for row in rows:
            writer.writerow(list(row))

        return out.getvalue()

    def close(self):
        if self.conn:
            self.conn.close()
