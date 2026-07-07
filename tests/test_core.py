"""Tests for peekr.core.peek and peek_dir orchestration."""
from __future__ import annotations

import numpy as np
import pytest

from peekr.core import PeekrReadError, UnsupportedFormatError, peek, peek_dir


def test_peek_missing_file_raises(tmp_path):
    with pytest.raises(PeekrReadError):
        peek(tmp_path / "nope.npz")


def test_peek_unsupported_extension_raises(tmp_path):
    bogus = tmp_path / "data.xyz"
    bogus.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        peek(bogus)


def test_peek_resolves_path(clean_npz):
    report = peek(str(clean_npz))
    assert report.path == str(clean_npz)


def test_peek_dir_finds_supported_files(tmp_path, clean_npz):
    (tmp_path / "ignore.txt").write_text("nope")
    reports = peek_dir(tmp_path)
    paths = {r.path for r in reports}
    assert str(clean_npz) in paths
    assert len(reports) == 1


def test_peek_dir_recursive(tmp_path, clean_npz):
    sub = tmp_path / "sub"
    sub.mkdir()
    nested = sub / "nested.npz"
    np.savez(nested, x=np.arange(10, dtype=np.float64))

    flat_reports = peek_dir(tmp_path, recursive=False)
    assert len(flat_reports) == 1

    recursive_reports = peek_dir(tmp_path, recursive=True)
    paths = {r.path for r in recursive_reports}
    assert str(nested) in paths
    assert str(clean_npz) in paths


def test_peek_dir_missing_dir_raises(tmp_path):
    with pytest.raises(PeekrReadError):
        peek_dir(tmp_path / "does_not_exist")


def test_peek_dir_pattern(tmp_path, clean_npz):
    (tmp_path / "other.csv").write_text("a,b\n1,2\n")
    reports = peek_dir(tmp_path, pattern="*.npz")
    assert len(reports) == 1
    assert reports[0].format == "npz"
