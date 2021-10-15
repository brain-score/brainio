from pathlib import Path

import pytest

import brainio
from pandas import DataFrame

from brainio.assemblies import DataAssembly, get_levels
from brainio.stimuli import StimulusSet
from brainio.packaging import write_netcdf, check_image_numbers, check_image_naming_convention, TYPE_ASSEMBLY, \
    TYPE_STIMULUS_SET, package_stimulus_set, package_data_assembly
import brainio.lookup as lookup

STIMULUS_SET_IDENTIFIER = "test.ten_images"

TEST_CATALOG_NAME = "brainio_test"


def test_write_netcdf():
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    netcdf_path = Path("test.nc")
    netcdf_sha1 = write_netcdf(assy, str(netcdf_path))
    assert netcdf_path.exists()


def test_reset_index():
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    assert assy["a"].variable.level_names == ["up", "down"]
    assert list(assy.indexes) == ["a", "b"]
    assy = assy.reset_index(list(assy.indexes))
    assert assy["a"].variable.level_names is None
    assert get_levels(assy) == []
    assert list(assy.indexes) == []


def test_reset_index_levels():
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    assert assy["a"].variable.level_names == ["up", "down"]
    assy = assy.reset_index(["up", "down"])
    assert get_levels(assy) == []


def test_image_numbers():
    stimulus_set = StimulusSet(DataFrame({'image_id': [0, 1]}))
    filenames = ['Nat300_1.png', 'Nat300_2.png']
    assert len(stimulus_set) == len(filenames)
    stimulus_set.image_paths = {stimulus_set.at[idx, 'image_id']: filenames[idx] for idx in range(len(stimulus_set))}

    check_image_numbers(stimulus_set)


def test_image_naming_convention():
    for name in ['image_1.png', 'Nat300_100.png', '1.png']:
        check_image_naming_convention(name)


def test_list_catalogs():
    catalog_names = lookup.list_catalogs()
    assert TEST_CATALOG_NAME in catalog_names


def test_append():
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    identifier = "test.append"
    target_netcdf_file = Path("assy_test_append.nc")
    netcdf_sha1 = write_netcdf(assy, str(target_netcdf_file))
    lookup.append(TEST_CATALOG_NAME, identifier, "DataAssembly", TYPE_ASSEMBLY, "brainio-temp", netcdf_sha1, "assy_test_append.nc", "dicarlo.hvm")
    assert identifier in list(lookup.get_catalogs()[TEST_CATALOG_NAME]["identifier"])
    assert identifier in lookup.list_assemblies()


@pytest.mark.private_access
def test_package_stimulus_set():
    stimulus_set = StimulusSet([{'image_id': "n"+str(i), 'thing': 'foo'} for i in range(10)])
    stimulus_set.image_paths = {"n"+str(i): Path(__file__).parent / f'images/n{i}.png' for i in range(10)}
    identifier = STIMULUS_SET_IDENTIFIER
    package_stimulus_set(TEST_CATALOG_NAME, stimulus_set, identifier, bucket_name="brainio-temp")
    assert identifier in lookup.list_stimulus_sets()
    gotten = brainio.get_stimulus_set(identifier)
    assert gotten is not None


@pytest.mark.private_access
def test_package_data_assembly():
    if STIMULUS_SET_IDENTIFIER not in brainio.list_stimulus_sets():
        test_package_stimulus_set()
    assy = DataAssembly(
        data=[[[1], [2], [3]], [[4], [5], [6]], [[7], [8], [9]], [[10], [11], [12]], [[13], [14], [15]], [[16], [17], [18]]],
        coords={
            'image_id': ("presentation", ["n"+str(i) for i in range(6)]),
            'image_type': ("presentation", ["foo"]*6),
            'neuroid_id': ("neuroid", list("ABC")),
            'neuroid_type': ("neuroid", ["bar"]*3),
            'time_bin_start': ('time_bin', [0]),
            'time_bin_end': ('time_bin', [10]),
        },
        dims=['presentation', 'neuroid', 'time_bin']
    )
    identifier = "test.package_assembly"
    package_data_assembly(TEST_CATALOG_NAME, assy, identifier, STIMULUS_SET_IDENTIFIER, "DataAssembly", "brainio-temp")
    assert identifier in lookup.list_assemblies()
    gotten = brainio.get_assembly(identifier)
    assert gotten is not None


