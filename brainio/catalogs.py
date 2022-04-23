from pathlib import Path

import pandas as pd
from pandas import DataFrame


class Catalog(DataFrame):
    # http://pandas.pydata.org/pandas-docs/stable/development/extending.html#subclassing-pandas-data-structures
    _metadata = pd.DataFrame._metadata + ["identifier", "source_path", "url", "from_files"]

    @property
    def _constructor(self):
        return Catalog

    @classmethod
    def from_files(cls, identifier, csv_path, url=None):
        loader = CatalogLoader(identifier, csv_path, cls=cls, url=url)
        return loader.load()


class CatalogLoader:
    def __init__(self, identifier, csv_path, cls=Catalog, url=None):
        self.identifier = identifier
        self.csv_path = Path(csv_path)
        self.cls = cls
        self.url = url

    def load(self):
        catalog = pd.read_csv(self.csv_path)
        catalog = self.cls(catalog)
        catalog.identifier = self.identifier
        catalog.source_path = self.csv_path
        catalog.url = self.url
        return catalog


SOURCE_CATALOG = "source_catalog"