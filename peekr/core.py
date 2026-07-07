"""Core data model and orchestration for peekr."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class PeekrReadError(Exception):
    """Raised when a file cannot be read at all. Message is user-facing."""


class UnsupportedFormatError(Exception):
    """Raised when no reader is registered for a file's extension."""


@dataclass
class ArraySummary:
    name: str
    dtype: str
    shape: tuple
    n_total: int
    n_nan: int
    n_inf: int
    min: float | None
    max: float | None
    mean: float | None
    median: float | None
    std: float | None
    n_unique: int | None
    flags: list[str] = field(default_factory=list)


@dataclass
class FileReport:
    path: str
    format: str
    size_bytes: int
    n_items: int
    summaries: list[ArraySummary] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def peek(path: str | Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    """Inspect a single file. deep=True computes expensive stats
    (percentiles, unique counts on large arrays). max_rows caps how
    much of a tabular file is read (default: full file for < 100 MB,
    first 1M rows otherwise)."""
    from .readers import get_reader

    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise PeekrReadError(f"File not found: {p}")
    if not p.is_file():
        raise PeekrReadError(f"Not a file: {p}")

    reader = get_reader(p)
    try:
        return reader(p, deep=deep, max_rows=max_rows)
    except PeekrReadError:
        raise
    except Exception as exc:
        raise PeekrReadError(f"Failed to read {p.name}: {exc}") from exc


def peek_dir(path: str | Path, *, pattern: str = "*", recursive: bool = False) -> list[FileReport]:
    """Inspect every supported file in a directory."""
    from .readers import READERS

    base = Path(path).expanduser().resolve()
    if not base.is_dir():
        raise PeekrReadError(f"Not a directory: {base}")

    glob_fn = base.rglob if recursive else base.glob
    reports: list[FileReport] = []
    for candidate in sorted(glob_fn(pattern)):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in READERS:
            continue
        try:
            reports.append(peek(candidate))
        except PeekrReadError as exc:
            reports.append(
                FileReport(
                    path=str(candidate),
                    format=candidate.suffix.lstrip(".").lower(),
                    size_bytes=candidate.stat().st_size if candidate.exists() else 0,
                    n_items=0,
                    summaries=[],
                    metadata={},
                    errors=[str(exc)],
                )
            )
    return reports
