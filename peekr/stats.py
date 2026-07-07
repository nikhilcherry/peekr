"""Per-array/column summary statistics, combined into an ArraySummary."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .anomalies import detect_anomalies

if TYPE_CHECKING:
    from .core import ArraySummary

_UNIQUE_CAP = 1_000_000


def summarize(name: str, arr: "np.ndarray", *, deep: bool = False) -> "ArraySummary":
    """Compute an ArraySummary for one array/column. NaN-aware, no RuntimeWarnings."""
    from .core import ArraySummary  # local import avoids circular dependency at module load

    arr = np.asarray(arr)
    n_total = int(arr.size)
    is_numeric = np.issubdtype(arr.dtype, np.number)
    is_complex = is_numeric and np.issubdtype(arr.dtype, np.complexfloating)
    is_float = is_numeric and (np.issubdtype(arr.dtype, np.floating) or is_complex)

    n_nan = 0
    n_inf = 0
    if is_float:
        nan_mask = np.isnan(arr)
        n_nan = int(np.count_nonzero(nan_mask))
        n_inf = int(np.count_nonzero(np.isinf(arr)))

    min_v = max_v = mean_v = median_v = std_v = None
    if is_numeric and not is_complex and n_total > 0:
        all_nan = is_float and n_nan == n_total
        if not all_nan:
            with np.errstate(all="ignore"):
                if is_float:
                    min_v = float(np.nanmin(arr))
                    max_v = float(np.nanmax(arr))
                    mean_v = float(np.nanmean(arr))
                    median_v = float(np.nanmedian(arr))
                    std_v = float(np.nanstd(arr))
                else:
                    min_v = float(np.min(arr))
                    max_v = float(np.max(arr))
                    mean_v = float(np.mean(arr))
                    median_v = float(np.median(arr))
                    std_v = float(np.std(arr))

    n_unique = None
    if n_total > 0 and (deep or n_total <= _UNIQUE_CAP):
        try:
            n_unique = int(np.unique(arr.ravel()).size)
        except Exception:
            n_unique = None

    flags = detect_anomalies(name, arr)

    return ArraySummary(
        name=name,
        dtype=str(arr.dtype),
        shape=tuple(arr.shape),
        n_total=n_total,
        n_nan=n_nan,
        n_inf=n_inf,
        min=min_v,
        max=max_v,
        mean=mean_v,
        median=median_v,
        std=std_v,
        n_unique=n_unique,
        flags=flags,
    )
