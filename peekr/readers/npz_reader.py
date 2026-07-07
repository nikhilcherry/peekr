"""NPZ reader."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core import FileReport, PeekrReadError
from ..stats import summarize


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    errors: list[str] = []
    used_pickle = False

    # np.load() is lazy for .npz: a pickled object array only raises when a
    # key is actually accessed, not at load time. Read all keys eagerly so
    # the pickle-required error surfaces here and we can retry.
    try:
        with np.load(path, allow_pickle=False) as npz:
            arrays = {key: npz[key] for key in npz.files}
    except ValueError as exc:
        if "pickle" not in str(exc).lower():
            raise PeekrReadError(f"Failed to read npz file {path.name}: {exc}") from exc
        try:
            with np.load(path, allow_pickle=True) as npz:
                arrays = {key: npz[key] for key in npz.files}
            used_pickle = True
            errors.append(
                "File contains pickled objects; loaded with allow_pickle=True. "
                "Object-dtype arrays are flagged OBJECT_DTYPE."
            )
        except Exception as exc2:
            raise PeekrReadError(f"Failed to read npz file {path.name}: {exc2}") from exc2
    except Exception as exc:
        raise PeekrReadError(f"Failed to read npz file {path.name}: {exc}") from exc

    summaries = [summarize(key, arr, deep=deep) for key, arr in arrays.items()]

    return FileReport(
        path=str(path),
        format="npz",
        size_bytes=path.stat().st_size,
        n_items=len(summaries),
        summaries=summaries,
        metadata={"allow_pickle": used_pickle},
        errors=errors,
    )
