import logging
from pathlib import Path

import pandas as pd

_logger = logging.getLogger(__name__)

def brainio_test():
    path = Path(__file__).parent / "lookup.csv"
    _logger.debug(f"Loading lookup from {path}")
    print(f"Loading lookup from {path}")  # print because logging usually isn't set up at this point during import
    return pd.read_csv(path)
