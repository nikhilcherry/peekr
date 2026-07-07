"""Positive and negative tests for every anomaly flag code."""
from __future__ import annotations

import numpy as np

from peekr.anomalies import detect_anomalies


def test_has_nan_positive():
    arr = np.array([1.0, 2.0, np.nan, 4.0])
    assert "HAS_NAN" in detect_anomalies("x", arr)


def test_has_nan_negative():
    arr = np.array([1.0, 2.0, 3.0, 4.0])
    assert "HAS_NAN" not in detect_anomalies("x", arr)


def test_has_inf_positive():
    arr = np.array([1.0, np.inf, 3.0])
    assert "HAS_INF" in detect_anomalies("x", arr)


def test_has_inf_negative():
    arr = np.array([1.0, 2.0, 3.0])
    assert "HAS_INF" not in detect_anomalies("x", arr)


def test_all_nan_positive():
    arr = np.full(5, np.nan)
    assert "ALL_NAN" in detect_anomalies("x", arr)


def test_all_nan_negative():
    arr = np.array([1.0, np.nan, 3.0])
    assert "ALL_NAN" not in detect_anomalies("x", arr)


def test_constant_positive():
    arr = np.full(10, 3.0)
    assert "CONSTANT" in detect_anomalies("x", arr)


def test_constant_negative():
    arr = np.array([1.0, 2.0, 3.0])
    assert "CONSTANT" not in detect_anomalies("x", arr)


def test_near_constant_positive():
    arr = np.full(10, 5.0)
    arr[-1] += 1e-14
    assert "NEAR_CONSTANT" in detect_anomalies("x", arr)


def test_near_constant_negative():
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert "NEAR_CONSTANT" not in detect_anomalies("x", arr)


def test_outliers_positive():
    rng = np.random.default_rng(0)
    arr = rng.normal(size=1000)
    arr[:5] = 1e6
    assert "OUTLIERS" in detect_anomalies("x", arr)


def test_outliers_negative():
    rng = np.random.default_rng(0)
    arr = rng.normal(size=1000)
    assert "OUTLIERS" not in detect_anomalies("x", arr)


def test_monotonic_positive():
    arr = np.arange(100, dtype=np.float64)
    assert "MONOTONIC" in detect_anomalies("x", arr)


def test_monotonic_negative():
    rng = np.random.default_rng(0)
    arr = rng.normal(size=100)
    assert "MONOTONIC" not in detect_anomalies("x", arr)


def test_empty_positive():
    arr = np.array([], dtype=np.float64)
    assert "EMPTY" in detect_anomalies("x", arr)


def test_empty_negative():
    arr = np.array([1.0])
    assert "EMPTY" not in detect_anomalies("x", arr)


def test_object_dtype_positive():
    arr = np.array([{"a": 1}, [1, 2], "x"], dtype=object)
    assert "OBJECT_DTYPE" in detect_anomalies("x", arr)


def test_object_dtype_negative():
    arr = np.array([1.0, 2.0, 3.0])
    assert "OBJECT_DTYPE" not in detect_anomalies("x", arr)


def test_high_cardinality_positive():
    arr = np.arange(2000, dtype=np.int64)
    assert "HIGH_CARDINALITY" in detect_anomalies("x", arr)


def test_high_cardinality_negative():
    arr = np.array([1, 1, 2, 2, 3, 3] * 400)
    assert "HIGH_CARDINALITY" not in detect_anomalies("x", arr)


def test_mostly_null_positive():
    arr = np.array([np.nan] * 6 + [1.0] * 4)
    assert "MOSTLY_NULL" in detect_anomalies("x", arr)


def test_mostly_null_negative():
    arr = np.array([np.nan] * 2 + [1.0] * 8)
    assert "MOSTLY_NULL" not in detect_anomalies("x", arr)
