from collections import OrderedDict, defaultdict

import itertools
import numpy as np
import xarray as xr
from xarray import DataArray, IndexVariable


def is_fastpath(*args, **kwargs):
    """checks whether a set of args and kwargs would be interpreted by DataArray.__init__"""
    n = 7 # maximum length of args if all arguments to DataArray are positional (as of 0.16.1)
    return ("fastpath" in kwargs and kwargs["fastpath"]) or (len(args) >= n and args[n-1])


class DataPoint(object):
    """A DataPoint represents one value, usually a recording from one neuron or node,
    in response to one presentation of a stimulus.  """

    def __init__(self, value, neuroid, presentation):
        self.value = value
        self.neuroid = neuroid
        self.presentation = presentation


class DataAssembly(DataArray):
    """A DataAssembly represents a set of data a researcher wishes to work with for
    an analysis or benchmarking task.  """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        if is_fastpath(*args, **kwargs):
            # DataArray.__init__ follows a very different code path if fastpath=True
            # gather_indexes is not necessary in those cases
            super(DataAssembly, self).__init__(*args, **kwargs)
        else:
            # We call gather_indexes so we can guarantee that DataAssemblies will always have all metadata as indexes.
            # set_index, and thus gather_indexes, cannot operate on self in-place, it can only return a new object.
            # We take advantage of the almost-idempotence of DataArray.__init__ to gather indexes on a temporary
            # object and then initialize self with that.
            temp = DataArray(*args, **kwargs)
            temp = gather_indexes(temp)
            super(DataAssembly, self).__init__(temp)

    def multi_groupby(self, group_coord_names, *args, **kwargs):
        if len(group_coord_names) < 2:
            return self.groupby(group_coord_names[0], *args, **kwargs)
        multi_group_name = "multi_group"
        dim = self._dim_of_group_coords(group_coord_names)
        tmp_assy = self._join_group_coords(dim, group_coord_names, multi_group_name)
        result = tmp_assy.groupby(multi_group_name, *args, **kwargs)
        return GroupbyBridge(result, self, dim, group_coord_names, multi_group_name)

    def _join_group_coords(self, dim, group_coord_names, multi_group_name):
        class MultiCoord:
            # this is basically a list of key-values, but not treated as a list to avoid xarray complaints
            def __init__(self, values):
                self.values = tuple(values) if isinstance(values, list) else values

            def __eq__(self, other):
                return len(self.values) == len(other.values) and \
                       all(v1 == v2 for v1, v2 in zip(self.values, other.values))

            def __lt__(self, other):
                return self.values < other.values

            def __hash__(self):
                return hash(self.values)

            def __repr__(self):
                return repr(self.values)

        tmp_assy = self.copy()
        group_coords = [tmp_assy.coords[c].values.tolist() for c in group_coord_names]
        multi_group_coord = []
        for coords in zip(*group_coords):
            multi_group_coord.append(MultiCoord(coords))
        tmp_assy.coords[multi_group_name] = dim, multi_group_coord
        tmp_assy = tmp_assy.set_index(append=True, **{dim: multi_group_name})
        return tmp_assy

    def _dim_of_group_coords(self, group_coord_names):
        dimses = [self.coords[coord_name].dims for coord_name in group_coord_names]
        dims = [dim for dim_tuple in dimses for dim in dim_tuple]
        if len(set(dims)) == 1:
            return dims[0]
        else:
            raise GroupbyError("All coordinates for grouping must be associated with the same single dimension.  ")

    def multi_dim_apply(self, groups, apply):
        # align
        groups = sorted(groups, key=lambda group: self.dims.index(self[group].dims[0]))
        # build indices
        groups = {group: np.unique(self[group]) for group in groups}
        group_dims = {self[group].dims: group for group in groups}
        indices = defaultdict(lambda: defaultdict(list))
        result_indices = defaultdict(lambda: defaultdict(list))
        for group in groups:
            for index, value in enumerate(self[group].values):
                indices[group][value].append(index)
                # result_indices
                index = max(itertools.chain(*result_indices[group].values())) + 1 \
                    if len(result_indices[group]) > 0 else 0
                result_indices[group][value].append(index)

        coords = {coord: (dims, value) for coord, dims, value in walk_coords(self)}

        def simplify(value):
            return value.item() if value.size == 1 else value

        def indexify(dict_indices):
            return tuple((i,) if isinstance(i, int) else tuple(i) for i in dict_indices.values())

        # group and apply
        # making this a DataArray right away and then inserting through .loc would slow things down
        shapes = {group: len(list(itertools.chain(*indices.values()))) for group, indices in result_indices.items()}
        result = np.zeros(list(shapes.values()))
        result_coords = {coord: (dims, (np.array([None] * shapes[group_dims[dims]])
                                        # deal with non-indexing coords (typically remnants from `.sel(coord=x)`)
                                        if dims else value))
                         for coord, (dims, value) in coords.items()}
        for values in itertools.product(*groups.values()):
            group_values = dict(zip(groups.keys(), values))
            self_indices = {group: indices[group][value] for group, value in group_values.items()}
            values_indices = indexify(self_indices)
            cells = self.values[values_indices]  # using DataArray would slow things down. thus we pass coords as kwargs
            cells = simplify(cells)
            cell_coords = {coord: (dims,
                                   value[self_indices[group_dims[dims]]]
                                   if dims else value)  # deal with non-indexing coords
                           for coord, (dims, value) in coords.items()}
            cell_coords = {coord: (dims, simplify(value)) for coord, (dims, value) in cell_coords.items()}

            # ignore dims when passing to function
            passed_coords = {coord: value for coord, (dims, value) in cell_coords.items()}
            merge = apply(cells, **passed_coords)
            result_idx = {group: result_indices[group][value] for group, value in group_values.items()}
            result[indexify(result_idx)] = merge
            for coord, (dims, value) in cell_coords.items():
                assert dims == result_coords[coord][0]
                if not dims:  # non-indexing coord
                    continue
                coord_index = result_idx[group_dims[dims]]
                result_coords[coord][1][coord_index] = value

        # re-package
        result = type(self)(result, coords=result_coords, dims=list(itertools.chain(*group_dims.keys())))
        return result

    def multisel(self, method=None, tolerance=None, drop=False, **indexers):
        """
        partial workaround to keep multi-indexes and scalar coords
        https://github.com/pydata/xarray/issues/1491, https://github.com/pydata/xarray/pull/1426
        this method might slow things down, use with caution
        """
        indexer_dims = {index: self[index].dims for index in indexers}
        dims = []
        for _dims in indexer_dims.values():
            assert len(_dims) == 1
            dims.append(_dims[0])
        coords_dim, dim_coords = {}, defaultdict(list)
        for dim in dims:
            for coord, coord_dims, _ in walk_coords(self):
                if array_is_element(coord_dims, dim):
                    coords_dim[coord] = dim
                    dim_coords[dim].append(coord)

        result = super().sel(method=method, tolerance=tolerance, drop=drop, **indexers)

        # un-drop potentially dropped dims
        for coord, value in indexers.items():
            dim = self[coord].dims
            assert len(dim) == 1
            dim = dim[0]
            if not hasattr(result, coord) and dim not in result.dims:
                result = result.expand_dims(coord)
                result[coord] = [value]

        # stack back together
        stack_dims = list(result.dims)
        for result_dim in stack_dims:
            if result_dim not in self.dims:
                original_dim = coords_dim[result_dim]
                stack_coords = [coord for coord in dim_coords[original_dim] if hasattr(result, coord)]
                for coord in stack_coords:
                    stack_dims.remove(coord)
                result = result.stack(**{original_dim: stack_coords})
        # add scalar indexer variable
        for index, value in indexers.items():
            if hasattr(result, index):
                continue  # already set, potentially during un-dropping
            dim = indexer_dims[index]
            assert len(dim) == 1
            value = np.repeat(value, len(result[dim[0]]))
            result[index] = dim, value
        return result


class BehavioralAssembly(DataAssembly):
    """A BehavioralAssembly is a DataAssembly containing behavioral data.  """
    __slots__ = ()


class NeuroidAssembly(DataAssembly):
    """A NeuroidAssembly is a DataAssembly containing data recorded from either neurons
    or neuron analogues.  """
    __slots__ = ()


class NeuronRecordingAssembly(NeuroidAssembly):
    """A NeuronRecordingAssembly is a NeuroidAssembly containing data recorded from neurons.  """
    __slots__ = ()


class ModelFeaturesAssembly(NeuroidAssembly):
    """A ModelFeaturesAssembly is a NeuroidAssembly containing data captured from nodes in
    a machine learning model.  """
    __slots__ = ()


class PropertyAssembly(DataAssembly):
    """A PropertyAssembly is a DataAssembly containing single neuronal properties data.  """
    __slots__ = ()


def coords_for_dim(xr_data, dim, exclude_indexes=True):
    result = OrderedDict()
    for key, value in xr_data.coords.variables.items():
        only_this_dim = value.dims == (dim,)
        exclude_because_index = exclude_indexes and isinstance(value, xr.IndexVariable)
        if only_this_dim and not exclude_because_index:
            result[key] = value
    return result


def gather_indexes(xr_data):
    """This is only necessary as long as xarray cannot persist MultiIndex to netCDF.  """
    coords_d = {}
    for dim in xr_data.dims:
        coords = coords_for_dim(xr_data, dim)
        if coords:
            coords_d[dim] = list(coords.keys())
    if coords_d:
        xr_data = xr_data.set_index(append=True, **coords_d)
    return xr_data


class GroupbyBridge(object):
    """Wraps an xarray GroupBy object to allow grouping on multiple coordinates.   """

    def __init__(self, groupby, assembly, dim, group_coord_names, multi_group_name):
        self.groupby = groupby
        self.assembly = assembly
        self.dim = dim
        self.group_coord_names = group_coord_names
        self.multi_group_name = multi_group_name

    def __getattr__(self, attr):
        result = getattr(self.groupby, attr)
        if callable(result):
            result = self.wrap_groupby(result)
        return result

    def wrap_groupby(self, func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, type(self.assembly)):
                result = self.split_group_coords(result)
            return result

        return wrapper

    def split_group_coords(self, result):
        split_coords = [multi_coord.values for multi_coord in result.coords[self.multi_group_name].values]
        split_coords = list(map(list, zip(*split_coords)))  # transpose
        for coord_name, coord in zip(self.group_coord_names, split_coords):
            result.coords[coord_name] = (self.multi_group_name, coord)
        result_type = type(result)
        result = xr.DataArray(result).reset_index(self.multi_group_name, drop=True)
        result = result_type(result.set_index(append=True, **{self.multi_group_name: list(self.group_coord_names)}))
        result = result.rename({self.multi_group_name: self.dim})
        return result


class GroupbyError(Exception):
    pass


def merge_data_arrays(data_arrays):
    # https://stackoverflow.com/a/50125997/2225200
    merged = xr.merge((data_array.rename('z') for data_array in data_arrays))['z'].rename(None)
    # ensure same class
    return type(data_arrays[0])(merged)


def array_is_element(arr, element):
    return len(arr) == 1 and arr[0] == element


def walk_coords(assembly):
    """
    walks through coords and all levels, just like the `__repr__` function, yielding `(name, dims, values)`.
    """
    coords = {}

    for name in assembly.coords.variables:
        values = assembly.coords.variables[name]
        is_index = isinstance(values, IndexVariable)
        if is_index and values.level_names:
            for level in values.level_names:
                level_values = assembly.coords[level]
                yield level, level_values.dims, level_values.values
        else:
            yield name, values.dims, values.values
    return coords


def get_levels(assembly):
    levels = []
    for key, value in assembly.coords.variables.items():
        if isinstance(value, IndexVariable) and value.level_names:
            for level in value.level_names:
                levels.append(level)
    return levels