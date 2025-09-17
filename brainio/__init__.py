# Import functions that depend on external dependencies (boto3) only when available
try:
    from .fetch import get_assembly, get_stimulus_set
except ImportError:
    # External dependencies not available - functions will raise NotImplementedError anyway
    pass

