from .io_utils import (
    get_spdx_licenses, get_predefined_tags,
    build_model_zip
)
from.constants import *


def flatten(nested):
    """Flatten a list of lists recursively."""
    if len(nested) == 0:
        return nested
    if isinstance(nested, dict):
        nested = list(nested.values())
    if isinstance(nested[0], list) or isinstance(nested[0], dict):
        return flatten(nested[0]) + flatten(nested[1:])
    return nested[:1] + flatten(nested[1:])


def safe_cast(value: str, to_type, default=None):
    """Casts value to given type safely."""
    try:
        return to_type(value.strip())
    except (ValueError, TypeError):
        return default
