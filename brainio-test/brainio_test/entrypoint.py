import logging
from pathlib import Path

from brainio.catalogs import Catalog

_logger = logging.getLogger(__name__)

# Note that setup.py is where the entrypoint's published name is set

def brainio_test():
    path = Path(__file__).parent / "lookup.csv"
    _logger.debug(f"Loading catalog from {path}")
    print(f"Loading catalog from {path}")  # print because logging usually isn't set up at this point during import
    catalog = Catalog.from_files("brainio_test", path)  # setup.py is where the entrypoint's published name is set
    return catalog


def brainio_test2():
    path = Path(__file__).parent / "lookup2.csv"
    _logger.debug(f"Loading catalog from {path}")
    print(f"Loading catalog from {path}")  # print because logging usually isn't set up at this point during import
    catalog = Catalog.from_files("brainio_test2", path)  # setup.py is where the entrypoint's published name is set
    return catalog

