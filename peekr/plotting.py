"""Quick-look PNG plots for a FileReport. matplotlib Agg backend, never opens a window."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .core import FileReport, PeekrReadError

_MAX_HEATMAP_DIM = 4096
_MAX_HIST_COLUMNS = 12
_MAX_PLOT_ELEMENTS = 5_000_000


def _load_named_arrays(report: FileReport) -> dict[str, np.ndarray]:
    """Best-effort re-load of raw arrays named in report.summaries for plotting."""
    path = Path(report.path)
    fmt = report.format
    arrays: dict[str, np.ndarray] = {}

    try:
        if fmt == "npz":
            npz = np.load(path, allow_pickle=True)
            try:
                for s in report.summaries:
                    if s.name in npz.files:
                        arrays[s.name] = np.asarray(npz[s.name])
            finally:
                npz.close()
        elif fmt == "csv":
            import pandas as pd

            df = pd.read_csv(path, low_memory=False)
            for s in report.summaries:
                if s.name in df.columns:
                    arrays[s.name] = df[s.name].to_numpy()
        elif fmt == "parquet":
            import pandas as pd

            df = pd.read_parquet(path)
            for s in report.summaries:
                if s.name in df.columns:
                    arrays[s.name] = df[s.name].to_numpy()
        elif fmt == "fits":
            from astropy.io import fits

            with fits.open(path, memmap=True) as hdul:
                for s in report.summaries:
                    if ":" in s.name:
                        idx = int(s.name.split(":", 1)[0][3:])
                        arrays[s.name] = np.asarray(hdul[idx].data)
                    elif "." in s.name:
                        hdu_part, col = s.name.split(".", 1)
                        idx = int(hdu_part[3:])
                        arrays[s.name] = np.asarray(hdul[idx].data[col])
        elif fmt == "h5":
            import h5py

            with h5py.File(path, "r") as f:
                for s in report.summaries:
                    name = s.name[:-len(" (sampled)")] if s.name.endswith(" (sampled)") else s.name
                    name = name.lstrip("/")
                    if name in f and isinstance(f[name], h5py.Dataset):
                        ds = f[name]
                        if ds.size <= _MAX_PLOT_ELEMENTS:
                            arrays[s.name] = np.asarray(ds[...])
    except Exception:
        pass

    return arrays


def _finite(arr: np.ndarray) -> np.ndarray:
    if np.issubdtype(arr.dtype, np.floating):
        return arr[np.isfinite(arr)]
    return arr


def _plot_1d(plt, arr: np.ndarray, name: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.arange(arr.size), arr, linewidth=0.8)
    ax.set_title(name)
    ax.set_xlabel("index")
    ax.set_ylabel("value")

    finite = _finite(arr)
    if finite.size > 0:
        inset = ax.inset_axes([0.68, 0.65, 0.28, 0.28])
        inset.hist(finite, bins=30, color="gray")
        inset.set_xticks([])
        inset.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _plot_heatmap(plt, arr: np.ndarray, name: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(arr, aspect="auto", cmap="viridis")
    ax.set_title(name)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _plot_hist_grid(plt, cols: dict[str, np.ndarray], out_path: Path) -> None:
    names = list(cols)[:_MAX_HIST_COLUMNS]
    n = len(names)
    ncols = min(4, n)
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), squeeze=False)
    axes = axes.ravel()
    for ax, name in zip(axes, names):
        finite = _finite(cols[name])
        if finite.size > 0:
            ax.hist(finite, bins=30, color="steelblue")
        ax.set_title(name, fontsize=9)
    for ax in axes[len(names):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def generate_plot(report: FileReport, *, plot_dir: str | Path | None = None) -> Path | None:
    """Render one quick-look PNG for a FileReport. Returns the output path, or
    None if the report has nothing plottable."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise PeekrReadError(
            'Plotting requires: pip install "peekr[plot] @ git+https://github.com/nikhilcherry/peekr"'
        ) from None

    arrays = _load_named_arrays(report)
    numeric = [s for s in report.summaries if s.min is not None and s.name in arrays]
    if not numeric:
        return None

    src_path = Path(report.path)
    out_dir = Path(plot_dir).expanduser().resolve() if plot_dir is not None else src_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{src_path.stem}.peekr.png"

    tabular = report.format in ("csv", "parquet")

    if not tabular and len(numeric) == 1:
        arr = arrays[numeric[0].name]
        if arr.ndim == 1:
            _plot_1d(plt, arr, numeric[0].name, out_path)
            return out_path
        if arr.ndim == 2 and arr.shape[0] <= _MAX_HEATMAP_DIM and arr.shape[1] <= _MAX_HEATMAP_DIM:
            _plot_heatmap(plt, arr, numeric[0].name, out_path)
            return out_path
        return None

    cols = {s.name: arrays[s.name] for s in numeric if arrays[s.name].ndim == 1}
    if cols:
        _plot_hist_grid(plt, cols, out_path)
        return out_path
    return None
