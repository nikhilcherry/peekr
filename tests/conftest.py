"""Shared fixtures: generate tiny sample files of each supported format in tmp_path."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def clean_npz(tmp_path):
    path = tmp_path / "clean.npz"
    rng = np.random.default_rng(0)
    np.savez(
        path,
        a=rng.normal(size=100).astype(np.float64),
        b=rng.uniform(0, 1, size=50).astype(np.float32),
        c=np.arange(30, dtype=np.int64),
    )
    return path


@pytest.fixture
def clean_npy(tmp_path):
    path = tmp_path / "clean.npy"
    rng = np.random.default_rng(7)
    np.save(path, rng.normal(size=200).astype(np.float64))
    return path


@pytest.fixture
def dirty_npy(tmp_path):
    path = tmp_path / "dirty.npy"
    obj_arr = np.array([{"a": 1}, [1, 2, 3], "text"], dtype=object)
    np.save(path, obj_arr, allow_pickle=True)
    return path


@pytest.fixture
def dirty_npz(tmp_path):
    path = tmp_path / "dirty.npz"
    rng = np.random.default_rng(1)
    has_nan = rng.normal(size=100)
    has_nan[:5] = np.nan
    constant = np.full(20, 7.0)
    outliers = rng.normal(size=500)
    outliers[:3] = 1000.0
    obj_arr = np.array([{"a": 1}, [1, 2, 3], "text"], dtype=object)
    np.savez(path, has_nan=has_nan, constant=constant, outliers=outliers, obj_arr=obj_arr)
    return path


@pytest.fixture
def truncated_npz(tmp_path):
    good_path = tmp_path / "_good_for_truncation.npz"
    np.savez(good_path, x=np.arange(100, dtype=np.float64))
    data = good_path.read_bytes()
    path = tmp_path / "truncated.npz"
    path.write_bytes(data[: len(data) // 2])
    return path


@pytest.fixture
def table_csv(tmp_path):
    pd = pytest.importorskip("pandas")
    path = tmp_path / "table.csv"
    rng = np.random.default_rng(2)
    n = 200
    ids = [f"ID{i:05d}" for i in range(n)]
    values = rng.normal(size=n)
    mostly_null = np.full(n, np.nan)
    mostly_null[: n // 4] = rng.normal(size=n // 4)
    categories = rng.choice(["a", "b", "c"], size=n)

    df = pd.DataFrame({"id": ids, "value": values, "mostly_null": mostly_null, "category": categories})
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def image_fits(tmp_path):
    fits = pytest.importorskip("astropy.io.fits")
    path = tmp_path / "image.fits"
    rng = np.random.default_rng(3)
    data = rng.normal(size=(20, 30)).astype(np.float32)
    hdu = fits.PrimaryHDU(data=data)
    hdu.header["OBSERVER"] = "peekr-test"
    hdu.writeto(path, overwrite=True)
    return path


@pytest.fixture
def bintable_fits(tmp_path):
    fits = pytest.importorskip("astropy.io.fits")
    path = tmp_path / "bintable.fits"
    rng = np.random.default_rng(4)
    col1 = fits.Column(name="flux", format="D", array=rng.normal(size=50))
    col2 = fits.Column(name="id", format="K", array=np.arange(50))
    hdu = fits.BinTableHDU.from_columns([col1, col2])
    primary = fits.PrimaryHDU()
    hdul = fits.HDUList([primary, hdu])
    hdul.writeto(path, overwrite=True)
    return path


@pytest.fixture
def data_h5(tmp_path):
    h5py = pytest.importorskip("h5py")
    path = tmp_path / "data.h5"
    rng = np.random.default_rng(5)
    with h5py.File(path, "w") as f:
        f.attrs["created_by"] = "peekr-test"
        f.create_dataset("flat", data=rng.normal(size=100))
        grp = f.create_group("group1")
        sub = grp.create_group("subgroup")
        sub.create_dataset("nested", data=rng.normal(size=(10, 10)))
        grp.create_dataset("bigger", data=rng.normal(size=5000))
    return path


@pytest.fixture
def data_parquet(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    path = tmp_path / "data.parquet"
    rng = np.random.default_rng(6)
    df = pd.DataFrame({"x": rng.normal(size=100), "y": rng.integers(0, 10, size=100)})
    df.to_parquet(path)
    return path
