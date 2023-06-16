from typing import Dict, List, Tuple

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QWidget, QApplication, QGridLayout,
    QLineEdit, QPushButton,
)

from core_bioimage_io_widgets.utils import nodes, schemas
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget
from core_bioimage_io_widgets.widgets.ui_helper import (
    enhance_widget, set_ui_data, get_input_data,
    create_validation_ui
)


class InputTensorWidget(QWidget):
    """Inputs form widget."""

    submit = Signal(object, name="submit")

    def __init__(self, input_tensor: nodes.model.InputTensor = None, parent=None):
        super().__init__(parent)

        self.input_tensor = input_tensor
        self.input_tensor_schema = schemas.model.InputTensor()

        self.create_ui()
        if self.input_tensor is not None:
            set_ui_data(self, self.input_tensor)

    def create_ui(self):
        """Creates ui for author's profile."""
        self.name_textbox = QLineEdit()
        name_label, _ = enhance_widget(
            self.name_textbox, "Name", self.input_tensor_schema.fields["name"]
        )
        
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_author)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())

        self.validation_widget = ValidationWidget()

        grid = QGridLayout()
        grid.addWidget(name_label, 0, 0)
        grid.addWidget(self.name_textbox, 0, 1)

        grid.addWidget(cancel_button, 6, 0, Qt.AlignBottom)
        grid.addWidget(submit_button, 6, 1, Qt.AlignBottom)

        self.setLayout(grid)
        self.setWindowTitle("Input Tensor")

    def submit_author(self):
        """Validate and submit the input tensor."""
        input_data = get_input_data(self)
        # validation
        errors = self.input_tensor_schema.validate(input_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        # emit submit signal and send author data
        input_tensor = self.input_tensor_schema.load(input_data)
        self.submit.emit(input_tensor)
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = InputTensorWidget()
    win.show()
    sys.exit(app.exec_())
