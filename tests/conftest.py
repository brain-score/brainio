import os
import shutil
from datetime import datetime
from pathlib import Path

import brainio.fetch
import numpy as np
import pandas as pd
import pytest
from brainio import lookup
from brainio.assemblies import DataAssembly, SpikeTimesAssembly, MetadataAssembly
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


def get_nc_extras_path(check=True):
    p = Path(__file__).parent/'files/assy_test_package_assembly_extras.nc'
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


def scattered_floats(lo, hi, num):
    # a kludge:  looks stochastic, but deterministic
    mid = (hi + lo) / 2
    half = mid - lo
    jump = 8
    return [mid + np.sin(x) * half for x in range(2, num * (jump + 1), jump)][:num]


# taken from values in /braintree/data2/active/users/sachis/projects/oasis900/monkeys/oleo/mworksproc/oleo_oasis900_210216_113846_mwk.csv
@pytest.fixture
def make_meta_assembly():
    coords = {
        "stim_on_time_ms": ("presentation", [100]*40),
        "stim_off_time_ms": ("presentation", [100]*40),
        "stim_on_delay_ms": ("presentation", [300]*40),
        "stimulus_size_degrees": ("presentation", [8]*40),
        "fixation_window_size_degrees": ("presentation", [2]*40),
        "fixation_point_size_degrees": ("presentation", [0.2]*40),
        "stimulus_presented": ("presentation", list(range(5))*8),
        "image_id": ("presentation", [f"n{x}" for x in list(range(5))*8]),
        "fixation_correct": ("presentation", [1]*14+[0]+[1]*25),
        "stimulus_order_in_trial": ("presentation", list(range(1, 6))*8),
        "eye_h_degrees": ("presentation", [str(scattered_floats(-0.375, -0.275, 200))]*40),
        "eye_v_degrees": ("presentation", [str(scattered_floats(0.121, 0.388, 200))]*40),
        "eye_time_ms": ("presentation", [str(scattered_floats(-50, 150, 200))]*40),
        "samp_on_us": ("presentation", scattered_floats(2_063_400, 18_820_950, 40)),
        "photodiode_on_us": ("presentation", scattered_floats(2_088_100, 18_854_550, 40)),
    }
    data = coords["photodiode_on_us"][1]
    a = MetadataAssembly(
        data=data,
        coords=coords,
        dims=['presentation']
    )
    return a


@pytest.fixture
def make_spk_assembly():
    coords = {
        "neuroid_id": ("event", ["A-019", "D-009"]*500),
        "project": ("event", ["test"]*1000),
        "datetime": ("event", np.repeat(np.datetime64('2021-02-16T11:41:55.000000000'), 1000)),
        "animal": ("event", ["testo"]*1000),
        "hemisphere": ("event", ["L", "R"]*500),
        "region": ("event", ["V4", "IT"]*500),
        "subregion": ("event", ["V4", "aIT"]*500),
        "array": ("event", ["6250-002416", "4865-233455"]*500),
        "bank": ("event", ["A", "D"]*500),
        "electrode": ("event", ["019", "009"]*500),
        "column": ("event", [5, 2]*500),
        "row": ("event", [4, 8]*500),
        "label": ("event", ["elec46", "elec123"]*500),
    }
    data = sorted(scattered_floats(67.7, 21116.2, 1000))
    a = SpikeTimesAssembly(
        data=data,
        coords=coords,
        dims=['event']
    )
    return a


def make_nc():
    a = make_proto_assembly()
    p = get_nc_path(check=False)
    write_netcdf(a, p)


def make_nc_extras(make_meta_assembly, make_spk_assembly):
    a = make_spk_assembly
    m = make_meta_assembly
    p = get_nc_extras_path(check=False)
    write_netcdf(a, p)
    write_netcdf(m, p, append=True, group="test")


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
def restore_catalog(restore_this_file):
    catalogs = {}
    def f(catalog_identifier):
        catalog = lookup.get_catalogs()[catalog_identifier]
        restore_this_file(catalog.source_path)
        catalogs[catalog_identifier] = catalog
    yield f
    main_catalogs = lookup.get_catalogs()
    for identifier, catalog in catalogs.items():
        main_catalogs[identifier] = catalog


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

