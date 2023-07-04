from typing import get_args

from .nodes import model
from .schemas import ProcMode

FORMAT_VERSION = "0.4.9"
AXES = ["b", "i", "t", "c", "z", "y", "x"]
AXES_REGEX = r"^(?!.*(.).*\1)[bitczyx]{LEN}$"
PREPROCESSING_TYPES = get_args(model.PreprocessingName)
POSTPROCESSING_TYPES = get_args(model.PostprocessingName)
PROCESSING_MODES = {mode: ProcMode.explanations[mode] for mode in ProcMode.all_modes}
WEIGHT_FORMATS = get_args(model.WeightsFormat)
PYTORCH_STATE_DICT = "pytorch_state_dict"
OUTPUT_TYPES = (
    "float32",
    "float64",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
)
