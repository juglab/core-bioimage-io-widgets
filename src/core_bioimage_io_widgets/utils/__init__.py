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
PROCESSING_MODES = {mode: ProcMode.explanations[mode] for mode in ProcMode.all_modes}
