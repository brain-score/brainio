import os
from pathlib import Path

import pytest
from pytest import approx
import numpy as np
import pandas as pd
import xarray as xr
from xarray import DataArray
from PIL import Image

import brainio
from brainio import assemblies
from brainio import fetch
from brainio.assemblies import DataAssembly, get_levels, gather_indexes, is_fastpath


@pytest.mark.parametrize('assembly', (
        'dicarlo.MajajHong2015',
        'dicarlo.MajajHong2015.private',
        'dicarlo.MajajHong2015.public',
        'dicarlo.MajajHong2015.temporal',
        'dicarlo.MajajHong2015.temporal.private',
        'dicarlo.MajajHong2015.temporal.public',
        'dicarlo.MajajHong2015.temporal-10ms',
        'gallant.David2004',
        'tolias.Cadena2017',
        'movshon.FreemanZiemba2013',
        'movshon.FreemanZiemba2013.private',
        'movshon.FreemanZiemba2013.public',
        'dicarlo.Rajalingham2018.public', 'dicarlo.Rajalingham2018.private',
        'dicarlo.Kar2019',
        'dicarlo.Kar2018hvm',
        'dicarlo.Kar2018cocogray',
        'klab.Zhang2018search_obj_array',
        'aru.Kuzovkin2018',
        'dicarlo.Rajalingham2020',
        'dicarlo.SanghaviMurty2020',
        'dicarlo.SanghaviJozwik2020',
        'dicarlo.Sanghavi2020',
        'dicarlo.SanghaviMurty2020THINGS1',
        'dicarlo.SanghaviMurty2020THINGS2',
        'aru.Kuzovkin2018',
        'dicarlo.Seibert2019',
        'aru.Cichy2019',
        'dicarlo.Rust2012.single',
        'dicarlo.Rust2012.array',
        'dicarlo.BashivanKar2019.naturalistic',
        'dicarlo.BashivanKar2019.synthetic',
))
def test_list_assembly(assembly):
    l = brainio.list_assemblies()
    assert assembly in l


def test_lookup_stim():
    stim_csv, stim_zip = brainio.lookup.lookup_stimulus_set("dicarlo.hvm")
    assert stim_csv['identifier'] == "dicarlo.hvm"
    assert stim_csv['location_type'] == "S3"
    hvm_s3_csv_url = "https://brainio.dicarlo.s3.amazonaws.com/image_dicarlo_hvm.csv"
    assert stim_csv['location'] == hvm_s3_csv_url
    assert stim_zip['identifier'] == "dicarlo.hvm"
    assert stim_zip['location_type'] == "S3"
    hvm_s3_zip_url = "https://brainio.dicarlo.s3.amazonaws.com/image_dicarlo_hvm.zip"
    assert stim_csv['location'] == hvm_s3_zip_url


def test_lookup_assy():
    assy = brainio.lookup.lookup_assembly("dicarlo.MajajHong2015.public")
    assert assy['identifier'] == "dicarlo.MajajHong2015.public"
    assert assy['location_type'] == "S3"
    hvm_s3_url = "https://brainio.dicarlo.s3.amazonaws.com/assy_dicarlo_MajajHong2015_public.nc"
    assert assy['location'] == hvm_s3_url


def test_lookup_stim():
    csv, zip = brainio.lookup.lookup_stimulus_set("dicarlo.hvm")
    assert csv['identifier'] == "dicarlo.hvm"
    assert csv['location_type'] == "S3"
    hvm_s3_url = "https://brainio.dicarlo.s3.amazonaws.com/image_dicarlo_hvm.csv"
    assert csv['location'] == hvm_s3_url


def test_lookup_bad_name():
    with pytest.raises(brainio.lookup.AssemblyLookupError):
        brainio.lookup.lookup_assembly("BadName")


def test_catalogs():
    cats = brainio.lookup.list_catalogs()
    assert len(cats) == 2
    assert "brainio_test" in cats
    assert "brainio_test2" in cats
    dfs = brainio.lookup.get_lookups()
    assert dfs["brainio_test"].attrs[brainio.lookup.CATALOG_PATH_KEY].endswith(".csv")
    assert dfs["brainio_test2"].attrs[brainio.lookup.CATALOG_PATH_KEY].endswith(".csv")
    assert len(dfs["brainio_test2"]) == 5
    concat = brainio.lookup.data()
    assert len(concat) == len(dfs["brainio_test"]) + len(dfs["brainio_test2"])


def test_duplicates():
    all_lookups = brainio.lookup.data()
    match_hvm = all_lookups['identifier'] == "dicarlo.hvm"
    assert np.count_nonzero(match_hvm) == 4
    match_stim = all_lookups['lookup_type'] == brainio.lookup.TYPE_STIMULUS_SET
    match_csv = all_lookups.apply(brainio.lookup._is_csv_lookup, axis=1)
    match_zip = all_lookups.apply(brainio.lookup._is_zip_lookup, axis=1)
    assert len(all_lookups[match_hvm & match_stim & match_csv]) == 2
    assert len(all_lookups[match_hvm & match_stim & match_zip]) == 2
    match_mh15 = all_lookups['identifier'] == "dicarlo.MajajHong2015"
    match_mh15_pub = all_lookups['identifier'] == "dicarlo.MajajHong2015.public"
    match_mh15_pvt = all_lookups['identifier'] == "dicarlo.MajajHong2015.private"
    match_assy = all_lookups['lookup_type'] == brainio.lookup.TYPE_ASSEMBLY
    assert len(all_lookups[match_mh15 & match_assy]) == 2
    assert len(all_lookups[match_mh15_pub & match_assy]) == 2
    assert len(all_lookups[match_mh15_pvt & match_assy]) == 2



