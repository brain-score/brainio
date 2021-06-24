import intake
from intake.source.base import DataSource
from intake.container.base import RemoteSource

class BrainIOStimulusSetSource(DataSource):
    container = ""


class RemoteBrainIOStimulusSet(RemoteSource):
    """
    A BrainIO data source
    """
    name = 'remote-brainio-stimulus-set'
    container = 'brainio-stimulus-set'

    def __init__(self, url, headers, **kwargs):
        """
        RemoteBrainIOStimulusSet
        """
        import xarray as xr
        super(RemoteBrainIOStimulusSet, self).__init__(url, headers, **kwargs)
        self._schema = None
        self._ds = xr.open_zarr(self.metadata['internal'])

    def _get_schema(self):
        """
        
        """
        import dask.array as da
        if self._schema is None:
            metadata = {
                'dims': dict(self._ds.dims),
                'data_vars': {k: list(self._ds[k].coords)
                              for k in self._ds.data_vars.keys()},
                'coords': tuple(self._ds.coords.keys()),
            }
            if getattr(self, 'on_server', False):
                metadata['internal'] = serialize_zarr_ds(self._ds)
            metadata.update(self._ds.attrs)
            self._schema = Schema(
                datashape=None,
                dtype=None,
                shape=None,
                npartitions=None,
                extra_metadata=metadata)
            # aparently can't replace coords in-place
            # we immediately fetch the values of coordinates
            # TODO: in the future, these could be functions from the metadata?
            self._ds = self._ds.assign_coords(**{c: self._get_partition((c, ))
                                                 for c in metadata['coords']})
            for var in list(self._ds.data_vars):
                # recreate dask arrays
                name = '-'.join(['remote-xarray', var, self._source_id])
                arr = self._ds[var].data
                chunks = arr.chunks
                nparts = (range(len(n)) for n in chunks)
                if self.metadata.get('array', False):
                    # original was an array, not dataset - no variable name
                    extra = ()
                else:
                    extra = (var, )
                dask = {
                    (name, ) + part: (get_partition, self.url, self.headers,
                                      self._source_id, self.container,
                                      extra + part)

                    for part in itertools.product(*nparts)
                }
                self._ds[var].data = da.Array(
                    dask,
                    name,
                    chunks,
                    dtype=arr.dtype,
                    shape=arr.shape)
            if self.metadata.get('array', False):
                self._ds = self._ds[self.metadata.get('array')]
        return self._schema

    def _get_partition(self, i):
        """
        The partition should look like ("var_name", int, int...), where the
        number of ints matches the number of coordinate axes in the named
        variable, and is between 0 and the number of chunks in each axis. For
        an array, as opposed to a dataset, omit the variable name.
        """
        return get_partition(self.url, self.headers, self._source_id,
                             self.container, i)

    def to_dask(self):
        self._get_schema()
        return self._ds

    def read_chunked(self):
        """The dask repr is the authoritative chunked version"""
        self._get_schema()
        return self._ds

    def read(self):
        self._get_schema()
        return self._ds.load()

    def close(self):
        self._ds = None
        self._schema = None


intake.register_driver('remote-brainio-stimulus-set', RemoteBrainIOStimulusSet)
intake.register_container('brainio-stimulus-set', RemoteBrainIOStimulusSet)
