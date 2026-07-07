# peekr

A universal scientific data file explorer for the command line.

Point `peekr` at any `.npz`, `.fits`, `.csv`, `.parquet`, or `.h5` file (or a
directory of them) and it instantly shows you what's inside: structure,
stats, quick plots, and automatic anomaly flags (NaNs, constant columns,
outliers, suspicious dtypes) — `ls` + `head` + `describe()` + "is this file
sane?" in one command, without opening a notebook.

## Install

```bash
pip install git+https://github.com/nikhilcherry/peekr
```

With optional format/plotting support:

```bash
pip install "peekr[fits] @ git+https://github.com/nikhilcherry/peekr"
pip install "peekr[csv] @ git+https://github.com/nikhilcherry/peekr"
pip install "peekr[parquet] @ git+https://github.com/nikhilcherry/peekr"
pip install "peekr[h5] @ git+https://github.com/nikhilcherry/peekr"
pip install "peekr[plot] @ git+https://github.com/nikhilcherry/peekr"

# everything
pip install "peekr[all] @ git+https://github.com/nikhilcherry/peekr"
```

## Usage

### Inspect a single file

```bash
$ peekr experiment.npz
```

```
experiment.npz  (npz, 84213 bytes, 3 items)
┌────────┬─────────┬───────────┬─────────┬─────────┬─────────┬──────┬─────────┐
│ name   │ dtype   │ shape     │     min │  median │     max │ %nan │ flags   │
├────────┼─────────┼───────────┼─────────┼─────────┼─────────┼──────┼─────────┤
│ good   │ float64 │ (1000,)   │  -3.482 │ -0.0224 │   3.291 │  0.0 │         │
│ bad    │ float64 │ (50,)     │     nan │     nan │     nan │100.0 │ ALL_NAN │
│ ids    │ int64   │ (1000,)   │     0.0 │   499.5 │   999.0 │  0.0 │         │
└────────┴─────────┴───────────┴─────────┴─────────┴─────────┴──────┴─────────┘
```

### Machine-readable output for CI

```bash
$ peekr experiment.npz --json | python -m json.tool
```

```json
{
  "path": "/data/experiment.npz",
  "format": "npz",
  "size_bytes": 84213,
  "n_items": 3,
  "summaries": [
    {
      "name": "bad",
      "dtype": "float64",
      "shape": [50],
      "n_total": 50,
      "n_nan": 50,
      "n_inf": 0,
      "min": null,
      "max": null,
      "mean": null,
      "median": null,
      "std": null,
      "n_unique": 1,
      "flags": ["ALL_NAN"]
    }
  ],
  "metadata": { "allow_pickle": false },
  "errors": []
}
```

`peekr` exits non-zero when data-quality flags are found, so it drops
straight into a CI pipeline as a data-quality gate:

```bash
peekr data/*.parquet || exit 1
```

### Scan a whole directory

```bash
$ peekr ./data -r
```

```
                 peekr directory summary
┌───────────────────────┬─────────┬────────┬───────┬───────┐
│ path                   │ format  │   size │ items │ flags │
├───────────────────────┼─────────┼────────┼───────┼───────┤
│ ./data/run1.npz        │ npz     │  84213 │     3 │     1 │
│ ./data/run2.csv        │ csv     │  12044 │     5 │     0 │
│ ./data/calib.fits      │ fits    │ 921600 │     2 │     0 │
└───────────────────────┴─────────┴────────┴───────┴───────┘

./data/run1.npz  (npz, 84213 bytes, 3 items)
┌──────┬─────────┬─────────┬──────┬─────────┬──────┬──────┬─────────┐
│ name │ dtype   │ shape   │  min │  median │  max │ %nan │ flags   │
├──────┼─────────┼─────────┼──────┼─────────┼──────┼──────┼─────────┤
│ bad  │ float64 │ (50,)   │  nan │     nan │  nan │100.0 │ ALL_NAN │
└──────┴─────────┴─────────┴──────┴─────────┴──────┴──────┴─────────┘
```

### Quick-look plots

```bash
peekr experiment.npz --plot
# -> experiment.peekr.png next to the file
```

## Anomaly flags

| Code | Condition |
|---|---|
| `HAS_NAN` | any NaN present |
| `HAS_INF` | any ±inf present |
| `ALL_NAN` | every value NaN |
| `CONSTANT` | ≥2 elements, all identical |
| `NEAR_CONSTANT` | std < 1e-12 × abs(mean), non-zero mean |
| `OUTLIERS` | >0.1% of values beyond 10× MAD from median |
| `MONOTONIC` | strictly increasing/decreasing numeric 1-D array (informational — likely a time/index axis) |
| `EMPTY` | zero elements |
| `OBJECT_DTYPE` | dtype is object (pickled data smell in npz) |
| `HIGH_CARDINALITY` | tabular column where n_unique == n_total > 1000 (likely an ID column, informational) |
| `MOSTLY_NULL` | >50% NaN/null |

`MONOTONIC` and `HIGH_CARDINALITY` are informational and do not affect the
exit code.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | clean — no data-quality flags found |
| `1` | at least one data-quality flag found (excluding informational flags) |
| `2` | usage error or unreadable file |

## CLI reference

```
peekr FILE_OR_DIR [options]

options:
  --deep            compute expensive stats (percentiles, unique counts)
  --plot            save quick-look PNG(s) next to the file: <name>.peekr.png
  --plot-dir DIR    save PNGs to DIR instead
  --json            emit the FileReport(s) as JSON to stdout (machine-readable)
  --key NAME        only inspect this array/column/dataset (repeatable)
  --recursive, -r   recurse into subdirectories
  --max-rows N      cap rows read from tabular files
  --no-anomalies    skip anomaly detection
  --version
```

## Development

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[all,dev]"
pytest tests/ -q
```

## License

MIT
