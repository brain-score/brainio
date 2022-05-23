package_stimulus_set(catalog_name, proto_stimulus_set, stimulus_set_identifier, bucket_name="brainio-temp"):
    Package a set of stimuli along with their metadata for the BrainIO system.

    :param catalog_name: The name of the lookup catalog to add the stimulus set to.
    :param proto_stimulus_set: A StimulusSet containing one row for each stimulus, and the columns {'stimulus_id', ['stimulus_path_within_store' (optional to structure zip directory layout)]} and columns for all stimulus-set-specific metadata but not the column 'filename'.
    :param stimulus_set_identifier: A unique name identifying the stimulus set <lab identifier>.<first author e.g. 'Rajalingham' or 'MajajHong' for shared first-author><YYYY year of publication>.
    :param bucket_name: The name of the bucket to upload to.

package_data_assembly(catalog_identifier, proto_data_assembly, assembly_identifier, stimulus_set_identifier, assembly_class_name="NeuronRecordingAssembly", bucket_name="brainio-contrib", extras=None):
    Package a set of data along with its metadata for the BrainIO system.

    :param catalog_identifier: The name of the lookup catalog to add the data assembly to.
    :param proto_data_assembly: An xarray DataArray containing experimental measurements and all related metadata.

        * The dimensions of the DataArray must be appropriate for the DataAssembly class:

          * NeuroidAssembly and its subclasses:  "presentation", "neuroid"[, "time_bin"]

            * except for SpikeTimesAssembly:  "event"

          * MetaDataAssembly:  "event"
          * BehavioralAssembly:  should have a "presentation" dimension, but can be flexible about its other dimensions.

        * A presentation dimension must have a stimulus_id coordinate and should have coordinates for presentation-level metadata such as repetition.
          The presentation dimension should not have coordinates for stimulus-specific metadata, these will be drawn from the StimulusSet based on stimulus_id.
        * The neuroid dimension must have a neuroid_id coordinate and should have coordinates for as much neural metadata as possible (e.g. region, subregion, animal, row in array, column in array, etc.)
        * The time_bin dimension should have coordinates time_bin_start and time_bin_end.
    :param assembly_identifier: A dot-separated string starting with a lab identifier.

        * For published: <lab identifier>.<first author e.g. 'Rajalingham' or 'MajajHong' for shared first-author><YYYY year of publication>
        * For requests: <lab identifier>.<b for behavioral or n for neuroidal>.<m for monkey or h for human>.<proposer e.g. 'Margalit'>.<pull request number>
    :param stimulus_set_identifier: The unique name of an existing StimulusSet in the BrainIO system.
    :param assembly_class_name: The name of a DataAssembly subclass.
    :param bucket_name: The name of the bucket to upload to.

