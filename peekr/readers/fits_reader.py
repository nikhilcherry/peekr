"""FITS reader."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core import ArraySummary, FileReport, PeekrReadError
from ..stats import summarize


def read(path: Path, *, deep: bool = False, max_rows: int | None = None) -> FileReport:
    try:
        from astropy.io import fits
    except ImportError:
        raise PeekrReadError(
            'FITS support requires: pip install "peekr[fits] @ git+https://github.com/nikhilcherry/peekr"'
        ) from None

    errors: list[str] = []
    summaries: list[ArraySummary] = []
    header_cards: dict[str, str] = {}

    try:
        with fits.open(path, memmap=True) as hdul:
            for i, hdu in enumerate(hdul):
                hdu_name = hdu.name or "PRIMARY"
                if i == 0:
                    for card in hdu.header.cards:
                        if card.keyword:
                            header_cards[str(card.keyword)] = str(card.value)

                data = hdu.data
                if data is None:
                    continue

                if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    for colname in data.dtype.names:
                        try:
                            col = np.asarray(data[colname])
                        except Exception as exc:
                            errors.append(f"HDU{i}.{colname}: failed to read column ({exc})")
                            continue
                        summaries.append(summarize(f"HDU{i}.{colname}", col, deep=deep))
                else:
                    try:
                        arr = np.asarray(data)
                    except Exception as exc:
                        errors.append(f"HDU{i}:{hdu_name}: failed to read data ({exc})")
                        continue
                    summaries.append(summarize(f"HDU{i}:{hdu_name}", arr, deep=deep))
    except PeekrReadError:
        raise
    except Exception as exc:
        raise PeekrReadError(f"Failed to read FITS file {path.name}: {exc}") from exc

    return FileReport(
        path=str(path),
        format="fits",
        size_bytes=path.stat().st_size,
        n_items=len(summaries),
        summaries=summaries,
        metadata={"header": header_cards},
        errors=errors,
    )
