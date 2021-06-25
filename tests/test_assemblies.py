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


def test_get_levels():
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    assert get_levels(assy) == ["up", "down"]


class TestSubclassing:
    def test_wrap_dataarray(self):
        da = DataArray(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
            coords={
                'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                'down': ("a", [1, 1, 1, 1, 2, 2]),
                'sideways': ('b', ['x', 'y', 'z'])
            },
            dims=['a', 'b']
        )
        assert "up" in da.coords
        assert da["a"].variable.level_names is None
        da = gather_indexes(da)
        assert da.coords.variables["a"].level_names == ["up", "down"]
        assert da["a"].variable.level_names == ["up", "down"]
        da = DataArray(da)
        assert da.coords.variables["a"].level_names == ["up", "down"]
        assert da["up"] is not None

    def test_wrap_dataassembly(self):
        assy = DataAssembly(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
            coords={
                'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                'down': ("a", [1, 1, 1, 1, 2, 2]),
                'sideways': ('b', ['x', 'y', 'z'])
            },
            dims=['a', 'b']
        )
        assert assy.coords.variables["a"].level_names == ["up", "down"]
        assert assy["a"].variable.level_names == ["up", "down"]
        da = DataArray(assy)
        assert da.coords.variables["a"].level_names == ["up", "down"]
        assert da["a"].variable.level_names == ["up", "down"]
        assert da["up"] is not None

    def test_reset_index(self):
        assy = DataAssembly(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
            coords={
                'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                'down': ("a", [1, 1, 1, 1, 2, 2]),
                'sideways': ('b', ['x', 'y', 'z'])
            },
            dims=['a', 'b']
        )
        da = DataArray(assy)
        da = da.reset_index(["up", "down"])
        assert get_levels(da) == []

    def test_repr(self):
        assy = DataAssembly(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
            coords={
                'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                'down': ("a", [1, 1, 1, 1, 2, 2]),
                'back': ('b', ['x', 'y', 'z']),
                'forth': ('b', [True, True, False])
            },
            dims=['a', 'b']
        )
        assy_repr = repr(assy)
        print(assy_repr)
        assert "up" in assy_repr
        assert "down" in assy_repr
        assert "back" in assy_repr
        assert "forth" in assy_repr

    def test_getitem(self):
        assy = DataAssembly(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
            coords={
                'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                'down': ("a", [1, 1, 1, 1, 2, 2]),
                'sideways': ('b', ['x', 'y', 'z'])
            },
            dims=['a', 'b']
        )
        single = assy[0, 0]
        assert type(single) is type(assy)

    def test_is_fastpath(self):
        """In DataAssembly.__init__ we have to check whether fastpath is present in a set of arguments and true
        or truthy (as interpreted by DataArray.__init__), even if only positional arguments are passed.  """
        assert is_fastpath(0, None, None, None, None, None, True)
        assert is_fastpath(0, None, None, None, None, None, fastpath=True)
        assert is_fastpath(0, None, None, None, None, None, 1)
        assert is_fastpath(0, None, None, None, None, None, fastpath=1)
        assert not is_fastpath(0, None, None, None, None, None, False)
        assert not is_fastpath(0, None, None, None, None, None, 0)
        assert not is_fastpath(0, None, None, None, None, None, fastpath=False)
        assert not is_fastpath(0, None, None, None, None, None, fastpath=0)
        assert not is_fastpath(0, None, None, None, None, None)

    def test_fastpath_signature_change(self):
        """Make sure that xarray hasn't changed the signature of DataArray.__init__ (again),
        because is_fastpath assumes a fixed length.  """
        # If the number of parameters has decreased, this will error:
        d = xr.DataArray(0, None, None, None, None, None, False)
        # This should raise TypeError: "__init__() takes from 1 to 8 positional arguments but 9 were given"
        with pytest.raises(TypeError) as te:
            d = xr.DataArray(0, None, None, None, None, None, None, False)
        assert "but 9" in str(te.value)
        # If they move fastpath to another spot in the list I guess it's tough.

    def test_align(self):
        name = "foo",
        data = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]]
        mi1 = pd.MultiIndex.from_arrays([
            ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta'],
            [1, 2, 3, 4, 5, 6]
        ], names=["up", "down"])
        mi2 = pd.MultiIndex.from_arrays([
            ['alpha', 'alpha', 'beta', 'beta', 'gamma', 'gamma'],
            [1, 2, 3, 4, 5, 6]
        ], names=["up", "down"])
        da1 = DataArray(
            name=name,
            data=data,
            coords={
                'a': mi1,
                'b': ['x', 'y', 'z']
            },
            dims=['a', 'b']
        )
        da2 = DataArray(
            name=name,
            data=data,
            coords={
                'a': mi2,
                'b': ['x', 'y', 'z']
            },
            dims=['a', 'b']
        )
        assert hasattr(da1, "up")
        assert da1.coords.variables["a"].level_names == ["up", "down"]
        assert da1["a"].variable.level_names == ["up", "down"]
        assert da1["up"] is not None
        aligned1, aligned2 = xr.align(da1, da2, join="outer")
        assert hasattr(aligned1, "up")
        assert aligned1.coords.variables["a"].level_names == ["up", "down"]
        assert aligned1["a"].variable.level_names == ["up", "down"]
        assert aligned1["up"] is not None
        assert hasattr(aligned2, "up")
        assert aligned2.coords.variables["a"].level_names == ["up", "down"]
        assert aligned2["a"].variable.level_names == ["up", "down"]
        assert aligned2["up"] is not None


class TestIndex:
    def test_single_element(self):
        d = DataAssembly([0], coords={'coordA': ('dim', [0]), 'coordB': ('dim', [1])}, dims=['dim'])
        d.sel(coordA=0)
        d.sel(coordB=1)

    def test_multi_elements(self):
        d = DataAssembly([0, 1, 2, 3, 4],
                         coords={'coordA': ('dim', [0, 1, 2, 3, 4]),
                                 'coordB': ('dim', [1, 2, 3, 4, 5])},
                         dims=['dim'])
        d.sel(coordA=0)
        d.sel(coordA=4)
        d.sel(coordB=1)
        d.sel(coordB=5)

    def test_incorrect_coord(self):
        d = DataAssembly([0], coords={'coordA': ('dim', [0]), 'coordB': ('dim', [1])}, dims=['dim'])
        with pytest.raises(KeyError):
            d.sel(coordA=1)
        with pytest.raises(KeyError):
            d.sel(coordB=0)


class TestMultiGroupby:
    def test_single_dimension(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6]], coords={'a': ['a', 'b'], 'b': ['x', 'y', 'z']}, dims=['a', 'b'])
        g = d.multi_groupby(['a']).mean(...)
        assert g.equals(DataAssembly([2, 5], coords={'a': ['a', 'b']}, dims=['a']))

    def test_single_dimension_int(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6]], coords={'a': [1, 2], 'b': [3, 4, 5]}, dims=['a', 'b'])
        g = d.multi_groupby(['a']).mean(...)
        assert g.equals(DataAssembly([2., 5.], coords={'a': [1, 2]}, dims=['a']))

    def test_single_coord(self):
        d = DataAssembly(
            data=[
                [ 0,  1,  2,  3,  4,  5,  6],
                [ 7,  8,  9, 10, 11, 12, 13],
                [14, 15, 16, 17, 18, 19, 20]
            ],
            coords={
                "greek": ("a", ['alpha', 'beta', 'gamma']),
                "colors": ("a", ['red', 'green', 'blue']),
                "compass": ("b", ['north', 'south', 'east', 'west', 'northeast', 'southeast', 'southwest']),
                "integer": ("b", [0, 1, 2, 3, 4, 5, 6]),
            },
            dims=("a", "b")
        )
        g = d.multi_groupby(['greek']).mean(...)
        c = DataAssembly(
            data=[3, 10, 17],
            coords={'greek': ('greek', ['alpha', 'beta', 'gamma'])},
            dims=['greek']
        )
        assert g.equals(c)

    def test_single_dim_multi_coord(self):
        d = DataAssembly([1, 2, 3, 4, 5, 6],
                         coords={'a': ('multi_dim', ['a', 'a', 'a', 'a', 'a', 'a']),
                                 'b': ('multi_dim', ['a', 'a', 'a', 'b', 'b', 'b']),
                                 'c': ('multi_dim', ['a', 'b', 'c', 'd', 'e', 'f'])},
                         dims=['multi_dim'])
        g = d.multi_groupby(['a', 'b']).mean()
        assert g.equals(DataAssembly([2, 5],
                                     coords={'a': ('multi_dim', ['a', 'a']), 'b': ('multi_dim', ['a', 'b'])},
                                     dims=['multi_dim']))

    def test_int_multi_coord(self):
        d = DataAssembly([1, 2, 3, 4, 5, 6],
                         coords={'a': ('multi_dim', [1, 1, 1, 1, 1, 1]),
                                 'b': ('multi_dim', ['a', 'a', 'a', 'b', 'b', 'b']),
                                 'c': ('multi_dim', ['a', 'b', 'c', 'd', 'e', 'f'])},
                         dims=['multi_dim'])
        g = d.multi_groupby(['a', 'b']).mean()
        assert g.equals(DataAssembly([2., 5.],
                                     coords={'a': ('multi_dim', [1, 1]), 'b': ('multi_dim', ['a', 'b'])},
                                     dims=['multi_dim']))

    def test_two_coord(self):
        assy = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
                         coords={'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                                 'down': ("a", [1, 1, 1, 1, 2, 2]),
                                 'sideways': ('b', ['x', 'y', 'z'])},
                         dims=['a', 'b'])
        assy_grouped = assy.multi_groupby(['up', 'down']).mean(dim="a")
        assy_2 = DataAssembly([[2.5, 3.5, 4.5], [8.5, 9.5, 10.5], [14.5, 15.5, 16.5]],
                                     coords={'up': ("a", ['alpha', 'beta', 'beta']),
                                             'down': ("a", [1, 1, 2]),
                                             'sideways': ('b', ['x', 'y', 'z'])},
                                     dims=['a', 'b'])
        assert assy_grouped.equals(assy_2)


class TestMultiDimApply:
    def test_unique_values(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
                         coords={'a': ['a', 'b', 'c', 'd'],
                                 'b': ['x', 'y', 'z']},
                         dims=['a', 'b'])
        g = d.multi_dim_apply(['a', 'b'], lambda x, **_: x)
        assert g.equals(d)

    def test_unique_values_swappeddims(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
                         coords={'a': ['a', 'b', 'c', 'd'],
                                 'b': ['x', 'y', 'z']},
                         dims=['a', 'b'])
        g = d.multi_dim_apply(['b', 'a'], lambda x, **_: x)
        assert g.equals(d)

    def test_nonindex_coord(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
                         coords={'a': ['a', 'b', 'c', 'd'],
                                 'b': ['x', 'y', 'z'],
                                 # additional coordinate that has no index values.
                                 # This could e.g. be the result of `.sel(c='remnant')`
                                 'c': 'remnant'},
                         dims=['a', 'b'])
        g = d.multi_dim_apply(['a', 'b'], lambda x, **_: x)
        assert g.equals(d)  # also tests that `c` persists

    def test_subtract_mean(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
                         coords={'a': ['a', 'b', 'c', 'd'],
                                 'aa': ('a', ['a', 'a', 'b', 'b']),
                                 'b': ['x', 'y', 'z']},
                         dims=['a', 'b'])
        g = d.multi_dim_apply(['aa', 'b'], lambda x, **_: x - x.mean())
        assert g.equals(DataAssembly([[-1.5, -1.5, -1.5], [1.5, 1.5, 1.5], [-1.5, -1.5, -1.5], [1.5, 1.5, 1.5]],
                                     coords={'a': ['a', 'b', 'c', 'd'],
                                             'aa': ('a', ['a', 'a', 'b', 'b']),
                                             'b': ['x', 'y', 'z']},
                                     dims=['a', 'b']))

    def test_multi_level(self):
        d = DataAssembly([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
                         coords={'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
                                 'down': ("a", [1, 1, 1, 1, 2, 2]),
                                 'sideways': ('b', ['x', 'y', 'z'])},
                         dims=['a', 'b'])
        g = d.multi_dim_apply(['a', 'b'], lambda x, **_: x)
        assert g.equals(d)


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


@pytest.mark.parametrize('assembly_identifier', [
    pytest.param('gallant.David2004', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.MajajHong2015', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.MajajHong2015.public', marks=[]),
    pytest.param('dicarlo.MajajHong2015.private', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.MajajHong2015.temporal', marks=[pytest.mark.private_access, pytest.mark.memory_intense]),
    pytest.param('dicarlo.MajajHong2015.temporal.public', marks=[pytest.mark.memory_intense]),
    pytest.param('dicarlo.MajajHong2015.temporal.private',
                 marks=[pytest.mark.private_access, pytest.mark.memory_intense]),
    # pytest.param('dicarlo.MajajHong2015.temporal-10ms', marks=[pytest.mark.private_access, pytest.mark.memory_intense]),
    pytest.param('tolias.Cadena2017', marks=[pytest.mark.private_access]),
    pytest.param('movshon.FreemanZiemba2013', marks=[pytest.mark.private_access, pytest.mark.memory_intense]),
    pytest.param('movshon.FreemanZiemba2013.public', marks=[pytest.mark.memory_intense]),
    pytest.param('movshon.FreemanZiemba2013.private', marks=[pytest.mark.private_access, pytest.mark.memory_intense]),
    pytest.param('dicarlo.Rajalingham2018.public', marks=[]),
    pytest.param('dicarlo.Rajalingham2018.private', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Kar2019', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Kar2018hvm', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Kar2018cocogray', marks=[pytest.mark.private_access]),
    pytest.param('klab.Zhang2018search_obj_array', marks=[pytest.mark.private_access]),
    pytest.param('aru.Kuzovkin2018', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Rajalingham2020', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.SanghaviMurty2020', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.SanghaviJozwik2020', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Sanghavi2020', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.SanghaviMurty2020THINGS1', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.SanghaviMurty2020THINGS2', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Seibert2019', marks=[pytest.mark.private_access]),
    pytest.param('aru.Cichy2019', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Rust2012.single', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.Rust2012.array', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.naturalistic', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.synthetic', marks=[pytest.mark.private_access]),
])
def test_existence(assembly_identifier):
    assert brainio.get_assembly(assembly_identifier) is not None


def test_nr_assembly_ctor():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    assert isinstance(assy_hvm, DataAssembly)


def test_load():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    assert assy_hvm.shape == (256, 148480, 1)
    print(assy_hvm)


def test_repr():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    repr_hvm = repr(assy_hvm)
    assert "neuroid" in repr_hvm
    assert "presentation" in repr_hvm
    assert "256" in repr_hvm
    assert "148480" in repr_hvm
    assert "animal" in repr_hvm
    print(repr_hvm)


def test_getitem():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    single = assy_hvm[0, 0, 0]
    assert type(single) is type(assy_hvm)


def test_lookup():
    assy = brainio.lookup.lookup_assembly("dicarlo.MajajHong2015.public")
    assert assy['identifier'] == "dicarlo.MajajHong2015.public"
    assert assy['location_type'] == "S3"
    hvm_s3_url = "https://brainio.dicarlo.s3.amazonaws.com/assy_dicarlo_MajajHong2015_public.nc"
    assert assy['location'] == hvm_s3_url


def test_lookup_bad_name():
    with pytest.raises(brainio.lookup.AssemblyLookupError):
        brainio.lookup.lookup_assembly("BadName")


def test_fetch():
    local_path = fetch.fetch_file(
        location_type='S3',
        location='https://brainio.dicarlo.s3.amazonaws.com/assy_dicarlo_MajajHong2015_public.nc',
        sha1='13d28ca0ce88ee550b54db3004374ae19096e9b9')
    assert os.path.exists(local_path)


def test_wrap():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    hvm_v3 = assy_hvm.sel(variation=3)
    assert isinstance(hvm_v3, assemblies.NeuronRecordingAssembly)

    hvm_it_v3 = hvm_v3.sel(region="IT")
    assert isinstance(hvm_it_v3, assemblies.NeuronRecordingAssembly)

    hvm_it_v3.coords["cat_obj"] = hvm_it_v3.coords["category_name"] + hvm_it_v3.coords["object_name"]
    hvm_it_v3.load()
    hvm_it_v3_grp = hvm_it_v3.multi_groupby(["category_name", "object_name"])
    assert not isinstance(hvm_it_v3_grp, xr.core.groupby.GroupBy)
    assert isinstance(hvm_it_v3_grp, assemblies.GroupbyBridge)

    hvm_it_v3_obj = hvm_it_v3_grp.mean(dim="presentation")
    assert isinstance(hvm_it_v3_obj, assemblies.NeuronRecordingAssembly)

    hvm_it_v3_sqz = hvm_it_v3_obj.squeeze("time_bin")
    assert isinstance(hvm_it_v3_sqz, assemblies.NeuronRecordingAssembly)

    hvm_it_v3_t = hvm_it_v3_sqz.T
    assert isinstance(hvm_it_v3_t, assemblies.NeuronRecordingAssembly)


def test_multi_group():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    hvm_it_v3 = assy_hvm.sel(variation=3).sel(region="IT")
    hvm_it_v3.load()
    hvm_it_v3_obj = hvm_it_v3.multi_groupby(["category_name", "object_name"]).mean(dim="presentation")
    assert "category_name" in hvm_it_v3_obj.indexes["presentation"].names
    assert "object_name" in hvm_it_v3_obj.indexes["presentation"].names


def test_stimulus_set_from_assembly():
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    stimulus_set = assy_hvm.attrs["stimulus_set"]
    assert stimulus_set.shape[0] == np.unique(assy_hvm["image_id"]).shape[0]
    for image_id in stimulus_set['image_id']:
        image_path = stimulus_set.get_image(image_id)
        assert os.path.exists(image_path)


@pytest.mark.private_access
def test_klab_Zhang2018search():
    assembly = brainio.get_assembly('klab.Zhang2018search_obj_array')
    assert set(assembly.dims) == {'presentation', 'fixation', 'position'}
    assert len(assembly['presentation']) == 4500
    assert len(set(assembly['image_id'].values)) == 300
    assert len(set(assembly['subjects'].values)) == 15
    assert len(assembly['fixation']) == 8
    assert len(assembly['position']) == 2
    assert assembly.stimulus_set is not None


class TestFreemanZiemba:
    @pytest.mark.parametrize('identifier', [
        pytest.param('movshon.FreemanZiemba2013.public', marks=[]),
        pytest.param('movshon.FreemanZiemba2013.private', marks=[pytest.mark.private_access]),
    ])
    def test_v1_v2_alignment(self, identifier):
        assembly = brainio.get_assembly(identifier)
        v1 = assembly[{'neuroid': [region == 'V1' for region in assembly['region'].values]}]
        v2 = assembly[{'neuroid': [region == 'V2' for region in assembly['region'].values]}]
        assert len(v1['presentation']) == len(v2['presentation'])
        assert set(v1['image_id'].values) == set(v2['image_id'].values)

    @pytest.mark.parametrize('identifier', [
        pytest.param('movshon.FreemanZiemba2013.public', marks=[]),
        pytest.param('movshon.FreemanZiemba2013.private', marks=[pytest.mark.private_access]),
    ])
    def test_num_neurons(self, identifier):
        assembly = brainio.get_assembly(identifier)
        assert len(assembly['neuroid']) == 205
        v1 = assembly[{'neuroid': [region == 'V1' for region in assembly['region'].values]}]
        assert len(v1['neuroid']) == 102
        v2 = assembly[{'neuroid': [region == 'V2' for region in assembly['region'].values]}]
        assert len(v2['neuroid']) == 103

    @pytest.mark.parametrize('identifier', [
        pytest.param('movshon.FreemanZiemba2013.public', marks=[]),
        pytest.param('movshon.FreemanZiemba2013.private', marks=[pytest.mark.private_access]),
    ])
    def test_nonzero(self, identifier):
        assembly = brainio.get_assembly(identifier)
        nonzero = np.count_nonzero(assembly)
        assert nonzero > 0

    @pytest.mark.parametrize('identifier, image_id, expected_amount_gray, ratio_gray', [
        pytest.param('movshon.FreemanZiemba2013.public', '21041db1f26c142812a66277c2957fb3e2070916',
                     31756, .3101171875, marks=[]),
        pytest.param('movshon.FreemanZiemba2013.private', 'bfd26c127f8ba028cc95cdc95f00c45c8884b365',
                     31585, .308447265625, marks=[pytest.mark.private_access]),
    ])
    def test_aperture(self, identifier, image_id, expected_amount_gray, ratio_gray):
        """ test a random image for the correct amount of gray pixels """
        assembly = brainio.get_assembly(identifier)
        stimulus_set = assembly.stimulus_set
        image_path = Path(stimulus_set.get_image(image_id))
        assert image_path.is_file()
        # count number of gray pixels in image
        image = Image.open(image_path)
        image = np.array(image)
        amount_gray = 0
        for index in np.ndindex(image.shape[:2]):
            color = image[index]
            gray = [128, 128, 128]
            if (color == gray).all():
                amount_gray += 1
        assert amount_gray / image.size == approx(ratio_gray, abs=.0001)
        assert amount_gray == expected_amount_gray


def test_inplace():
    d = xr.DataArray(0, None, None, None, None, None, False)
    with pytest.raises(TypeError) as te:
        d = d.reset_index(None, inplace=True)
    assert "inplace" in str(te.value)


class TestSeibert:
    @pytest.mark.private_access
    def test_dims(self):
        assembly = brainio.get_assembly('dicarlo.Seibert2019')
        # neuroid: 258 presentation: 286080 time_bin: 1
        assert assembly.dims == ("neuroid", "presentation", "time_bin")
        assert len(assembly['neuroid']) == 258
        assert len(assembly['presentation']) == 286080
        assert len(assembly['time_bin']) == 1

    @pytest.mark.private_access
    def test_coords(self):
        assembly = brainio.get_assembly('dicarlo.Seibert2019')
        assert len(set(assembly['image_id'].values)) == 5760
        assert len(set(assembly['neuroid_id'].values)) == 258
        assert len(set(assembly['animal'].values)) == 3
        assert len(set(assembly['region'].values)) == 2
        assert len(set(assembly['variation'].values)) == 3

    @pytest.mark.private_access
    def test_content(self):
        assembly = brainio.get_assembly('dicarlo.Seibert2019')
        assert np.count_nonzero(np.isnan(assembly)) == 19118720
        assert assembly.stimulus_set_identifier == "dicarlo.hvm"
        hvm = assembly.stimulus_set
        assert hvm.shape == (5760, 18)


class TestRustSingle:
    @pytest.mark.private_access
    def test_dims(self):
        assembly = brainio.get_assembly('dicarlo.Rust2012.single')
        # (neuroid: 285, presentation: 1500, time_bin: 1)
        assert assembly.dims == ("neuroid", "presentation", "time_bin")
        assert len(assembly['neuroid']) == 285
        assert len(assembly['presentation']) == 1500
        assert len(assembly['time_bin']) == 1

    @pytest.mark.private_access
    def test_coords(self):
        assembly = brainio.get_assembly('dicarlo.Rust2012.single')
        assert len(set(assembly['image_id'].values)) == 300
        assert len(set(assembly['neuroid_id'].values)) == 285
        assert len(set(assembly['region'].values)) == 2


class TestRustArray:
    @pytest.mark.private_access
    def test_dims(self):
        assembly = brainio.get_assembly('dicarlo.Rust2012.array')
        # (neuroid: 296, presentation: 53700, time_bin: 6)
        assert assembly.dims == ("neuroid", "presentation", "time_bin")
        assert len(assembly['neuroid']) == 296
        assert len(assembly['presentation']) == 53700
        assert len(assembly['time_bin']) == 6

    @pytest.mark.private_access
    def test_coords(self):
        assembly = brainio.get_assembly('dicarlo.Rust2012.array')
        assert len(set(assembly['image_id'].values)) == 300
        assert len(set(assembly['neuroid_id'].values)) == 296
        assert len(set(assembly['animal'].values)) == 2
        assert len(set(assembly['region'].values)) == 2


@pytest.mark.parametrize('assembly,shape,nans', [
    pytest.param('dicarlo.BashivanKar2019.naturalistic', (24320, 233, 1), 309760, marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.synthetic', (21360, 233, 1), 4319940, marks=[pytest.mark.private_access]),
])
def test_synthetic(assembly, shape, nans):
    assy = brainio.get_assembly(assembly)
    assert assy.shape == shape
    assert np.count_nonzero(np.isnan(assy)) == nans

