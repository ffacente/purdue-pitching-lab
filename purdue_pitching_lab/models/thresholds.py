"""Benchmarks and static thresholds used across the application."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkSet:
    """Represents baseline benchmarks for a pitch family."""

    velocity: float
    induced_vertical_break: float
    horizontal_break: float
    spin_rate: float


PROGRAM_BENCHMARKS = {
    "Fastball": BenchmarkSet(90.0, 16.0, 8.0, 2250.0),
    "Sinker": BenchmarkSet(89.0, 12.0, 14.0, 2100.0),
    "Slider": BenchmarkSet(82.0, -1.0, -12.0, 2450.0),
    "Curveball": BenchmarkSet(78.0, -10.0, -7.0, 2550.0),
    "Changeup": BenchmarkSet(82.0, 10.0, 14.0, 1800.0),
    "Cutter": BenchmarkSet(86.0, 8.0, -2.0, 2350.0),
}

PITCH_CLUSTER_THRESHOLDS = {
    "Power Fastball": {"min_velocity": 92.0, "min_ivb": 14.0},
    "Ride Fastball": {"min_velocity": 88.0, "min_ivb": 17.0},
    "Running Fastball": {"min_velocity": 88.0, "min_hb": 12.0},
    "Sinker": {"max_ivb": 12.0, "min_hb": 12.0},
    "Sweeper": {"max_ivb": 2.0, "max_hb": -14.0},
    "Gyro Slider": {"max_ivb": 1.0, "min_hb": -8.0, "max_hb": -2.0},
    "Power Slider": {"min_velocity": 84.0, "max_ivb": 2.0, "max_hb": -8.0},
    "Slurve": {"max_ivb": -5.0, "max_hb": -8.0},
    "Vertical Changeup": {"max_velocity": 86.0, "min_ivb": 12.0},
}