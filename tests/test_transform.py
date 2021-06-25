import numpy as np
import pytest
import xarray as xr
from brainio import get_assembly

from brainio.assemblies import NeuroidAssembly
from brainio.transform import subset, index_efficient


class TestSubset:
    def test_equal(self):
        assembly = np.random.rand(100, 3)
        assembly = NeuroidAssembly(assembly, coords={
            'image_id': list(range(assembly.shape[0])),
            'neuroid_id': list(range(assembly.shape[1]))},
                                   dims=['image_id', 'neuroid_id'])
        assembly = assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))
        subset_assembly = subset(assembly, assembly, subset_dims=('presentation',))
        assert (subset_assembly == assembly).all()

    def test_equal_shifted(self):
        target_assembly = np.random.rand(100, 3)
        target_assembly = NeuroidAssembly(target_assembly, coords={
            'image_id': list(range(target_assembly.shape[0])),
            'neuroid_id': list(range(target_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        target_assembly = target_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        shifted_values = np.concatenate((target_assembly.values[1:], target_assembly.values[:1]))
        shifed_ids = np.array(list(range(shifted_values.shape[0]))) + 1
        shifed_ids[-1] = 0
        source_assembly = NeuroidAssembly(shifted_values, coords={
            'image_id': shifed_ids,
            'neuroid_id': list(range(shifted_values.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        source_assembly = source_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',))
        np.testing.assert_array_equal(subset_assembly.coords.keys(), target_assembly.coords.keys())
        assert subset_assembly.shape == target_assembly.shape

    def test_smaller_first(self):
        source_assembly = np.random.rand(100, 3)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': list(range(source_assembly.shape[0])),
            'neuroid_id': list(range(source_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        source_assembly = source_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        target_assembly = source_assembly.sel(presentation=list(map(lambda x: (x,), range(50))),
                                              neuroid=list(map(lambda x: (x,), range(2))))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',))
        np.testing.assert_array_equal(subset_assembly.coords.keys(), target_assembly.coords.keys())
        for coord_name in target_assembly.coords:
            assert all(subset_assembly[coord_name] == target_assembly[coord_name])
        assert (subset_assembly == target_assembly).all()

    def test_smaller_last(self):
        source_assembly = np.random.rand(100, 3)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': list(range(source_assembly.shape[0])),
            'neuroid_id': list(range(source_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        source_assembly = source_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        target_assembly = source_assembly.sel(presentation=list(map(lambda x: (50 + x,), range(50))),
                                              neuroid=list(map(lambda x: (1 + x,), range(2))))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',))
        np.testing.assert_array_equal(subset_assembly.coords.keys(), target_assembly.coords.keys())
        for coord_name in target_assembly.coords:
            assert all(subset_assembly[coord_name] == target_assembly[coord_name])
        assert (subset_assembly == target_assembly).all()

    def test_larger_error(self):
        source_assembly = np.random.rand(50, 2)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': list(range(source_assembly.shape[0])),
            'neuroid_id': list(range(source_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        source_assembly = source_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        target_assembly = np.random.rand(100, 3)
        target_assembly = NeuroidAssembly(target_assembly, coords={
            'image_id': list(range(target_assembly.shape[0])),
            'neuroid_id': list(range(target_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        target_assembly = target_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        with pytest.raises(Exception):
            subset(source_assembly, target_assembly, subset_dims=('presentation',))

    def test_repeated_target(self):
        source_assembly = np.random.rand(5, 3)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': list(range(source_assembly.shape[0])),
            'neuroid_id': list(range(source_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        source_assembly = source_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        target_assembly = NeuroidAssembly(np.repeat(source_assembly, 2, axis=0), coords={
            'image_id': np.repeat(list(range(source_assembly.shape[0])), 2, axis=0),
            'neuroid_id': list(range(source_assembly.shape[1]))},
                                          dims=['image_id', 'neuroid_id'])
        target_assembly = target_assembly.stack(presentation=('image_id',), neuroid=('neuroid_id',))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',), repeat=True)
        np.testing.assert_array_equal(subset_assembly.coords.keys(), target_assembly.coords.keys())
        for coord_name in target_assembly.coords:
            assert all(subset_assembly[coord_name] == target_assembly[coord_name])
        np.testing.assert_array_equal(subset_assembly, target_assembly)
        assert (subset_assembly == target_assembly).all()

    @pytest.mark.private_access
    def test_category_subselection(self):
        assembly = get_assembly('dicarlo.MajajHong2015')
        categories = np.unique(assembly['category_name'])
        target = xr.DataArray([0] * len(categories), coords={'category_name': categories},
                              dims=['category_name']).stack(presentation=['category_name'])
        sub_assembly = subset(assembly, target, repeat=True, dims_must_match=False)
        assert (assembly == sub_assembly).all()

    def test_repeated_dim(self):
        source_assembly = np.random.rand(5, 5)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': ('presentation', list(range(source_assembly.shape[0]))),
            'image_meta': ('presentation', np.zeros(source_assembly.shape[0]))},
                                          dims=['presentation', 'presentation'])

        target_assembly = NeuroidAssembly(np.zeros(3), coords={
            'image_id': [0, 2, 3]}, dims=['image_id']).stack(presentation=('image_id',))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',), repeat=True)
        np.testing.assert_array_equal(subset_assembly.shape, (3, 3))
        assert set(subset_assembly['image_id'].values) == set(target_assembly['image_id'].values)

    def test_repeated_dim_and_adjacent(self):
        source_assembly = np.random.rand(5, 5)
        source_assembly = NeuroidAssembly(source_assembly, coords={
            'image_id': ('presentation', list(range(source_assembly.shape[0]))),
            'image_meta': ('presentation', np.zeros(source_assembly.shape[0])),
            'adjacent': 12},
                                          dims=['presentation', 'presentation'])

        target_assembly = NeuroidAssembly(np.zeros(3), coords={
            'image_id': [0, 2, 3]}, dims=['image_id']).stack(presentation=('image_id',))

        subset_assembly = subset(source_assembly, target_assembly, subset_dims=('presentation',), repeat=True)
        np.testing.assert_array_equal(subset_assembly.shape, (3, 3))
        assert set(subset_assembly['image_id'].values) == set(target_assembly['image_id'].values)
        assert subset_assembly['adjacent'] == 12


class TestIndexEfficient:
    def test(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([1, 1, 3, 4, 4, 4, 5])
        indexer = [a.tolist().index(target_val) for target_val in b]
        indexer = [index for index in indexer if index != -1]
        result = index_efficient(a, b)
        assert result == indexer
