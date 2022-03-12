import logging
from pathlib import Path

import pandas as pd

from brainio.catalogs import CATALOG_PATH_KEY, Catalog

_logger = logging.getLogger(__name__)

def brainio_test():
    path = Path(__file__).parent / "lookup.csv"
    _logger.debug(f"Loading catalog from {path}")
    print(f"Loading catalog from {path}")  # print because logging usually isn't set up at this point during import
    catalog = Catalog.from_file("brainio_test", path)
    catalog.attrs[CATALOG_PATH_KEY] = str(path)
    return catalog


def brainio_test2():
    path = Path(__file__).parent / "lookup2.csv"
    _logger.debug(f"Loading catalog from {path}")
    print(f"Loading catalog from {path}")  # print because logging usually isn't set up at this point during import
    catalog = Catalog.from_file("brainio_test2", path)
    catalog.attrs[CATALOG_PATH_KEY] = str(path)
    return catalog

