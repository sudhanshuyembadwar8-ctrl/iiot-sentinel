"""
sensors.py — Physics-based industrial sensor simulation engine
Simulates 6 sensors with realistic noise, drift, and failure modes.
"""

import math
import random
import time


class Sensor:
    """A single industrial sensor with drift, noise, and fault injection."""

    def __init__(self, name: str, unit: str, base: float,
                 noise: float, drift_rate: float,
                 min_val: float, max_val: float,
                 warning_lo: float, warning_hi: float,
                 critical_lo: float, critical_hi: float):
        self.name        = name
        self.unit        = unit
        self.base        = base
        self.noise       = noise
        self.drift_rate  = drift_rate
        self.min_val     = min_val
        self.max_val     = max_val
        self.warning_lo  = warning_lo
        self.warning_hi  = warning_hi
        self.critical_lo = critical_lo
        self.critical_hi = critical_hi

        self._value      = base
        self._drift      = 0.0
        self._fault_mode = False
        self._fault_end  = 0.0
        self._t          = 0

    def read(self) -> dict:
        self._t += 1

        # Slow sinusoidal drift (simulates temperature of day cycle etc.)
        self._drift = self.drift_rate * math.sin(self._t / 120 * math.pi)

        # Random fault injection (1% chance each tick, lasts 10–30 s)
        if not self._fault_mode and random.random() < 0.01:
            self._fault_mode = True
            self._fault_end  = time.time() + random.uniform(10, 30)

        if self._fault_mode and time.time() > self._fault_end:
            self._fault_mode = False

        # Compute raw value
        if self._fault_mode:
            # Spike toward critical boundary
            spike  = random.choice([self.critical_hi * 1.05, self.critical_lo * 0.95])
            target = spike
        else:
            target = self.base + self._drift

        # Low-pass filter (smooth transitions)
        self._value += (target - self._value) * 0.15
        self._value += random.gauss(0, self.noise)
        self._value  = max(self.min_val, min(self.max_val, self._value))

        val = round(self._value, 2)

        # Determine status
        if val <= self.critical_lo or val >= self.critical_hi:
            status = "CRITICAL"
        elif val <= self.warning_lo or val >= self.warning_hi:
            status = "WARNING"
        else:
            status = "NORMAL"

        return {
            "name":    self.name,
            "value":   val,
            "unit":    self.unit,
            "status":  status,
            "min":     self.min_val,
            "max":     self.max_val,
            "warn_lo": self.warning_lo,
            "warn_hi": self.warning_hi,
            "crit_lo": self.critical_lo,
            "crit_hi": self.critical_hi,
        }


class SensorEngine:
    """Factory floor sensor bank — 6 sensors covering key industrial parameters."""

    def __init__(self):
        self.sensors: dict[str, Sensor] = {
            "temperature": Sensor(
                name="temperature", unit="°C",
                base=72.0,   noise=0.4,  drift_rate=8.0,
                min_val=0,   max_val=150,
                warning_lo=40, warning_hi=90,
                critical_lo=20, critical_hi=110,
            ),
            "humidity": Sensor(
                name="humidity", unit="%RH",
                base=55.0,   noise=0.5,  drift_rate=6.0,
                min_val=0,   max_val=100,
                warning_lo=30, warning_hi=75,
                critical_lo=15, critical_hi=90,
            ),
            "pressure": Sensor(
                name="pressure", unit="bar",
                base=4.2,    noise=0.05, drift_rate=0.5,
                min_val=0,   max_val=10,
                warning_lo=2.5, warning_hi=6.0,
                critical_lo=1.0, critical_hi=8.0,
            ),
            "vibration": Sensor(
                name="vibration", unit="mm/s",
                base=2.1,    noise=0.15, drift_rate=1.5,
                min_val=0,   max_val=20,
                warning_lo=0, warning_hi=4.5,
                critical_lo=0, critical_hi=7.1,
            ),
            "power": Sensor(
                name="power", unit="kW",
                base=18.5,   noise=0.3,  drift_rate=3.0,
                min_val=0,   max_val=50,
                warning_lo=5, warning_hi=30,
                critical_lo=2, critical_hi=40,
            ),
            "flow_rate": Sensor(
                name="flow_rate", unit="L/min",
                base=85.0,   noise=0.8,  drift_rate=10.0,
                min_val=0,   max_val=200,
                warning_lo=50, warning_hi=130,
                critical_lo=20, critical_hi=160,
            ),
        }

    def read_all(self) -> dict:
        return {key: sensor.read() for key, sensor in self.sensors.items()}
