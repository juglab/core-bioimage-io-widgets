"""Utility function."""

from typing import Any

from .constants import (
    AXES,
    AXES_REGEX,
    FORMAT_VERSION,
    OUTPUT_TYPES,
    POSTPROCESSING_TYPES,
    PREPROCESSING_TYPES,
    PROCESSING_MODES,
    PYTORCH_STATE_DICT,
    WEIGHT_FORMATS,
)
from .io_utils import build_model_zip, get_predefined_tags, get_spdx_licenses


def safe_cast(value: str, to_type: Any, default: Any = None) -> Any:
    """Casts value to given type safely."""
    try:
        return to_type(value.strip())
    except (ValueError, TypeError):
        return default


__all__ = [
    "FORMAT_VERSION",
    "AXES",
    "AXES_REGEX",
    "PREPROCESSING_TYPES",
    "POSTPROCESSING_TYPES",
    "PROCESSING_MODES",
    "WEIGHT_FORMATS",
    "PYTORCH_STATE_DICT",
    "OUTPUT_TYPES",
    "build_model_zip",
    "get_predefined_tags",
    "get_spdx_licenses",
    "nodes",
    "schemas",
]
