"""CSV reader."""
from __future__ import annotations

import csv
from pathlib import Path

from ..core import ArraySummary, FileReport, PeekrReadError
from ..stats import summarize


def _read_sample(path: Path, encoding: str) -> str:
    with open(path, "r", encoding=encoding, errors="strict") as f:
        return f.read(65536)


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        return ","


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    try:
        import pandas as pd
    except ImportError:
        raise PeekrReadError("CSV support requires: pip install peekr[csv]") from None

    errors: list[str] = []
    encoding = "utf-8"
    try:
        sample = _read_sample(path, encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
        errors.append("File is not valid UTF-8; decoded as latin-1.")
        try:
            sample = _read_sample(path, encoding)
        except Exception as exc:
            raise PeekrReadError(f"Failed to read CSV file {path.name}: {exc}") from exc

    delimiter = _sniff_delimiter(sample)

    try:
        df = pd.read_csv(path, sep=delimiter, low_memory=False, encoding=encoding, nrows=max_rows)
    except Exception as exc:
        raise PeekrReadError(f"Failed to read CSV file {path.name}: {exc}") from exc

    summaries: list[ArraySummary] = [
        summarize(str(col), df[col].to_numpy(), deep=deep) for col in df.columns
    ]

    return FileReport(
        path=str(path),
        format="csv",
        size_bytes=path.stat().st_size,
        n_items=len(summaries),
        summaries=summaries,
        metadata={"delimiter": delimiter, "encoding": encoding},
        errors=errors,
    )
