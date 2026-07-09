"""Parquet reader."""
from __future__ import annotations

from pathlib import Path

from ..core import ArraySummary, FileReport, PeekrReadError
from ..stats import summarize


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise PeekrReadError(
            'Parquet support requires: pip install "peekr[parquet] @ git+https://github.com/nikhilcherry/peekr"'
        ) from None

    errors: list[str] = []
    metadata: dict = {}

    try:
        pf = pq.ParquetFile(path)
        metadata["n_row_groups"] = pf.num_row_groups
        try:
            if pf.num_row_groups > 0:
                metadata["compression"] = pf.metadata.row_group(0).column(0).compression
        except Exception:
            pass

        if max_rows is not None and pf.num_row_groups > 0:
            tables = []
            total = 0
            for i in range(pf.num_row_groups):
                tables.append(pf.read_row_group(i))
                total += tables[-1].num_rows
                if total >= max_rows:
                    break
            table = pa.concat_tables(tables) if len(tables) > 1 else tables[0]
            df = table.to_pandas()
            if len(df) > max_rows:
                df = df.iloc[:max_rows]
        else:
            df = pf.read().to_pandas()
    except Exception as exc:
        raise PeekrReadError(f"Failed to read parquet file {path.name}: {exc}") from exc

    summaries: list[ArraySummary] = [
        summarize(str(col), df[col].to_numpy(), deep=deep) for col in df.columns
    ]

    return FileReport(
        path=str(path),
        format="parquet",
        size_bytes=path.stat().st_size,
        n_items=len(summaries),
        summaries=summaries,
        metadata=metadata,
        errors=errors,
    )
