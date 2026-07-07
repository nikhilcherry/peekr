"""Rendering of FileReports: rich tables (degrading to plain text off a TTY) and JSON."""
from __future__ import annotations

import dataclasses
import json
import sys
from typing import Any

import numpy as np
from rich import box
from rich.console import Console
from rich.table import Table

from .anomalies import INFO_FLAGS
from .core import FileReport

_DATA_QUALITY_STYLE = "red"
_INFO_STYLE = "dim"


def make_console(*, wide: bool = False) -> Console:
    """Build the output console. When stdout isn't a TTY, rich falls back to
    an 80-column width by default, which truncates names/flags aggressively.
    Widen that fallback so piped output (files, CI logs) stays readable."""
    width = None
    if not sys.stdout.isatty():
        width = 200 if wide else 120
    elif wide:
        width = 200
    return Console(file=sys.stdout, width=width)


def _flag_text(flags: list[str]) -> str:
    parts = []
    for flag in flags:
        style = _INFO_STYLE if flag in INFO_FLAGS else _DATA_QUALITY_STYLE
        parts.append(f"[{style}]{flag}[/{style}]")
    return " ".join(parts)


def _fmt_num(value: float | None) -> str:
    if value is None:
        return "-"
    if value != 0 and (abs(value) >= 1e5 or abs(value) < 1e-4):
        return f"{value:.3e}"
    return f"{value:.4g}"


def flag_count(report: FileReport, *, exclude_info: bool = False) -> int:
    total = 0
    for s in report.summaries:
        for flag in s.flags:
            if exclude_info and flag in INFO_FLAGS:
                continue
            total += 1
    return total


def render_file_report(report: FileReport, console: Console | None = None) -> None:
    console = console or make_console()
    use_box = box.SQUARE if console.is_terminal else None

    console.print(
        f"[bold]{report.path}[/bold]  ({report.format}, {report.size_bytes:,} bytes, {report.n_items} items)"
    )
    for err in report.errors:
        console.print(f"[yellow]! {err}[/yellow]")

    if not report.summaries:
        return

    table = Table(box=use_box, show_lines=False)
    table.add_column("name", overflow="fold")
    table.add_column("dtype")
    table.add_column("shape")
    table.add_column("min", justify="right")
    table.add_column("median", justify="right")
    table.add_column("max", justify="right")
    table.add_column("%nan", justify="right")
    table.add_column("flags", overflow="fold")

    for s in report.summaries:
        pct_nan = f"{(s.n_nan / s.n_total * 100):.1f}" if s.n_total else "-"
        table.add_row(
            s.name,
            s.dtype,
            str(s.shape),
            _fmt_num(s.min),
            _fmt_num(s.median),
            _fmt_num(s.max),
            pct_nan,
            _flag_text(s.flags),
        )

    console.print(table)


def render_dir_summary(reports: list[FileReport], console: Console | None = None) -> None:
    console = console or make_console()
    use_box = box.SQUARE if console.is_terminal else None

    table = Table(box=use_box, show_lines=False, title="peekr directory summary")
    table.add_column("path", overflow="fold")
    table.add_column("format")
    table.add_column("size", justify="right")
    table.add_column("items", justify="right")
    table.add_column("flags", justify="right")

    for r in reports:
        n_flags = flag_count(r)
        row_style = "red" if n_flags else None
        table.add_row(r.path, r.format, f"{r.size_bytes:,}", str(r.n_items), str(n_flags), style=row_style)

    console.print(table)

    flagged = [r for r in reports if flag_count(r) > 0 or r.errors]
    for r in flagged:
        console.print()
        render_file_report(r, console)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _sanitize(value.tolist())
    return value


def to_json(reports: list[FileReport] | FileReport) -> str:
    """Pure json.dumps of dataclasses via dataclasses.asdict, no rich markup."""
    if isinstance(reports, FileReport):
        data: Any = dataclasses.asdict(reports)
    else:
        data = [dataclasses.asdict(r) for r in reports]
    return json.dumps(_sanitize(data), indent=2)
