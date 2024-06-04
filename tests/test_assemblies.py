import os

import pytest
import numpy as np
import pandas as pd
import xarray as xr
from brainio.stimuli import StimulusSet
from tests.conftest import get_nc_extras_path, get_nc_path, get_csv_path, get_dir_path, make_proto_assembly
from xarray import DataArray

import brainio
from brainio import assemblies
from brainio import fetch
from brainio.assemblies import DataAssembly, get_levels, gather_indexes, is_fastpath, MetadataAssembly, \
    SpikeTimesAssembly, get_metadata, BRAINIO_CHUNKS


def test_get_metadata():
    xr.show_versions()
    # assembly, dims, names_only, include_coords, include_indexes, include_multi_indexes, include_levels
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'why': ("a", ['yes', 'yes', 'yes', 'yes', 'yes', 'no']),
            'b': ('b', ['x', 'y', 'z']),
        },
        dims=['a', 'b']
    )
    assy = assy.reset_index('why')
    assert set(get_metadata(assy, None, True, True, True, True, True)) == {'a', 'up', 'down', 'why', 'b'}
    assert set(get_metadata(assy, None, True, True, True, True, False)) == {'a', 'why', 'b'}
    assert set(get_metadata(assy, None, True, True, True, False, True)) == {'up', 'down', 'why', 'b'}
    assert set(get_metadata(assy, None, True, True, True, False, False)) == {'why', 'b'}
    assert set(get_metadata(assy, None, True, True, False, True, True)) == {'a', 'up', 'down', 'why'}
    assert set(get_metadata(assy, None, True, True, False, True, False)) == {'a', 'why'}
    assert set(get_metadata(assy, None, True, True, False, False, True)) == {'up', 'down', 'why'}
    assert set(get_metadata(assy, None, True, True, False, False, False)) == {'why'}
    assert set(get_metadata(assy, None, True, False, True, True, True)) == {'a', 'up', 'down', 'b'}
    assert set(get_metadata(assy, None, True, False, True, True, False)) == {'a', 'b'}
    assert set(get_metadata(assy, None, True, False, True, False, True)) == {'up', 'down', 'b'}
    assert set(get_metadata(assy, None, True, False, True, False, False)) == {'b'}
    assert set(get_metadata(assy, None, True, False, False, True, True)) == {'a', 'up', 'down'}
    assert set(get_metadata(assy, None, True, False, False, True, False)) == {'a'}
    assert set(get_metadata(assy, None, True, False, False, False, True)) == {'up', 'down'}
    assert set(get_metadata(assy, None, True, False, False, False, False)) == set()

    a = make_proto_assembly()
    md_all = list(get_metadata(a))
    assert len(md_all) == 4
    md_coo = list(get_metadata(a, include_indexes=False, include_levels=False))
    assert len(md_coo) == 0
    md_ind = list(get_metadata(a, include_coords=False, include_indexes=True, include_multi_indexes=True, include_levels=False))
    assert len(md_ind) == 2
    md_lev = list(get_metadata(a, include_coords=False, include_indexes=False))
    assert len(md_lev) == 4


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
    assert get_levels(assy) == ["up", "down", "sideways"]


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
        assert "a" not in da.indexes
        da = gather_indexes(da)
        assert da.indexes["a"].names == ["up", "down"]
        da = DataArray(da)
        assert da.indexes["a"].names == ["up", "down"]
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
        assert assy.indexes["a"].names == ["up", "down"]
        da = DataArray(assy)
        assert assy.indexes["a"].names == ["up", "down"]
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
        da = da.reset_index(["up", "down", "sideways"])
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
        assert single == 1

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
        assert da1.indexes["a"].names == ["up", "down"]
        assert da1["up"] is not None
        aligned1, aligned2 = xr.align(da1, da2, join="outer")
        assert hasattr(aligned1, "up")
        assert aligned1.indexes["a"].names == ["up", "down"]
        assert aligned1["up"] is not None
        assert hasattr(aligned2, "up")
        assert aligned2.indexes["a"].names == ["up", "down"]
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


class TestPlainGroupy:

    def test_on_data_array(self):
        d = DataArray(
            data=[
                [0, 1, 2, 3, 4, 5, 6],
                [7, 8, 9, 10, 11, 12, 13],
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
        d = d.set_index(a=['greek', 'colors'], b=['compass', 'integer'])
        g = d.groupby('greek')
        # with xarray==2022.06.0, the following line fails with:
        # ValueError: conflicting multi-index level name 'greek' with dimension 'greek'
        m = g.mean(...)
        c = DataArray(
            data=[3, 10, 17],
            coords={'greek': ('greek', ['alpha', 'beta', 'gamma'])},
            dims=['greek']
        )
        assert m.equals(c)

    def test_on_data_assembly(self):
        d = DataAssembly(
            data=[
                [0, 1, 2, 3, 4, 5, 6],
                [7, 8, 9, 10, 11, 12, 13],
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
        g = d.groupby('greek')
        m = g.mean(...)
        c = DataAssembly(
            data=[3, 10, 17],
            coords={'greek': ('greek', ['alpha', 'beta', 'gamma'])},
            dims=['greek']
        )
        assert m.equals(c)


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
        g = d.multi_groupby(['greek'])
        m = g.mean(...)
        c = DataAssembly(
            data=[3, 10, 17],
            coords={'greek': ('greek', ['alpha', 'beta', 'gamma'])},
            dims=['greek']
        )
        assert m.equals(c)

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


@pytest.mark.parametrize('assembly_identifier', [
    pytest.param('dicarlo.MajajHong2015', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.MajajHong2015.public', marks=[]),
    pytest.param('dicarlo.MajajHong2015.private', marks=[pytest.mark.private_access]),
    pytest.param('tolias.Cadena2017', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.naturalistic', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.synthetic', marks=[pytest.mark.private_access]),
])
def test_existence(assembly_identifier, brainio_home_session):
    assert brainio.get_assembly(assembly_identifier) is not None


def test_nr_assembly_ctor(brainio_home_session):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    assert isinstance(assy_hvm, DataAssembly)


def test_load(brainio_home):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    assert assy_hvm.shape == (256, 148480, 1)
    print(assy_hvm)


class TestDask:
    def test_dask(self, brainio_home):
        assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
        try:
            import dask
            assert assy_hvm.chunks is not None
        except ModuleNotFoundError as e:
            assert assy_hvm.chunks is None

    def test_dask_override(self, brainio_home, monkeypatch):
        with monkeypatch.context() as patch:
            patch.setenv(BRAINIO_CHUNKS, 'None')
            assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
        assert assy_hvm.chunks is None


def test_repr(brainio_home_session):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    repr_hvm = repr(assy_hvm)
    assert "neuroid" in repr_hvm
    assert "presentation" in repr_hvm
    assert "256" in repr_hvm
    assert "148480" in repr_hvm
    assert "animal" in repr_hvm
    print(repr_hvm)


def test_getitem(brainio_home_session):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    single = assy_hvm[0, 0, 0]
    assert type(single) is type(assy_hvm)


def test_fetch(brainio_home):
    local_path = fetch.fetch_file(
        location_type='S3',
        location='https://brainio.dicarlo.s3.amazonaws.com/assy_dicarlo_MajajHong2015_public.nc',
        sha1='13d28ca0ce88ee550b54db3004374ae19096e9b9')
    assert os.path.exists(local_path)


def test_wrap(brainio_home_session):
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


def test_multi_group(brainio_home_session):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    hvm_it_v3 = assy_hvm.sel(variation=3).sel(region="IT")
    hvm_it_v3.load()
    hvm_it_v3_obj = hvm_it_v3.multi_groupby(["category_name", "object_name"]).mean(dim="presentation")
    assert "category_name" in hvm_it_v3_obj.indexes["presentation"].names
    assert "object_name" in hvm_it_v3_obj.indexes["presentation"].names


def test_stimulus_set_from_assembly(brainio_home):
    assy_hvm = brainio.get_assembly(identifier="dicarlo.MajajHong2015.public")
    stimulus_set = assy_hvm.attrs["stimulus_set"]
    assert stimulus_set.shape[0] == np.unique(assy_hvm["image_id"]).shape[0]
    for stimulus_id in stimulus_set['stimulus_id']:
        stimulus_path = stimulus_set.get_stimulus(stimulus_id)
        assert os.path.exists(stimulus_path)


def test_inplace():
    d = xr.DataArray(0, None, None, None, None, None, False)
    with pytest.raises(TypeError) as te:
        d = d.reset_index(None, inplace=True)
    assert "inplace" in str(te.value)


@pytest.mark.parametrize('assembly,shape,nans', [
    pytest.param('dicarlo.BashivanKar2019.naturalistic', (24320, 233, 1), 309760, marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.synthetic', (21360, 233, 1), 4319940, marks=[pytest.mark.private_access]),
])
def test_synthetic(assembly, shape, nans, brainio_home_session):
    assy = brainio.get_assembly(assembly)
    assert assy.shape == shape
    assert np.count_nonzero(np.isnan(assy)) == nans


class TestFromFiles:
    def test_from_files(self, test_stimulus_set_identifier):
        p = get_nc_path()
        s = StimulusSet.from_files(get_csv_path(), get_dir_path())
        a = DataAssembly.from_files(p, stimulus_set_identifier=test_stimulus_set_identifier, stimulus_set=s)
        assert a.shape == (6, 3)

    def test_load_extras(self, test_stimulus_set_identifier):
        p = get_nc_extras_path()
        s = StimulusSet.from_files(get_csv_path(), get_dir_path())
        a = SpikeTimesAssembly.from_files(p, stimulus_set_identifier=test_stimulus_set_identifier, stimulus_set=s)
        assert isinstance(a, SpikeTimesAssembly)
        assert a.shape == (1000,)
        assert "test" in a.attrs
        extra = a.attrs["test"]
        assert extra is not None
        assert isinstance(extra, MetadataAssembly)
        assert "stimulus_set" in extra.attrs
        assert extra.shape == (40,)




