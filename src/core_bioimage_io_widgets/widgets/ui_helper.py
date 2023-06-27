from typing import List, Tuple, Dict, Union, Any
from marshmallow import missing
from marshmallow.fields import Field
import markdown

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QComboBox, QLabel, QPlainTextEdit,
    QLayout, QListWidget, QMessageBox, QLineEdit,
    QFileDialog,
)

from core_bioimage_io_widgets.utils import schemas, nodes, flatten


def none_for_empty(text: str):
    """Makes sure the string is not empty otherwise returns None."""
    return None if len(text.strip()) == 0 else text


def to_html(text: str):
    """Converts Markdown text into HTML."""
    return markdown.markdown(text)


def get_tooltip(field: schemas.SharedBioImageIOSchema) -> str:
    """Returns 'bioimageio_description' as an HTML string."""
    return to_html(field.bioimageio_description)


def get_widget_text(widget: QWidget):
    """Returns current text inside the input widget."""
    if isinstance(widget, QComboBox):
        return widget.currentText()
    elif isinstance(widget, QPlainTextEdit):
        return widget.toPlainText()

    return widget.text()


def set_widget_text(widget: QWidget, text: str):
    """Sets the text of the input widget."""
    if isinstance(widget, QLineEdit):
        widget.setText(text)
    elif isinstance(widget, QComboBox):
        index = widget.findText(text)
        if index > -1:
            widget.setCurrentIndex(index)
    elif isinstance(widget, QPlainTextEdit):
        widget.setPlainText(text)


def safe_cast(value, to_type, default=None):
    """Casts value to given type safely."""
    try:
        return to_type(value)
    except (ValueError, TypeError):
        return default


def convert_data(text: str, field_type: str):
    """Converts string data into field type."""
    if field_type.endswith('Float'):
        return safe_cast(text, float, default=text)
    elif field_type.endswith('Integer'):
        return safe_cast(text, int, default=text)
    elif field_type.startswith('Array'):
        return [safe_cast(s.strip(), float, default=text) for s in text.split(',')]

    return text


def enhance_widget(
        input_widget: QWidget, label_text: str,
        field: Union[schemas.SharedBioImageIOSchema, Field] = None
        ):
    """Adds a label, and set some properties on the input widget."""
    label_text = label_text.title()
    label = QLabel(label_text + ":")
    if field is not None:
        input_widget.setProperty("field", field)
        input_widget.setToolTip(to_html(field.bioimageio_description))
        if field.required:
            label.setText(f"{label_text}<sup>*</sup>: ")

    return label, input_widget


def set_ui_data_from_dict(parent: QWidget, data: dict):
    """Fills ui widgets with given data based on widget's field property."""
    if data is None:
        return

    for child in parent.findChildren(QWidget):
        field = child.property("field")
        if field is not None:
            value = data.get(field.name, None)
            if value is None:
                value = ""
            set_widget_text(child, value)


def set_ui_data_from_node(parent: QWidget, data: nodes.RawNode):
    """Fills ui widgets with given data based on widget's field property."""
    if data is None:
        return

    for child in parent.findChildren(QWidget):
        field = child.property("field")
        if field is not None:
            value = getattr(data, field.name)
            if value is missing:
                value = ""
            set_widget_text(child, value)


def get_input_data(parent: QWidget):
    """Gets input data from ui elements that have the field property."""
    entities = {}
    # for i in range(parent.count()):
    for widget in parent.findChildren(QWidget):
        # widget = parent.itemAt(i).widget()
        # if widget:
        field = widget.property("field")
        if field is not None:
            text = get_widget_text(widget)
            text = none_for_empty(text)
            if text or field.required:
                entities[field.name] = convert_data(text, field.type_name)

    return entities


def create_validation_ui(errors: Dict):
    """Creates ui for validation errors."""
    widgets = []
    for field_name, msg_list in errors.items():
        msg_list = flatten(msg_list)
        msg = " | ".join(msg_list)
        label = QLabel(f"{field_name.title()}: {msg}")
        label.setStyleSheet("color: rgb(240, 40, 90)")
        label.setAlignment(Qt.AlignCenter)
        widgets.append(label)

    return widgets


def clear_layout(layout: QLayout) -> None:
    """Removes all widgets from the given layout."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            item.widget().deleteLater()
        else:
            clear_layout(item.layout())


def remove_from_listview(parent: QWidget, list_widget: QListWidget, msg: str = None):
    """Removes the selected item from the given listview widget."""
    curr_row = list_widget.currentRow()
    if curr_row > -1:
        reply = QMessageBox.warning(
            parent, "Bioimage.io",
            msg or "Are you sure you want to remove the selected item from the list?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            list_widget.takeItem(curr_row)

    return reply == QMessageBox.Yes, curr_row


def select_file(filter: str, parent: QWidget = None, output_widget: QWidget = None):
    """Opens a file dialog and set the selected file path into given widget's text."""
    selected_file, _filter = QFileDialog.getOpenFileName(parent, "Browse", ".", filter)
    if output_widget is not None:
        output_widget.setText(selected_file)

    return selected_file
