import hashlib
import logging
from pathlib import Path

import entrypoints
import numpy as np
import pandas as pd

_logger = logging.getLogger(__name__)

ENTRYPOINT = "brainio_lookups"
TYPE_ASSEMBLY = 'assembly'
TYPE_STIMULUS_SET = 'stimulus_set'
CATALOG_PATH_KEY = "catalog_path"
_catalogs = {}
_concat_catalogs = None


def list_catalogs():
    return list(entrypoints.get_group_named(ENTRYPOINT).keys())


def load_lookup(name, entry_point):
    df = entry_point.load()()
    df["lookup_source"] = name
    return df


def get_lookups():
    lookups = entrypoints.get_group_named(ENTRYPOINT)
    dfs = {}
    for k, v in lookups.items():
        df = load_lookup(k, v)
        dfs[k] = df
    return dfs


def get_catalogs():
    global _catalogs
    if not _catalogs:
        _logger.debug(f"Loading lookup from entrypoints")
        print(f"Loading lookup from entrypoints")
        _catalogs = get_lookups()
    return _catalogs


def data():
    global _concat_catalogs
    if _concat_catalogs is None:
        catalogs = get_catalogs()
        _concat_catalogs = pd.concat(catalogs.values(), ignore_index=True)
    return _concat_catalogs


def list_stimulus_sets():
    stimuli_rows = data()[data()['lookup_type'] == TYPE_STIMULUS_SET]
    return list(set(stimuli_rows['identifier']))


def list_assemblies():
    assembly_rows = data()[data()['lookup_type'] == TYPE_ASSEMBLY]
    return list(assembly_rows['identifier'])


def lookup_stimulus_set(identifier):
    lookup = data()[(data()['identifier'] == identifier) & (data()['lookup_type'] == TYPE_STIMULUS_SET)]
    if len(lookup) == 0:
        raise StimulusSetLookupError(f"stimulus_set {identifier} not found")
    if len(lookup) > 2:
        raise RuntimeError(
            f"Internal data inconsistency: Found more than 2 lookup rows for stimulus_set identifier {identifier}")
    csv_lookup = [lookup_row for _, lookup_row in lookup.iterrows() if _is_csv_lookup(lookup_row)]
    zip_lookup = [lookup_row for _, lookup_row in lookup.iterrows() if _is_zip_lookup(lookup_row)]
    assert len(csv_lookup) == 1 and len(zip_lookup) == 1
    csv_lookup, zip_lookup = csv_lookup[0], zip_lookup[0]
    return csv_lookup, zip_lookup


def lookup_assembly(identifier):
    lookup = data()[(data()['identifier'] == identifier) & (data()['lookup_type'] == TYPE_ASSEMBLY)]
    if len(lookup) == 0:
        raise AssemblyLookupError(f"assembly {identifier} not found")
    if len(lookup) > 1:
        raise RuntimeError(f"Internal data inconsistency: Found multiple lookup rows for identifier {identifier}")
    lookup = lookup.squeeze()
    return lookup


class StimulusSetLookupError(KeyError):
    pass


class AssemblyLookupError(KeyError):
    pass


def append(catalog_name, object_identifier, cls, lookup_type,
           bucket_name, sha1, s3_key, stimulus_set_identifier=None):
    global _catalogs
    global _concat_catalogs
    catalogs = get_catalogs()
    catalog = catalogs[catalog_name]
    catalog_path = Path(catalog.attrs[CATALOG_PATH_KEY])
    _logger.debug(f"Adding {lookup_type} {object_identifier} to catalog {catalog_name}")
    object_lookup = {
        'identifier': object_identifier,
        'lookup_type': lookup_type,
        'class': cls,
        'location_type': "S3",
        'location': f"https://{bucket_name}.s3.amazonaws.com/{s3_key}",
        'sha1': sha1,
        'stimulus_set_identifier': stimulus_set_identifier,
        'lookup_source': catalog_name,
    }
    # check duplicates
    assert object_lookup['lookup_type'] in [TYPE_ASSEMBLY, TYPE_STIMULUS_SET]
    duplicates = catalog[(catalog['identifier'] == object_lookup['identifier']) &
                           (catalog['lookup_type'] == object_lookup['lookup_type'])]
    if len(duplicates) > 0:
        if object_lookup['lookup_type'] == TYPE_ASSEMBLY:
            raise ValueError(f"Trying to add duplicate identifier {object_lookup['identifier']}, "
                             f"existing \n{duplicates.to_string()}")
        elif object_lookup['lookup_type'] == TYPE_STIMULUS_SET:
            if len(duplicates) == 1 and duplicates.squeeze()['identifier'] == object_lookup['identifier'] and (
                    (_is_csv_lookup(duplicates.squeeze()) and _is_zip_lookup(object_lookup)) or
                    (_is_zip_lookup(duplicates.squeeze()) and _is_csv_lookup(object_lookup))):
                pass  # all good, we're just adding the second part of a stimulus set
            else:
                raise ValueError(
                    f"Trying to add duplicate identifier {object_lookup['identifier']}, existing {duplicates}")
    # append and save
    add_lookup = pd.DataFrame({key: [value] for key, value in object_lookup.items()})
    catalog = catalog.append(add_lookup)
    catalog.to_csv(catalog_path, index=False)
    _catalogs[catalog_name] = catalog
    _concat_catalogs = None


def _is_csv_lookup(data_row):
    return data_row['lookup_type'] == TYPE_STIMULUS_SET \
           and data_row['location'].endswith('.csv') \
           and data_row['class'] not in [None, np.nan]


def _is_zip_lookup(data_row):
    return data_row['lookup_type'] == TYPE_STIMULUS_SET \
           and data_row['location'].endswith('.zip') \
           and data_row['class'] in [None, np.nan]


def sha1_hash(path, buffer_size=64 * 2 ** 10):
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()
