"""Tests for peekr.render.to_json."""
from __future__ import annotations

import json

import numpy as np

from peekr.core import peek
from peekr.render import to_json


def test_to_json_roundtrips_clean_array(tmp_path):
    path = tmp_path / "clean.npy"
    np.save(path, np.arange(10, dtype=np.float64))
    report = peek(path)

    payload = json.loads(to_json(report))
    assert payload["path"] == str(path)
    assert payload["summaries"][0]["min"] == 0.0
    assert payload["summaries"][0]["max"] == 9.0


def test_to_json_emits_spec_compliant_json_for_inf_stats(tmp_path):
    # min/max/mean/std can legitimately be inf/nan for a HAS_INF-flagged
    # array; json.dumps' default bare NaN/Infinity tokens aren't valid
    # JSON (RFC 8259) and would break strict parsers consuming --json
    # output. They must come out as null instead.
    path = tmp_path / "with_inf.npy"
    np.save(path, np.array([1.0, 2.0, np.inf, 3.0]))
    report = peek(path)

    text = to_json(report)
    assert "Infinity" not in text
    assert "NaN" not in text

    payload = json.loads(text)  # would still parse either way; the real check is the string above
    summary = payload["summaries"][0]
    assert summary["min"] == 1.0
    assert summary["max"] is None
    assert summary["mean"] is None
    assert summary["std"] is None
    assert "HAS_INF" in summary["flags"]


def test_to_json_handles_list_of_reports(tmp_path):
    path = tmp_path / "a.npy"
    np.save(path, np.arange(3, dtype=np.float64))
    report = peek(path)

    payload = json.loads(to_json([report, report]))
    assert len(payload) == 2
