"""Tests for individual format readers via peekr.core.peek."""
from __future__ import annotations

import builtins

import numpy as np
import pytest

from peekr.core import PeekrReadError, peek


def test_npz_reader(clean_npz):
    report = peek(clean_npz)
    assert report.format == "npz"
    assert report.n_items == 3
    names = {s.name for s in report.summaries}
    assert names == {"a", "b", "c"}
    by_name = {s.name: s for s in report.summaries}
    assert by_name["a"].shape == (100,)
    assert by_name["c"].dtype == "int64"


def test_npz_reader_pickled_objects(dirty_npz):
    report = peek(dirty_npz)
    assert report.metadata["allow_pickle"] is True
    obj_summary = next(s for s in report.summaries if s.name == "obj_arr")
    assert "OBJECT_DTYPE" in obj_summary.flags


def test_npz_truncated_raises(truncated_npz):
    with pytest.raises(PeekrReadError):
        peek(truncated_npz)


def test_csv_reader(table_csv):
    report = peek(table_csv)
    assert report.format == "csv"
    names = {s.name for s in report.summaries}
    assert {"id", "value", "mostly_null", "category"} <= names
    mostly_null = next(s for s in report.summaries if s.name == "mostly_null")
    assert "MOSTLY_NULL" in mostly_null.flags
    assert report.metadata["delimiter"] == ","


def test_fits_image_reader(image_fits):
    report = peek(image_fits)
    assert report.format == "fits"
    assert report.n_items == 1
    assert report.summaries[0].shape == (20, 30)
    assert "header" in report.metadata
    assert report.metadata["header"].get("OBSERVER") == "peekr-test"


def test_fits_bintable_reader(bintable_fits):
    report = peek(bintable_fits)
    assert report.format == "fits"
    names = {s.name for s in report.summaries}
    assert any(n.endswith(".flux") for n in names)
    assert any(n.endswith(".id") for n in names)


def test_h5_reader(data_h5):
    report = peek(data_h5)
    assert report.format == "h5"
    names = {s.name for s in report.summaries}
    assert "/flat" in names
    assert "/group1/subgroup/nested" in names
    assert report.metadata["attrs"]["created_by"] == "peekr-test"


def test_parquet_reader(data_parquet):
    report = peek(data_parquet)
    assert report.format == "parquet"
    names = {s.name for s in report.summaries}
    assert names == {"x", "y"}
    assert report.n_items == 2


def test_fits_missing_dependency_message(monkeypatch, tmp_path):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "astropy" or name.startswith("astropy."):
            raise ImportError("mocked missing astropy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    fake_fits = tmp_path / "fake.fits"
    fake_fits.write_bytes(b"not a real fits file")

    with pytest.raises(PeekrReadError, match=r"FITS support requires: pip install peekr\[fits\]"):
        peek(fake_fits)
