"""Command-line interface for peekr."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import FileReport, PeekrReadError, UnsupportedFormatError, peek, peek_dir
from .render import flag_count, make_console, render_dir_summary, render_file_report, to_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="peekr",
        description="Universal scientific data file explorer.",
    )
    parser.add_argument("path", help="File or directory to inspect")
    parser.add_argument(
        "--deep", action="store_true", help="Compute expensive stats (percentiles, unique counts)"
    )
    parser.add_argument("--plot", action="store_true", help="Save a quick-look PNG next to each file")
    parser.add_argument(
        "--plot-dir", metavar="DIR", default=None, help="Save PNGs to DIR instead of next to the file"
    )
    parser.add_argument("--json", action="store_true", help="Emit FileReport(s) as JSON to stdout")
    parser.add_argument(
        "--key",
        metavar="NAME",
        action="append",
        default=None,
        help="Only inspect this array/column/dataset (repeatable)",
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories")
    parser.add_argument(
        "--max-rows", type=int, default=None, metavar="N", help="Cap rows read from tabular files"
    )
    parser.add_argument("--no-anomalies", action="store_true", help="Skip anomaly detection")
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Use a wider table layout; reduces name/flag truncation, useful when piping output",
    )
    parser.add_argument("--version", action="version", version=f"peekr {__version__}")
    return parser


def _apply_key_filter(report: FileReport, keys: list[str] | None, err_console) -> None:
    if not keys:
        return
    key_set = set(keys)
    matched = [s for s in report.summaries if s.name in key_set]
    unmatched = key_set - {s.name for s in matched}
    if unmatched and report.summaries:
        # A --key that matches nothing (a likely typo) previously produced
        # a silently "clean" 0-item report at exit 0, indistinguishable
        # from a genuinely empty file -- surface it instead.
        available = ", ".join(sorted(s.name for s in report.summaries))
        err_console.print(
            f"[yellow]! --key {sorted(unmatched)} matched nothing in {report.path} "
            f"(available: {available})[/yellow]"
        )
    report.summaries = matched
    report.n_items = len(report.summaries)


def _apply_no_anomalies(report: FileReport) -> None:
    for s in report.summaries:
        s.flags = []


def _postprocess(report: FileReport, args: argparse.Namespace, err_console) -> None:
    _apply_key_filter(report, args.key, err_console)
    if args.no_anomalies:
        _apply_no_anomalies(report)


def _maybe_plot(report: FileReport, args: argparse.Namespace, err_console) -> None:
    if not args.plot:
        return
    from .plotting import generate_plot

    try:
        out = generate_plot(report, plot_dir=args.plot_dir)
    except PeekrReadError as exc:
        err_console.print(f"[yellow]! {exc}[/yellow]")
        return
    if out is not None:
        err_console.print(f"[dim]Saved plot: {out}[/dim]")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    console = make_console(wide=args.wide)
    from rich.console import Console

    err_console = Console(file=sys.stderr)

    target = Path(args.path).expanduser().resolve()

    try:
        if target.is_dir():
            reports = peek_dir(
                target, recursive=args.recursive, deep=args.deep, max_rows=args.max_rows
            )
            for r in reports:
                _postprocess(r, args, err_console)
                _maybe_plot(r, args, err_console)

            if args.json:
                print(to_json(reports))
            else:
                render_dir_summary(reports, console)

            total_flags = sum(flag_count(r, exclude_info=True) for r in reports)
            return 1 if total_flags > 0 else 0

        report = peek(target, deep=args.deep, max_rows=args.max_rows)
        _postprocess(report, args, err_console)
        _maybe_plot(report, args, err_console)

        if args.json:
            print(to_json(report))
        else:
            render_file_report(report, console)

        n_flags = flag_count(report, exclude_info=True)
        return 1 if n_flags > 0 else 0

    except (PeekrReadError, UnsupportedFormatError) as exc:
        print(f"peekr: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"peekr: unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
