"""Reader registry: file extension -> read(path, *, deep, max_rows) -> FileReport.

Each reader module lazily imports its optional dependency inside `read()`
so that importing this package never fails when optional extras are absent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..core import FileReport, UnsupportedFormatError
from . import csv_reader, fits_reader, h5_reader, npy_reader, npz_reader, parquet_reader

READERS: dict[str, Callable[..., FileReport]] = {
    ".npy": npy_reader.read,
    ".npz": npz_reader.read,
    ".fits": fits_reader.read,
    ".fit": fits_reader.read,
    ".csv": csv_reader.read,
    ".parquet": parquet_reader.read,
    ".h5": h5_reader.read,
    ".hdf5": h5_reader.read,
}


def get_reader(path: Path) -> Callable[..., FileReport]:
    """Resolve by extension (case-insensitive). Raise UnsupportedFormatError
    with a message listing supported extensions."""
    ext = path.suffix.lower()
    try:
        return READERS[ext]
    except KeyError:
        supported = ", ".join(sorted(READERS))
        raise UnsupportedFormatError(
            f"Unsupported file extension '{ext or path.name}'. Supported extensions: {supported}"
        ) from None
