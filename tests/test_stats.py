"""Tests for peekr.stats.summarize."""
from __future__ import annotations

import warnings

import numpy as np

from peekr.stats import summarize


def test_summarize_basic_numeric():
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    s = summarize("x", arr)
    assert s.name == "x"
    assert s.n_total == 5
    assert s.n_nan == 0
    assert s.min == 1.0
    assert s.max == 5.0
    assert s.mean == 3.0
    assert s.median == 3.0
    assert s.n_unique == 5


def test_summarize_all_nan_no_warning():
    arr = np.full(10, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        s = summarize("x", arr)
    assert s.min is None
    assert s.max is None
    assert s.mean is None
    assert "ALL_NAN" in s.flags


def test_summarize_partial_nan_no_warning():
    arr = np.array([1.0, np.nan, 3.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        s = summarize("x", arr)
    assert s.n_nan == 1
    assert s.mean == 2.0


def test_summarize_non_numeric():
    arr = np.array(["a", "b", "c"])
    s = summarize("x", arr)
    assert s.min is None
    assert s.max is None
    assert s.n_unique == 3


def test_summarize_deep_unique_large_array():
    arr = np.arange(5, dtype=np.int64).repeat(300_000)
    s = summarize("x", arr, deep=False)
    assert s.n_unique is None
    s_deep = summarize("x", arr, deep=True)
    assert s_deep.n_unique == 5


def test_summarize_normalizes_byte_order():
    arr = np.array([1.0, 2.0, 3.0], dtype=">f8")
    s = summarize("x", arr)
    assert s.dtype == "float64"

    arr_int = np.array([1, 2, 3], dtype=">i4")
    s_int = summarize("x", arr_int)
    assert s_int.dtype == "int32"


def test_summarize_string_dtype_unchanged():
    arr = np.array(["a", "bb", "ccc"], dtype="<U10")
    s = summarize("x", arr)
    assert s.dtype == "<U10"


def test_summarize_empty_array():
    arr = np.array([], dtype=np.float64)
    s = summarize("x", arr)
    assert s.n_total == 0
    assert s.min is None
    assert "EMPTY" in s.flags
