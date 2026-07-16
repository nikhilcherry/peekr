"""NPY reader: a single bare numpy array (no container), unlike .npz."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core import FileReport, PeekrReadError
from ..stats import summarize


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    errors: list[str] = []
    used_pickle = False

    try:
        arr = np.load(path, allow_pickle=False)
    except ValueError as exc:
        if "pickle" not in str(exc).lower():
            raise PeekrReadError(f"Failed to read npy file {path.name}: {exc}") from exc
        try:
            arr = np.load(path, allow_pickle=True)
            used_pickle = True
            errors.append(
                "File contains pickled objects; loaded with allow_pickle=True. "
                "Object-dtype arrays are flagged OBJECT_DTYPE."
            )
        except Exception as exc2:
            raise PeekrReadError(f"Failed to read npy file {path.name}: {exc2}") from exc2
    except Exception as exc:
        raise PeekrReadError(f"Failed to read npy file {path.name}: {exc}") from exc

    summary = summarize(path.stem, arr, deep=deep)

    return FileReport(
        path=str(path),
        format="npy",
        size_bytes=path.stat().st_size,
        n_items=1,
        summaries=[summary],
        metadata={"allow_pickle": used_pickle},
        errors=errors,
    )
