from pathlib import Path
import os

import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

import brainio
from pandas import DataFrame

from brainio.assemblies import DataAssembly, get_levels
from brainio.stimuli import StimulusSet
from brainio.packaging import write_netcdf, check_stimulus_numbers, check_stimulus_naming_convention, TYPE_ASSEMBLY, \
    package_stimulus_set, package_data_assembly, get_user_info, upload_to_s3
import brainio.lookup as lookup
from tests.conftest import make_stimulus_set_df, make_spk_assembly, make_meta_assembly, BUCKET_NAME


def test_write_netcdf(test_write_netcdf_path):
    assy = DataAssembly(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]],
        coords={
            'up': ("a", ['alpha', 'alpha', 'beta', 'beta', 'beta', 'beta']),
            'down': ("a", [1, 1, 1, 1, 2, 2]),
            'sideways': ('b', ['x', 'y', 'z'])
        },
        dims=['a', 'b']
    )
    netcdf_sha1 = write_netcdf(assy, str(test_write_netcdf_path))
    assert test_write_netcdf_path.exists()


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
    assert get_levels(assy) == ["sideways"]
    assy = assy.reset_index(["sideways"])
    assert get_levels(assy) == []


def test_stimulus_numbers():
    stimulus_set = StimulusSet(DataFrame({'stimulus_id': [0, 1]}))
    filenames = ['Nat300_1.png', 'Nat300_2.png']
    assert len(stimulus_set) == len(filenames)
    stimulus_set.stimulus_paths = {stimulus_set.at[idx, 'stimulus_id']: filenames[idx]
                                   for idx in range(len(stimulus_set))}

    check_stimulus_numbers(stimulus_set)


def test_stimulus_naming_convention():
    for name in ['image_1.png', 'Nat300_100.png', '1.png']:
        check_stimulus_naming_convention(name)


def test_list_catalogs(test_catalog_identifier):
    catalog_names = lookup.list_catalogs()
    assert test_catalog_identifier in catalog_names


def test_append(test_catalog_identifier, test_write_netcdf_path, restore_this_file):
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
    netcdf_sha1 = write_netcdf(assy, str(test_write_netcdf_path))
    catalog = lookup.get_catalogs()[test_catalog_identifier]
    print(catalog.attrs['source_path'])
    restore_this_file(catalog.attrs['source_path'])
    catalog = lookup.append(test_catalog_identifier, identifier, "DataAssembly", TYPE_ASSEMBLY, "brainio-temp",
                            netcdf_sha1, "assy_test_append.nc", "dicarlo.hvm")
    assert identifier in list(catalog["identifier"])
    assert identifier in lookup.list_assemblies()


@pytest.mark.private_access
def test_package_stimulus_set(test_stimulus_set_identifier, test_catalog_identifier, brainio_home, restore_this_file,
                              restore_catalog):
    stimulus_set = StimulusSet(make_stimulus_set_df())
    stimulus_set.stimulus_paths = {row["stimulus_id"]: Path(__file__).parent / f'images/{row["filename"]}'
                                   for _, row in stimulus_set.iterrows()}
    del stimulus_set["filename"]
    identifier = test_stimulus_set_identifier
    restore_catalog(test_catalog_identifier)
    package_stimulus_set(test_catalog_identifier, stimulus_set, identifier, bucket_name=BUCKET_NAME)
    assert identifier in lookup.list_stimulus_sets()
    gotten = brainio.get_stimulus_set(identifier)
    assert gotten is not None
    assert gotten.shape == (10, 3)
    catalog = lookup.get_catalog(test_catalog_identifier)
    assert 'lookup_source' not in catalog
    assert 'source_catalog' not in catalog


@pytest.mark.private_access
def test_package_data_assembly(test_stimulus_set_identifier, test_catalog_identifier, brainio_home,
                               restore_this_file, restore_catalog):
    catalog = lookup.get_catalog(test_catalog_identifier)
    assert 'lookup_source' not in catalog
    assert 'source_catalog' not in catalog
    stimulus_set = StimulusSet(make_stimulus_set_df())
    stimulus_set.stimulus_paths = {row["stimulus_id"]: Path(__file__).parent / f'images/{row["filename"]}'
                                   for _, row in stimulus_set.iterrows()}
    del stimulus_set["filename"]
    identifier = test_stimulus_set_identifier
    restore_catalog(test_catalog_identifier)
    package_stimulus_set(test_catalog_identifier, stimulus_set, identifier, bucket_name=BUCKET_NAME)
    assy = DataAssembly(
        data=[[[1], [2], [3]], [[4], [5], [6]], [[7], [8], [9]], [[10], [11], [12]], [[13], [14], [15]], [[16], [17], [18]]],
        coords={
            'stimulus_id': ("presentation", ["n"+str(i) for i in range(6)]),
            'stimulus_type': ("presentation", ["foo"]*6),
            'neuroid_id': ("neuroid", list("ABC")),
            'neuroid_type': ("neuroid", ["bar"]*3),
            'time_bin_start': ('time_bin', [0]),
            'time_bin_end': ('time_bin', [10]),
        },
        dims=['presentation', 'neuroid', 'time_bin']
    )
    identifier = "test.package_assembly"
    package_data_assembly(
        test_catalog_identifier, assy, identifier, test_stimulus_set_identifier, "DataAssembly", "brainio-temp")
    assert identifier in lookup.list_assemblies()
    gotten = brainio.get_assembly(identifier)
    assert gotten is not None
    assert gotten.shape == (6, 3, 1)
    catalog = lookup.get_catalog(test_catalog_identifier)
    assert 'lookup_source' not in catalog
    assert 'source_catalog' not in catalog


@pytest.mark.private_access
def test_package_extras(test_stimulus_set_identifier, test_catalog_identifier, brainio_home,
                        restore_catalog):
    stimulus_set = StimulusSet(make_stimulus_set_df())
    stimulus_set.stimulus_paths = {row["stimulus_id"]: Path(__file__).parent / f'images/{row["filename"]}'
                                   for _, row in stimulus_set.iterrows()}
    del stimulus_set["filename"]
    identifier = test_stimulus_set_identifier
    restore_catalog(test_catalog_identifier)
    package_stimulus_set(test_catalog_identifier, stimulus_set, identifier, bucket_name=BUCKET_NAME)
    assy = make_spk_assembly()
    identifier = "test.package_assembly_extras"
    assy_extra = make_meta_assembly()
    assy_extra.name = "test"
    extras = {assy_extra.name: assy_extra}
    package_data_assembly(test_catalog_identifier, assy, identifier, test_stimulus_set_identifier,
                          "SpikeTimesAssembly", "brainio-temp", extras)
    assert identifier in lookup.list_assemblies()
    gotten = brainio.get_assembly(identifier)
    assert gotten is not None
    assert gotten.attrs["test"] is not None
    assert gotten.attrs["test"].shape == (40,)


def test_compression(test_write_netcdf_path):
    write_netcdf(make_spk_assembly(6), test_write_netcdf_path, compress=False)
    uncompressed = test_write_netcdf_path.stat().st_size
    write_netcdf(make_spk_assembly(6), test_write_netcdf_path, compress=True)
    compressed = test_write_netcdf_path.stat().st_size
    assert uncompressed > compressed


@mock_aws
def test_get_user_info():
    client = boto3.client('sts', region_name='us-east-1')

    # mocking the get_caller_identity method on the client instance
    with patch('brainio.packaging.boto3.client') as mock_boto_client:
        mock_boto_client.return_value = client

        with patch.object(client, 'get_caller_identity', return_value={
            'Account': '123456789012',
            'Arn': 'arn:aws:iam::123456789012:user/testuser',
            'UserId': 'ABCDEFGHIJKLMNO:testuser'
        }):
            account_id, username = get_user_info(client)
            assert account_id == '123456789012'
            assert username == 'testuser'


@mock_aws
@patch('brainio.packaging.tqdm')
@patch('os.path.getsize', return_value=1000)
def test_upload_to_s3(mock_getsize, mock_tqdm):
    # set up mocks
    mock_tqdm_instance = MagicMock()
    mock_tqdm.return_value = mock_tqdm_instance
    s3_client = boto3.client('s3', region_name='us-east-1')
    sts_client = boto3.client('sts', region_name='us-east-1')

    # crreate test bucket and file
    s3_client.create_bucket(Bucket='test-bucket')
    source_file_path = Path('files/testfile.txt')
    bucket_name = 'test-bucket'
    target_s3_key = 'testfile.txt'
    os.makedirs(source_file_path.parent, exist_ok=True)
    with open(source_file_path, 'w') as f:
        f.write("dummy content")

    # mock STS response
    with patch.object(sts_client, 'get_caller_identity', return_value={
        'Account': '123456789012',
        'Arn': 'arn:aws:iam::123456789012:user/testuser',
        'UserId': 'ABCDEFGHIJKLMNO:testuser'
    }):
        # patch get_user_info to return the expected user
        with patch('brainio.packaging.get_user_info', return_value=('123456789012', 'testuser')):
            object_properties = upload_to_s3(source_file_path, bucket_name, target_s3_key)

            # after upload, check that tagging worked
            tag_set = s3_client.get_object_tagging(Bucket=bucket_name, Key=target_s3_key)['TagSet']
            expected_tag = {'Key': 'uploadedBy', 'Value': 'testuser'}
            assert expected_tag in tag_set
            mock_tqdm.assert_called_once_with(total=1000, unit='B', unit_scale=True, desc='upload to s3')

    # clean up dummy file
    os.remove(source_file_path)

