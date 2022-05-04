import logging
import os

import pandas as pd

_logger = logging.getLogger(__name__)


class StimulusSet(pd.DataFrame):
    # http://pandas.pydata.org/pandas-docs/stable/development/extending.html#subclassing-pandas-data-structures
    _metadata = pd.DataFrame._metadata + ["identifier", "get_stimulus", "stimulus_paths", "from_files"]

    @property
    def _constructor(self):
        return StimulusSet

    def get_stimulus(self, stimulus_id):
        return self.stimulus_paths[stimulus_id]

    @classmethod
    def from_files(cls, csv_path, dir_path):
        loader = StimulusSetLoader(csv_path=csv_path, stimuli_directory=dir_path, cls=cls)
        return loader.load()


class StimulusSetLoader:
    def __init__(self, csv_path, stimuli_directory, cls):
        self.csv_path = csv_path
        self.stimuli_directory = stimuli_directory
        self.cls = cls

    def load(self):
        stimulus_set = pd.read_csv(self.csv_path)
        stimulus_set = self.cls(stimulus_set)
        stimulus_set.stimulus_paths = {}
        for _, row in stimulus_set.iterrows():
            col_name = 'stimulus_id'
            if 'stimulus_id' not in row:
                col_name = 'image_id' # for legacy packages
            stimulus_set.stimulus_paths[row[col_name]] = os.path.join(self.stimuli_directory, row['filename'])
        assert all(os.path.isfile(stimulus_path) for stimulus_path in stimulus_set.stimulus_paths.values())
        return stimulus_set