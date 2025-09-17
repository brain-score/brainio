import hashlib
import logging

_logger = logging.getLogger(__name__)


def sha1_hash(path, buffer_size=64 * 2 ** 10):
    """Calculate SHA1 hash of a file."""
    _logger.debug(f'BEGIN sha1_hash on {path}')
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    _logger.debug(f'END   sha1_hash on {path}')
    return sha1.hexdigest()