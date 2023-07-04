"""UI Widgets for this project."""

from .author_widget import AuthorWidget
from .cite_widget import CiteWidget
from .inputs_widget import InputTensorWidget
from .main_widget import BioImageModelWidget
from .outputs_widget import OutputTensorWidget
from .postprocessing_widget import PostprocessingWidget
from .preprocessing_widget import PreprocessingWidget
from .single_input_widget import SingleInputWidget
from .tags_input_widget import TagsInputWidget
from .validation_widget import ValidationWidget

__all__ = [
    "AuthorWidget",
    "CiteWidget",
    "InputTensorWidget",
    "OutputTensorWidget",
    "PostprocessingWidget",
    "PreprocessingWidget",
    "SingleInputWidget",
    "TagsInputWidget",
    "ValidationWidget",
    "BioImageModelWidget",
]
