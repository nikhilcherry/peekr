"""HDF5 reader."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core import ArraySummary, FileReport, PeekrReadError
from ..stats import summarize

_MAX_BYTES = 500 * 1024 * 1024
_SAMPLE_ELEMENTS = 1_000_000


def _stringify(value: object) -> object:
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    try:
        import h5py
    except ImportError:
        raise PeekrReadError(
            'HDF5 support requires: pip install "peekr[h5] @ git+https://github.com/nikhilcherry/peekr"'
        ) from None

    errors: list[str] = []
    summaries: list[ArraySummary] = []
    root_attrs: dict = {}

    try:
        with h5py.File(path, "r") as f:
            root_attrs = {k: _stringify(v) for k, v in f.attrs.items()}

            def visit(name: str, obj: object) -> None:
                if not isinstance(obj, h5py.Dataset):
                    return
                full_name = f"/{name}"

                if obj.ndim == 0:
                    try:
                        arr = np.asarray(obj[()])
                        summaries.append(summarize(full_name, arr, deep=deep))
                    except Exception as exc:
                        errors.append(f"{full_name}: failed to read dataset ({exc})")
                    return

                try:
                    nbytes = obj.size * obj.dtype.itemsize
                except Exception:
                    nbytes = 0

                if nbytes > _MAX_BYTES:
                    try:
                        row_size = int(np.prod(obj.shape[1:])) if obj.ndim > 1 else 1
                        row_size = max(row_size, 1)
                        n_rows = max(1, min(obj.shape[0], _SAMPLE_ELEMENTS // row_size))
                        arr = np.asarray(obj[:n_rows]).ravel()[:_SAMPLE_ELEMENTS]
                        summaries.append(summarize(f"{full_name} (sampled)", arr, deep=deep))
                    except Exception as exc:
                        errors.append(f"{full_name}: failed to sample dataset ({exc})")
                else:
                    try:
                        arr = np.asarray(obj[...])
                        summaries.append(summarize(full_name, arr, deep=deep))
                    except Exception as exc:
                        errors.append(f"{full_name}: failed to read dataset ({exc})")

            f.visititems(visit)
    except PeekrReadError:
        raise
    except Exception as exc:
        raise PeekrReadError(f"Failed to read HDF5 file {path.name}: {exc}") from exc

    return FileReport(
        path=str(path),
        format="h5",
        size_bytes=path.stat().st_size,
        n_items=len(summaries),
        summaries=summaries,
        metadata={"attrs": root_attrs},
        errors=errors,
    )
