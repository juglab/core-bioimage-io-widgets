from typing import get_args

from .io_utils import (
    get_spdx_licenses, get_predefined_tags
)
from .nodes import model
from .schemas import ProcMode


FORMAT_VERSION = '0.4.9'
AXES = ["b", "i", "t", "c", "z", "y", "x"]
AXES_REGEX = r"^(?!.*(.).*\1)[bitczyx]{LEN}$"
PREPROCESSING_TYPES = get_args(model.PreprocessingName)
POSTPROCESSING_TYPES = get_args(model.PostprocessingName)
PROCESSING_MODES = {mode: ProcMode.explanations[mode] for mode in ProcMode.all_modes}
WEIGHT_FORMATS = get_args(model.WeightsFormat)


def flatten(nested):
    """Flatten a list of lists recursively."""
    if len(nested) == 0:
        return nested
    if isinstance(nested, dict):
        nested = list(nested.values())
    if isinstance(nested[0], list):
        return flatten(nested[0]) + flatten(nested[1:])
    return nested[:1] + flatten(nested[1:])


def safe_cast(value: str, to_type, default=None):
    """Casts value to given type safely."""
    try:
        return to_type(value.strip())
    except (ValueError, TypeError):
        return default
