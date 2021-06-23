import pandas as pd


class StimulusSet(pd.DataFrame):
    # http://pandas.pydata.org/pandas-docs/stable/development/extending.html#subclassing-pandas-data-structures
    _metadata = pd.DataFrame._metadata + ["identifier", "get_image", "image_paths"]

    @property
    def _constructor(self):
        return StimulusSet

    def get_image(self, image_id):
        return self.image_paths[image_id]
