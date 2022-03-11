import logging
import os
import zipfile
from pathlib import Path
import re
import mimetypes

import boto3
from tqdm import tqdm
import numpy as np
from PIL import Image

import brainio.assemblies
from brainio import lookup, list_stimulus_sets
from brainio.lookup import TYPE_ASSEMBLY, TYPE_STIMULUS_SET, sha1_hash

_logger = logging.getLogger(__name__)


def create_image_zip(proto_stimulus_set, target_zip_path):
    """
    Create zip file for images in StimulusSet.
    Files in the zip will follow a flat directory structure with each row's filename equal to the `image_id` by default,
        or `image_path_within_store` if passed.
    :param proto_stimulus_set: a `StimulusSet` with a `get_image: image_id -> local path` method, an `image_id` column,
        and optionally an `image_path_within_store` column.
    :param target_zip_path: path to write the zip file to
    :return: SHA1 hash of the zip file
    """
    _logger.debug(f"Zipping stimulus set to {target_zip_path}")
    os.makedirs(os.path.dirname(target_zip_path), exist_ok=True)
    arcnames = []
    with zipfile.ZipFile(target_zip_path, 'w') as target_zip:
        for _, row in proto_stimulus_set.iterrows():  # using iterrows instead of itertuples for very large StimulusSets
            image_path = proto_stimulus_set.get_image(row['image_id'])
            extension = os.path.splitext(image_path)[1]
            arcname = row['image_path_within_store'] if hasattr(row, 'image_path_within_store') else row['image_id']
            arcname = arcname + extension
            target_zip.write(image_path, arcname=arcname)
            arcnames.append(arcname)
    sha1 = sha1_hash(target_zip_path)
    return sha1, arcnames


def upload_to_s3(source_file_path, bucket_name, target_s3_key):
    _logger.debug(f"Uploading {source_file_path} to {bucket_name}/{target_s3_key}")

    file_size = os.path.getsize(source_file_path)
    with tqdm(total=file_size, unit='B', unit_scale=True, desc="upload to s3") as progress_bar:
        def progress_hook(bytes_amount):
            if bytes_amount > 0:  # at the end, this sometimes passes a negative byte amount which tqdm can't handle
                progress_bar.update(bytes_amount)

        client = boto3.client('s3')
        client.upload_file(str(source_file_path), bucket_name, target_s3_key, Callback=progress_hook)


def extract_specific(proto_stimulus_set):
    general = ['image_current_local_file_path', 'image_path_within_store']
    stimulus_set_specific_attributes = set(proto_stimulus_set.columns) - set(general)
    return list(stimulus_set_specific_attributes)


def create_image_csv(proto_stimulus_set, target_path):
    _logger.debug(f"Writing csv to {target_path}")
    specific_columns = extract_specific(proto_stimulus_set)
    specific_stimulus_set = proto_stimulus_set[specific_columns]
    specific_stimulus_set.to_csv(target_path, index=False)
    sha1 = sha1_hash(target_path)
    return sha1


def check_naming_convention(name):
    assert re.match(r"[a-z]+\.[A-Z][a-zA-Z0-9]+", name)


def check_image_naming_convention(name):
    assert re.match(r"[a-zA-Z0-9]+_?(?!0)\d+\.(?:jpg|jpeg|png|mp4)|(?!0)\d+\.(?:jpg|jpeg|png|mp4)", name)


def check_image_format(image, identifier):
    assert image.mode in ['RGBA', 'RGB', 'LA', 'L'], f"{identifier}: incorrect image mode {image.mode}"
    image_shape = np.array(image).shape
    assert 3 == len(image_shape), f"{identifier}: incorrect shape {len(image_shape)}"

    channels = {'RGBA': 4, 'RGB': 3, 'LA': 2, 'L': 1}
    assert channels[image.mode] == image_shape[2], f"{identifier}: incorrect channels {image_shape[2]}"


def check_image_numbers(stimulus_set):
    image_numbers = [int(image_file_path[image_file_path.rfind('_') + 1:image_file_path.rfind('.')])
                     for image_file_path in list(stimulus_set.image_paths.values())]
    image_numbers.sort()
    for i in range(len(image_numbers) - 1):
        assert image_numbers[i] == image_numbers[i + 1] - 1, "StimulusSet files not sequentially numbered"


def check_experiment_stimulus_set(stimulus_set):
    """
    Checks the stimulus set files are non-corrupt and named/numbered sequentially. This function should only be called
    on stimulus sets that are pushed to the `brainio.requested` bucket.
    :param stimulus_set: A StimulusSet containing one row for each image, and the columns
    {'image_id', ['image_path_within_store' (optional to structure zip directory layout)]}
    and columns for all stimulus-set-specific metadata but not the column 'filename'.
    """
    assert len(stimulus_set['image_id']), "StimulusSet is empty"
    file_paths = list(stimulus_set.image_paths.values())

    file_type_0 = mimetypes.guess_type(file_paths[0])[0]

    for file_path in file_paths:
        check_image_naming_convention(file_path[file_path.rfind('/') + 1:])
        assert os.path.isfile(file_path), f"{file_path} does not exist"
        assert file_type_0 == mimetypes.guess_type(file_path)[0], f"{file_path} is a different media type than other stimuli in the StimulusSet"
        if file_type_0.startswith('image'):
            image = Image.open(file_path)
            check_image_format(image, file_path)

    check_image_numbers(stimulus_set)


def package_stimulus_set(catalog_name, proto_stimulus_set, stimulus_set_identifier, bucket_name="brainio-contrib"):
    """
    Package a set of images along with their metadata for the BrainIO system.
    :param catalog_name: The name of the lookup catalog to add the stimulus set to.
    :param proto_stimulus_set: A StimulusSet containing one row for each image,
        and the columns {'image_id', ['image_path_within_store' (optional to structure zip directory layout)]}
        and columns for all stimulus-set-specific metadata but not the column 'filename'.
    :param stimulus_set_identifier: A unique name identifying the stimulus set
        <lab identifier>.<first author e.g. 'Rajalingham' or 'MajajHong' for shared first-author><YYYY year of publication>.
    :param bucket_name: 'brainio.dicarlo' for DiCarlo Lab stimulus sets, 'brainio.contrib' for external stimulus sets,
        'brainio.requested' for to-be-run-on-monkey-machine stimulus sets.
    """
    _logger.debug(f"Packaging {stimulus_set_identifier}")

    assert 'image_id' in proto_stimulus_set.columns, "StimulusSet needs to have an `image_id` column"

    if bucket_name == 'brainio.requested':
        check_experiment_stimulus_set(proto_stimulus_set)

    # naming
    image_store_identifier = "image_" + stimulus_set_identifier.replace(".", "_")
    # - csv
    csv_file_name = image_store_identifier + ".csv"
    target_csv_path = Path(__file__).parent / csv_file_name
    # - zip
    zip_file_name = image_store_identifier + ".zip"
    target_zip_path = Path(__file__).parent / zip_file_name
    # create csv and zip files
    image_zip_sha1, zip_filenames = create_image_zip(proto_stimulus_set, str(target_zip_path))
    assert 'filename' not in proto_stimulus_set.columns, "StimulusSet already has column 'filename'"
    proto_stimulus_set['filename'] = zip_filenames  # keep record of zip (or later local) filenames
    csv_sha1 = create_image_csv(proto_stimulus_set, str(target_csv_path))
    # upload both to S3
    upload_to_s3(str(target_csv_path), bucket_name, target_s3_key=csv_file_name)
    upload_to_s3(str(target_zip_path), bucket_name, target_s3_key=zip_file_name)
    # link to csv and zip from same identifier. The csv however is the only one of the two rows with a class.
    lookup.append(
        catalog_name=catalog_name,
        object_identifier=stimulus_set_identifier, cls='StimulusSet',
        lookup_type=TYPE_STIMULUS_SET,
        bucket_name=bucket_name, sha1=csv_sha1, s3_key=csv_file_name,
        stimulus_set_identifier=None
    )
    lookup.append(
        catalog_name=catalog_name,
        object_identifier=stimulus_set_identifier, cls=None,
        lookup_type=TYPE_STIMULUS_SET,
        bucket_name=bucket_name, sha1=image_zip_sha1, s3_key=zip_file_name,
        stimulus_set_identifier=None
    )
    _logger.debug(f"stimulus set {stimulus_set_identifier} packaged")


def write_netcdf(assembly, target_netcdf_file):
    _logger.debug(f"Writing assembly to {target_netcdf_file}")
    assembly = assembly.reset_index(list(assembly.indexes))
    assembly.to_netcdf(target_netcdf_file)
    sha1 = sha1_hash(target_netcdf_file)
    return sha1


def verify_assembly(assembly, assembly_class):
    if assembly_class is not "PropertyAssembly":
        assert 'presentation' in assembly.dims
        if assembly_class.startswith('Neur'):  # neural/neuron assemblies need to follow this format
            assert set(assembly.dims) == {'presentation', 'neuroid'} or \
                   set(assembly.dims) == {'presentation', 'neuroid', 'time_bin'}


def package_data_assembly(catalog_name, proto_data_assembly, assembly_identifier, stimulus_set_identifier,
                          assembly_class="NeuronRecordingAssembly", bucket_name="brainio-contrib"):
    """
    Package a set of data along with its metadata for the BrainIO system.
    :param catalog_name: The name of the lookup catalog to add the data assembly to.
    :param proto_data_assembly: An xarray DataArray containing experimental measurements and all related metadata.
        * The dimensions of a neural DataArray must be
            * presentation
            * neuroid
            * time_bin
            A behavioral DataArray should also have a presentation dimension, but can be flexible about its other dimensions.
        * The presentation dimension must have an image_id coordinate and should have coordinates for presentation-level metadata such as repetition and image_id.
          The presentation dimension should not have coordinates for image-specific metadata, these will be drawn from the StimulusSet based on image_id.
        * The neuroid dimension must have a neuroid_id coordinate and should have coordinates for as much neural metadata as possible (e.g. region, subregion, animal, row in array, column in array, etc.)
        * The time_bin dimension should have coordinates time_bin_start and time_bin_end.
    :param assembly_identifier: A dot-separated string starting with a lab identifier.
        * For published: <lab identifier>.<first author e.g. 'Rajalingham' or 'MajajHong' for shared first-author><YYYY year of publication>
        * For requests: <lab identifier>.<b for behavioral|n for neuroidal>.<m for monkey|h for human>.<proposer e.g. 'Margalit'>.<pull request number>
    :param stimulus_set_identifier: The unique name of an existing StimulusSet in the BrainIO system.
    :param assembly_class: The name of a DataAssembly subclass.
    :param bucket_name: 'brainio-dicarlo' for DiCarlo Lab assemblies, 'brainio-contrib' for external assemblies.
    """
    _logger.debug(f"Packaging {assembly_identifier}")

    # verify
    verify_assembly(proto_data_assembly, assembly_class=assembly_class)
    assert hasattr(brainio.assemblies, assembly_class)
    assert stimulus_set_identifier in list_stimulus_sets(), \
        f"StimulusSet {stimulus_set_identifier} not found in packaged stimulus sets"

    # identifiers
    assembly_store_identifier = "assy_" + assembly_identifier.replace(".", "_")
    netcdf_file_name = assembly_store_identifier + ".nc"
    target_netcdf_path = Path(__file__).parent / netcdf_file_name
    s3_key = netcdf_file_name

    # execute
    netcdf_kf_sha1 = write_netcdf(proto_data_assembly, target_netcdf_path)
    upload_to_s3(target_netcdf_path, bucket_name, s3_key)
    lookup.append(
        catalog_name=catalog_name,
        object_identifier=assembly_identifier, stimulus_set_identifier=stimulus_set_identifier,
        lookup_type=TYPE_ASSEMBLY,
        bucket_name=bucket_name, sha1=netcdf_kf_sha1,
        s3_key=s3_key, cls=assembly_class
    )
    _logger.debug(f"assembly {assembly_identifier} packaged")
