"""
anomaly.py — Multi-algorithm anomaly detection engine
Uses: Z-score, moving average deviation, and rate-of-change spike detection.
"""

from collections import deque
import math


class SensorBuffer:
    """Rolling window of sensor readings for statistical analysis."""

    def __init__(self, window: int = 60):
        self.window = window
        self.data: deque[float] = deque(maxlen=window)

    def push(self, value: float):
        self.data.append(value)

    @property
    def mean(self) -> float:
        if not self.data:
            return 0.0
        return sum(self.data) / len(self.data)

    @property
    def std(self) -> float:
        if len(self.data) < 2:
            return 0.0
        m = self.mean
        variance = sum((x - m) ** 2 for x in self.data) / len(self.data)
        return math.sqrt(variance)

    @property
    def last(self) -> float | None:
        return self.data[-1] if self.data else None

    @property
    def prev(self) -> float | None:
        return self.data[-2] if len(self.data) >= 2 else None


class AnomalyDetector:
    """
    Detects anomalies using three methods:
      1. Threshold breach   — static warning / critical bounds
      2. Z-score outlier    — value > 2.5 std from rolling mean
      3. Rate-of-change     — sudden spike between consecutive readings
    """

    ZSCORE_THRESHOLD = 2.5
    ROC_MULTIPLIER   = 3.0   # flag if change > 3× typical change

    def __init__(self, window: int = 60):
        self.buffers: dict[str, SensorBuffer] = {}
        self.window = window

    def _get_buffer(self, name: str) -> SensorBuffer:
        if name not in self.buffers:
            self.buffers[name] = SensorBuffer(self.window)
        return self.buffers[name]

    def check(self, readings: dict) -> list[dict]:
        alerts = []

        for key, r in readings.items():
            val = r["value"]
            buf = self._get_buffer(key)
            buf.push(val)

            # 1. Threshold breach (already computed by sensor)
            if r["status"] == "CRITICAL":
                alerts.append({
                    "sensor":  key,
                    "method":  "threshold",
                    "severity": "CRITICAL",
                    "value":   val,
                    "unit":    r["unit"],
                    "message": f"{key.title()} CRITICAL: {val}{r['unit']}",
                })
            elif r["status"] == "WARNING":
                alerts.append({
                    "sensor":  key,
                    "method":  "threshold",
                    "severity": "WARNING",
                    "value":   val,
                    "unit":    r["unit"],
                    "message": f"{key.title()} WARNING: {val}{r['unit']}",
                })

            # 2. Z-score anomaly
            if len(buf.data) >= 20:
                std = buf.std
                if std > 0:
                    z = abs(val - buf.mean) / std
                    if z > self.ZSCORE_THRESHOLD and r["status"] == "NORMAL":
                        alerts.append({
                            "sensor":   key,
                            "method":   "z_score",
                            "severity": "WARNING",
                            "value":    val,
                            "unit":     r["unit"],
                            "message":  f"{key.title()} statistical anomaly (z={z:.1f})",
                        })

            # 3. Rate-of-change spike
            if buf.prev is not None and buf.std > 0:
                change     = abs(val - buf.prev)
                avg_change = buf.std * 0.5    # approximate typical per-step change
                if avg_change > 0 and change > self.ROC_MULTIPLIER * avg_change:
                    # Only flag if not already alerted
                    already = any(a["sensor"] == key and a["method"] == "threshold" for a in alerts)
                    if not already:
                        alerts.append({
                            "sensor":   key,
                            "method":   "rate_of_change",
                            "severity": "WARNING",
                            "value":    val,
                            "unit":     r["unit"],
                            "message":  f"{key.title()} sudden spike Δ={change:.2f}{r['unit']}",
                        })

        return alerts
