"""Anomaly detection for a single array or tabular column.

Pure numpy, no I/O, no knowledge of file formats.
"""
from __future__ import annotations

import numpy as np

_UNIQUE_CAP = 1_000_000
_MAD_OUTLIER_MULT = 10
_OUTLIER_MIN_SIZE = 20
_OUTLIER_FRACTION = 0.001
_HIGH_CARDINALITY_MIN = 1000

# Informational flags describe the data rather than flagging a quality problem.
# They don't affect the CLI's clean/dirty exit code.
INFO_FLAGS = {"MONOTONIC", "HIGH_CARDINALITY"}


def _is_float_like(dtype: np.dtype) -> bool:
    return np.issubdtype(dtype, np.floating) or np.issubdtype(dtype, np.complexfloating)


def _object_null_mask(arr: np.ndarray) -> np.ndarray:
    def _isnull(x: object) -> bool:
        if x is None:
            return True
        if isinstance(x, float) and np.isnan(x):
            return True
        return False

    return np.fromiter((_isnull(x) for x in arr.ravel()), dtype=bool, count=arr.size)


def detect_anomalies(name: str, arr: "np.ndarray") -> list[str]:
    """Return a list of flag codes for one array/column."""
    flags: list[str] = []
    arr = np.asarray(arr)
    n_total = arr.size

    if n_total == 0:
        flags.append("EMPTY")
        return flags

    is_object = arr.dtype == object
    if is_object:
        flags.append("OBJECT_DTYPE")

    is_numeric = np.issubdtype(arr.dtype, np.number)
    is_complex = is_numeric and np.issubdtype(arr.dtype, np.complexfloating)
    is_float = is_numeric and _is_float_like(arr.dtype)
    is_real_numeric = is_numeric and not is_complex

    null_mask: np.ndarray | None = None
    n_null = 0
    if is_float:
        null_mask = np.isnan(arr)
        n_null = int(np.count_nonzero(null_mask))
        if n_null > 0:
            flags.append("HAS_NAN")
        if n_null == n_total:
            flags.append("ALL_NAN")
        if np.any(np.isinf(arr)):
            flags.append("HAS_INF")
    elif is_object:
        null_mask = _object_null_mask(arr)
        n_null = int(np.count_nonzero(null_mask))

    if n_null / n_total > 0.5:
        flags.append("MOSTLY_NULL")

    flat = arr.ravel()
    valid = flat[~null_mask.ravel()] if null_mask is not None else flat

    if valid.size >= 2:
        try:
            if np.all(valid == valid[0]):
                flags.append("CONSTANT")
        except Exception:
            pass

    has_inf_valid = is_float and bool(np.any(np.isinf(valid)))

    if is_real_numeric and not has_inf_valid and "CONSTANT" not in flags and valid.size >= 2:
        mean = float(np.mean(valid))
        std = float(np.std(valid))
        if mean != 0 and std < 1e-12 * abs(mean):
            flags.append("NEAR_CONSTANT")

    if is_real_numeric and not has_inf_valid and valid.size >= _OUTLIER_MIN_SIZE:
        median = float(np.median(valid))
        mad = float(np.median(np.abs(valid - median)))
        if mad > 0:
            dist = np.abs(valid - median)
            n_outliers = int(np.count_nonzero(dist > _MAD_OUTLIER_MULT * mad))
            if n_outliers / valid.size > _OUTLIER_FRACTION:
                flags.append("OUTLIERS")

    no_nulls = null_mask is None or not bool(null_mask.any())
    if is_real_numeric and arr.ndim == 1 and n_total >= 2 and no_nulls:
        diffs = np.diff(arr)
        if diffs.size > 0 and (bool(np.all(diffs > 0)) or bool(np.all(diffs < 0))):
            flags.append("MONOTONIC")

    # Only meaningful for 1-D columns (e.g. an ID column); a 2-D image trivially
    # has all-unique float values and isn't an "ID" in any useful sense.
    if arr.ndim == 1 and _HIGH_CARDINALITY_MIN < n_total <= _UNIQUE_CAP:
        try:
            n_unique = int(np.unique(flat).size)
            if n_unique == n_total:
                flags.append("HIGH_CARDINALITY")
        except Exception:
            pass

    return flags
