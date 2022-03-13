import os
import shutil
from datetime import datetime
from pathlib import Path

import brainio.fetch
import pandas as pd
import pytest
from brainio.assemblies import DataAssembly
from brainio.packaging import write_netcdf

@pytest.fixture
def test_catalog_identifier():
    return "brainio_test"


@pytest.fixture
def get_nc_path(check=True):
    p = Path(__file__).parent/'files/assy_test_TestMe.nc'
    if check:
        assert p.exists()
    return p


@pytest.fixture
def test_write_netcdf_path(tmp_path):
    p = tmp_path/"test.nc"
    return p


@pytest.fixture
def make_proto_assembly():
    a = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'neuroid_id': ("neuroid", ['alpha','beta', 'gamma']),
            'foo': ("neuroid", [1, 2, 5]),
            'image_id': ('presentation', ['n0', 'n1', 'n1', 'n0', 'n4', 'n9']),
            'repetition': ('presentation', [1, 1, 2, 1, 1, 1]),
        },
        dims=['presentation', 'neuroid']
    )
    return a


def make_nc():
    a = make_proto_assembly()
    p = get_nc_path(check=False)
    write_netcdf(a, p)


@pytest.fixture
def test_stimulus_set_identifier():
    return "test.TenImages"


@pytest.fixture
def get_csv_path(check=True):
    p = Path(__file__).parent / 'images/image_test_ten_images.csv'
    if check:
        assert p.exists()
    return p


@pytest.fixture
def get_dir_path(check=True):
    p = Path(__file__).parent / 'images'
    if check:
        assert p.exists()
        assert p.is_dir()
        assert list(p.iterdir())
    return p


@pytest.fixture
def make_stimulus_set_df(check=True):
    df = pd.DataFrame({'image_id': "n" + str(i), 'filename': f'n{i}.png', 'thing': f'foo{i}'} for i in range(10))
    if check:
        assert len(df) == 10
        assert len(df.columns) == 3
    return df


def make_csv():
    p = get_csv_path(check=False)
    df = make_stimulus_set_df()
    df.to_csv(p, index=False)


@pytest.fixture
def files_to_remove():
    now = datetime.now()
    paths = []
    yield paths
    for path in paths:
        p = Path(path)
        mtime = datetime.fromtimestamp(p.stat().st_ctime_ns * 1e-9)
        if p.exists() and mtime > now:
            p.unlink()


@pytest.fixture
def restore_this_file():
    now = datetime.now()
    paths = {}
    def f(path):
        path = Path(path)
        assert path.exists()
        assert path.is_file()
        tmp = path.with_suffix(path.suffix + ".bak")
        paths[path] = tmp
        shutil.copy2(str(path), str(tmp))
    yield f
    for path in paths:
        mtime = datetime.fromtimestamp(path.stat().st_mtime_ns * 1e-9)
        if path.exists() and mtime > now:
            path.unlink()
            shutil.move(paths[path], path)


@pytest.fixture
def brainio_home(tmp_path, monkeypatch):
    monkeypatch.setattr(brainio.fetch, "_local_data_path", str(tmp_path))
    yield tmp_path


@pytest.fixture(scope="session")
def home_path(tmp_path_factory):
    home_path = tmp_path_factory.mktemp("brainio_home")
    yield home_path


@pytest.fixture # for tests not intended to test fetching and loading specifically
def brainio_home_session(monkeypatch, home_path):
    monkeypatch.setattr(brainio.fetch, "_local_data_path", str(home_path))
    yield home_path

