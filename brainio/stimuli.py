import logging
import os
from pathlib import Path

import pandas as pd

_logger = logging.getLogger(__name__)


class StimulusSet(pd.DataFrame):
    # http://pandas.pydata.org/pandas-docs/stable/development/extending.html#subclassing-pandas-data-structures
    _metadata = pd.DataFrame._metadata + ["identifier", "get_stimulus", 'get_loader_class', "stimulus_paths", "from_files"]

    @property
    def _constructor(self):
        return StimulusSet

    def get_stimulus(self, stimulus_id):
        return self.stimulus_paths[stimulus_id]

    @classmethod
    def get_loader_class(cls):
        return StimulusSetLoader

    @classmethod
    def from_files(cls, csv_path, dir_path, **kwargs):
        loader_class = cls.get_loader_class()
        loader = loader_class(
            cls=cls,
            csv_path=csv_path,
            stimuli_directory=dir_path,
            **kwargs,
        )
        return loader.load()


class StimulusSetLoader:
    """
    Loads a StimulusSet from a CSV file and a directory of stimuli.
    """
    def __init__(self, cls, csv_path, stimuli_directory):
        self.stimulus_set_class = cls
        self.csv_path = csv_path
        self.stimuli_directory = stimuli_directory

    def load(self):
        stimulus_set = pd.read_csv(self.csv_path)
        stimulus_set = self.stimulus_set_class(stimulus_set)
        stimulus_set.stimulus_paths = {}
        for _, row in stimulus_set.iterrows():
            col_name = 'stimulus_id'
            if 'stimulus_id' not in row:
                col_name = 'image_id' # for legacy packages
            stimulus_set.stimulus_paths[row[col_name]] = Path(self.stimuli_directory) / row['filename']
        assert all(stimulus_path.is_file() for stimulus_path in stimulus_set.stimulus_paths.values())
        return stimulus_set

