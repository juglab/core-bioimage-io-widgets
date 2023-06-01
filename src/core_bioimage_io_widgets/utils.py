from typing import List, Tuple, Dict, Union, Any
from marshmallow import missing
from marshmallow.fields import Field
import markdown

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QApplication, QCheckBox,
    QComboBox, QCompleter, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QPlainTextEdit,
    QPushButton, QRadioButton, QVBoxLayout,
)

# from bioimageio.spec.shared.fields import DocumentedField
from bioimageio.spec.shared.schema import SharedBioImageIOSchema


def none_for_empty(text: str):
    """Makes sure the string is not empty otherwise returns None."""
    return None if len(text) == 0 else text


def to_html(text: str):
    """Converts Markdown text into HTML."""
    return markdown.markdown(text)


def get_tooltip(field: SharedBioImageIOSchema) -> str:
    """Returns 'bioimageio_description' as an HTML string."""
    return to_html(field.bioimageio_description)

def get_widget_text(widget: QWidget):
    """Returns current text inside the input widget."""
    # if isinstance(widget, QLineEdit):
        # return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()

    return widget.text()


def enhance_widget(
        input_widget: QWidget, label_text: str,
        field: Union[SharedBioImageIOSchema, Field] = None
        ):
    """Add a label, and set some properties on the input widget."""
    label_text = label_text.title()
    label = QLabel(label_text)
    if field is not None:
        input_widget.setProperty('field', field)
        input_widget.setToolTip(to_html(field.bioimageio_description))
        if field.required:
            label.setText(f'{label_text}<sup>*</sup>: ')
            label.setStyleSheet('color: rgb(250,200,200)')

    return label, input_widget


def set_ui_data(parent: QWidget, data: Any):
    """Fill ui widgets with given data based on field(schema) property."""
    if data is None:
        return

    for child in parent.findChildren(QWidget):
        field = child.property('field')
        if field is not None:
            value = getattr(data, field.name)
            if value is missing:
                value = ''
            child.setText(value)


def get_input_data(parent: QWidget):
    """Get input data from ui elements that have the field property."""
    entity = {}
    for child in parent.findChildren(QWidget):
        field = child.property('field')
        if field is not None:
            text = get_widget_text(child)
            if field.required or len(text) > 0:
                entity[field.name] = none_for_empty(text)

    return entity


def create_validation_ui(errors: Dict):
    """Create ui for validation errors."""
    widgets = []
    for field_name, msg_list in errors.items():
        msg = ' | '.join(m for m in msg_list)
        label = QLabel(f'{field_name.title()}: {msg}')
        label.setStyleSheet('color: rgb(240, 40, 90)')
        label.setAlignment(Qt.AlignCenter)
        widgets.append(label)

    return widgets
