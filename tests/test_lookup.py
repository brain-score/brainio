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
        'tolias.Cadena2017',
        'dicarlo.BashivanKar2019.naturalistic',
        'dicarlo.BashivanKar2019.synthetic',
))
def test_list_assembly(assembly):
    l = brainio.list_assemblies()
    assert assembly in l


@pytest.mark.parametrize('stimulus_set', (
        'dicarlo.hvm',
        'dicarlo.hvm-public',
        'dicarlo.hvm-private',
        'tolias.Cadena2017',
        'dicarlo.BashivanKar2019.naturalistic',
        'dicarlo.BashivanKar2019.synthetic'
))
def test_list_stimulus_set(stimulus_set):
    l = brainio.list_stimulus_sets()
    assert stimulus_set in l


def test_lookup_stim():
    stim_csv, stim_zip = brainio.lookup.lookup_stimulus_set("dicarlo.hvm")
    assert stim_csv['identifier'] == "dicarlo.hvm"
    assert stim_csv['location_type'] == "S3"
    hvm_s3_csv_url = "https://brainio.dicarlo.s3.amazonaws.com/image_dicarlo_hvm.csv"
    assert stim_csv['location'] == hvm_s3_csv_url
    assert stim_zip['identifier'] == "dicarlo.hvm"
    assert stim_zip['location_type'] == "S3"
    hvm_s3_zip_url = "https://brainio.dicarlo.s3.amazonaws.com/image_dicarlo_hvm.zip"
    assert stim_zip['location'] == hvm_s3_zip_url


def test_lookup_assy():
    assy = brainio.lookup.lookup_assembly("dicarlo.MajajHong2015.public")
    assert assy['identifier'] == "dicarlo.MajajHong2015.public"
    assert assy['location_type'] == "S3"
    hvm_s3_url = "https://brainio.dicarlo.s3.amazonaws.com/assy_dicarlo_MajajHong2015_public.nc"
    assert assy['location'] == hvm_s3_url


def test_lookup_bad_name():
    with pytest.raises(brainio.lookup.AssemblyLookupError):
        brainio.lookup.lookup_assembly("BadName")


def test_catalogs():
    cats = brainio.lookup.list_installed_catalogs()
    assert len(cats) == 2
    assert "brainio_test" in cats
    assert "brainio_test2" in cats
    dfs = brainio.lookup._load_installed_catalogs()
    assert dfs["brainio_test"].attrs[brainio.lookup.CATALOG_PATH_KEY].endswith(".csv")
    assert dfs["brainio_test2"].attrs[brainio.lookup.CATALOG_PATH_KEY].endswith(".csv")
    assert len(dfs["brainio_test"]) == 12
    assert len(dfs["brainio_test2"]) == 9
    concat = brainio.lookup.combined_catalog()
    assert len(concat) == len(dfs["brainio_test"]) + len(dfs["brainio_test2"])


def test_duplicates():
    all_lookups = brainio.lookup.combined_catalog()
    match_stim = all_lookups['lookup_type'] == brainio.lookup.TYPE_STIMULUS_SET
    match_csv = all_lookups.apply(brainio.lookup._is_csv_lookup, axis=1)
    match_zip = all_lookups.apply(brainio.lookup._is_zip_lookup, axis=1)
    match_assy = all_lookups['lookup_type'] == brainio.lookup.TYPE_ASSEMBLY

    match_hvm = all_lookups['identifier'] == "dicarlo.hvm"
    assert np.count_nonzero(match_hvm) == 4
    assert len(all_lookups[match_hvm & match_stim & match_csv]) == 2
    assert len(all_lookups[match_hvm & match_stim & match_zip]) == 2
    match_mh15 = all_lookups['identifier'] == "dicarlo.MajajHong2015"
    match_mh15_pub = all_lookups['identifier'] == "dicarlo.MajajHong2015.public"
    match_mh15_pvt = all_lookups['identifier'] == "dicarlo.MajajHong2015.private"
    assert len(all_lookups[match_mh15 & match_assy]) == 2
    assert len(all_lookups[match_mh15_pub & match_assy]) == 1
    assert len(all_lookups[match_mh15_pvt & match_assy]) == 1
    match_c17 = all_lookups['identifier'] == "tolias.Cadena2017"
    assert len(all_lookups[match_c17 & match_stim & match_csv]) == 1
    assert len(all_lookups[match_c17 & match_stim & match_zip]) == 1
    assert len(all_lookups[match_c17 & match_assy]) == 1



