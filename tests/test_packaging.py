from pathlib import Path

from pandas import DataFrame

from brainio.assemblies import DataAssembly, get_levels
from brainio.stimuli import StimulusSet
from brainio.packaging import write_netcdf, check_image_numbers, check_image_naming_convention


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

