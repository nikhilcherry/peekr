"""CLI integration tests, run via subprocess from a directory outside the repo."""
from __future__ import annotations

import json
import subprocess
import sys


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "peekr", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_version(tmp_path):
    result = _run(["--version"], cwd=tmp_path)
    assert result.returncode == 0
    assert "peekr" in result.stdout


def test_cli_clean_exit_zero(clean_npz, tmp_path):
    result = _run([str(clean_npz)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_cli_dirty_exit_one(dirty_npz, tmp_path):
    result = _run([str(dirty_npz)], cwd=tmp_path)
    assert result.returncode == 1, result.stderr


def test_cli_missing_file_exit_two(tmp_path):
    result = _run([str(tmp_path / "does_not_exist.npz")], cwd=tmp_path)
    assert result.returncode == 2


def test_cli_unsupported_format_exit_two(tmp_path):
    bogus = tmp_path / "data.xyz"
    bogus.write_text("hello")
    result = _run([str(bogus)], cwd=tmp_path)
    assert result.returncode == 2


def test_cli_json_roundtrip(clean_npz, tmp_path):
    result = _run([str(clean_npz), "--json"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["format"] == "npz"
    assert len(data["summaries"]) == 3


def test_cli_runs_from_unrelated_cwd(clean_npz, tmp_path):
    other_cwd = tmp_path / "somewhere_else"
    other_cwd.mkdir()
    result = _run([str(clean_npz)], cwd=other_cwd)
    assert result.returncode == 0, result.stderr


def test_cli_directory_mode_does_not_crash(tmp_path, clean_npz):
    (tmp_path / "not_a_data_file.txt").write_text("hello")
    result = _run([str(tmp_path)], cwd=tmp_path)
    assert result.returncode in (0, 1), result.stderr


def test_cli_key_filter(clean_npz, tmp_path):
    result = _run([str(clean_npz), "--key", "a", "--json"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert [s["name"] for s in data["summaries"]] == ["a"]


def test_cli_key_filter_typo_warns_instead_of_silent_empty_report(clean_npz, tmp_path):
    # A --key that matches nothing (a likely typo, e.g. "flux" vs "flx")
    # previously produced a silently "clean" 0-item report at exit 0,
    # indistinguishable from a genuinely empty file.
    result = _run([str(clean_npz), "--key", "nonexistent_column"], cwd=tmp_path)
    assert result.returncode == 0
    assert "matched nothing" in result.stderr
    assert "nonexistent_column" in result.stderr
    assert "a" in result.stderr and "b" in result.stderr and "c" in result.stderr


def test_cli_key_filter_valid_key_has_no_warning(clean_npz, tmp_path):
    result = _run([str(clean_npz), "--key", "a"], cwd=tmp_path)
    assert result.returncode == 0
    assert "matched nothing" not in result.stderr


def test_cli_no_anomalies(dirty_npz, tmp_path):
    result = _run([str(dirty_npz), "--no-anomalies", "--json"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert all(s["flags"] == [] for s in data["summaries"])
