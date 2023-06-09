from typing import List, Optional

import numpy as np
from qtpy.QtCore import QRegExp, Qt, Signal
from qtpy.QtGui import QRegExpValidator
from qtpy.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core_bioimage_io_widgets.utils import AXES_REGEX, schemas
from core_bioimage_io_widgets.widgets.preprocessing_widget import PreprocessingWidget
from core_bioimage_io_widgets.widgets.ui_helper import (
    create_validation_ui,
    enhance_widget,
    remove_from_listview,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class InputTensorWidget(QWidget):
    """Model's Input widget form."""

    submit = Signal(object, name="submit")

    def __init__(
        self,
        input_names: Optional[list] = None,
        input_data: Optional[dict] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.input_tensor_schema = schemas.model.InputTensor()
        if input_names is None:
            self.input_names = []
        else:
            self.input_names = input_names
        self.input_shape: List[int] = []
        self.preprocessings: List[dict] = []

        self.create_ui()
        # check edit mode
        if input_data is not None:
            self.set_ui_data(input_data)

    def create_ui(self) -> None:
        """Creates ui for model's input tensor."""
        self.test_input_textbox = QLineEdit()
        self.test_input_textbox.setPlaceholderText("select Test Input file (*.npy)")
        self.test_input_textbox.setReadOnly(True)
        test_input_label, _ = enhance_widget(
            self.test_input_textbox, "Test Input<sup>*</sup>"
        )
        test_input_button = QPushButton("Browse...")
        test_input_button.clicked.connect(self.select_test_input)
        test_input_hbox = QHBoxLayout()
        test_input_hbox.addWidget(test_input_label)
        test_input_hbox.addWidget(self.test_input_textbox)
        test_input_hbox.addWidget(test_input_button)
        #
        self.name_textbox = QLineEdit()
        name_label, _ = enhance_widget(
            self.name_textbox, "Name", self.input_tensor_schema.fields["name"]
        )
        #
        self.shape_textbox = QLineEdit()
        self.shape_textbox.setReadOnly(True)
        shape_label, _ = enhance_widget(
            self.shape_textbox, "Shape", self.input_tensor_schema.fields["shape"]
        )
        #
        self.axes_textbox = QLineEdit()
        axes_label, _ = enhance_widget(
            self.axes_textbox, "Axes", self.input_tensor_schema.fields["axes"]
        )
        #
        preprocessing_label = QLabel("Preprocessing:")
        self.preprocessing_listview = QListWidget()
        self.preprocessing_listview.setMaximumHeight(120)
        preprocessing_button_add = QPushButton("Add")
        preprocessing_button_add.clicked.connect(self.show_preprocessing_form)
        preprocessing_button_del = QPushButton("Remove")
        preprocessing_button_del.clicked.connect(self.remove_preprocessing)
        preprocessing_btn_vbox = QVBoxLayout()
        preprocessing_btn_vbox.addWidget(preprocessing_button_add)
        preprocessing_btn_vbox.addWidget(preprocessing_button_del)
        preprocessing_btn_vbox.insertStretch(-1, 1)
        #
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_input_tensor)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())
        form_btn_hbox = QHBoxLayout()
        form_btn_hbox.addWidget(cancel_button)
        form_btn_hbox.addWidget(submit_button)
        #
        self.validation_widget = ValidationWidget()
        #
        grid = QGridLayout()
        grid.addWidget(name_label, 0, 0)
        grid.addWidget(self.name_textbox, 0, 1, alignment=Qt.AlignLeft)
        grid.addWidget(shape_label, 1, 0)
        grid.addWidget(self.shape_textbox, 1, 1, alignment=Qt.AlignLeft)
        grid.addWidget(axes_label, 2, 0)
        grid.addWidget(self.axes_textbox, 2, 1, alignment=Qt.AlignLeft)
        grid.addWidget(preprocessing_label, 3, 0, alignment=Qt.AlignTop)
        grid.addWidget(self.preprocessing_listview, 3, 1, alignment=Qt.AlignTop)
        grid.addLayout(preprocessing_btn_vbox, 3, 2)
        grid.addWidget(self.validation_widget, 4, 0, 1, 3)
        grid.addLayout(form_btn_hbox, 5, 1, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 5)

        vbox = QVBoxLayout()
        vbox.addLayout(test_input_hbox)
        #
        self.input_groupbox = QGroupBox("Input Specifications")
        self.input_groupbox.setLayout(grid)
        self.input_groupbox.setEnabled(False)
        vbox.addWidget(self.input_groupbox)
        #
        self.setLayout(vbox)
        self.setMinimumWidth(400)
        self.setMaximumWidth(700)
        self.setWindowTitle("Input Tensor")

    def set_ui_data(self, input_data: dict) -> None:
        """Fill ui fields with given data."""
        self.test_input_selected(input_data["test_input"])
        input_tensor_data: dict = input_data["input_tensor"]
        self.name_textbox.setText(input_tensor_data["name"])
        self.axes_textbox.setText(input_tensor_data["axes"])
        for process in input_tensor_data["preprocessing"]:
            self.add_preprocessing(process)

    def submit_input_tensor(self) -> None:
        """Validate and submit the input tensor."""
        input_data = {
            "name": self.name_textbox.text(),
            "data_type": "float32",
            "shape": self.input_shape,
            "axes": self.axes_textbox.text(),
        }
        if len(self.preprocessings) > 0:
            input_data["preprocessing"] = self.preprocessings
        # validation
        errors = self.input_tensor_schema.validate(input_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return
        # check input name is unique
        if self.name_textbox.text() in self.input_names:
            errors = {"name": ["Input name must be unique."]}
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        # emit submit signal and send input data
        self.submit.emit(
            {"test_input": self.test_input_textbox.text(), "input_tensor": input_data}
        )
        self.close()

    def select_test_input(self) -> None:
        """Show a file dialog to select a npy file as test input.

        Then read the input shape.
        """
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Browse", ".", "Numpy file (*.npy)"
        )
        if selected_file:
            self.test_input_selected(selected_file)

    def test_input_selected(self, selected_file: str) -> None:
        """Read selected numpy file and update corresponding ui."""
        self.test_input_textbox.setText(selected_file)
        self.input_groupbox.setEnabled(True)
        self.test_input = selected_file
        # read numpy file
        with open(selected_file, mode="rb") as f:
            arr = np.load(f)
        _max_len = len(arr.shape)
        # input shape
        self.input_shape = arr.shape
        self.shape_textbox.setText(" x ".join(str(d) for d in arr.shape))
        # set axes textbox validator based on the test input array shape:
        self.axes_textbox.setMaxLength(_max_len)
        validator = QRegExpValidator(QRegExp(AXES_REGEX.replace("LEN", str(_max_len))))
        self.axes_textbox.setValidator(validator)
        # set input name
        self.name_textbox.setText(self.get_input_name())

    def show_preprocessing_form(self) -> None:
        """Show Preprocessing form."""
        preprocess_form = PreprocessingWidget()
        preprocess_form.setWindowModality(Qt.ApplicationModal)
        preprocess_form.submit.connect(self.add_preprocessing)
        preprocess_form.show()

    def add_preprocessing(self, preprocess: dict) -> None:
        """Add created preprocessing to the listview."""
        self.preprocessings.append(
            {"name": preprocess["name"], "kwargs": preprocess["kwargs"]}
        )
        text = f"{preprocess['name']} {preprocess['kwargs']}"
        self.preprocessing_listview.addItem(text)

    def remove_preprocessing(self) -> None:
        """Remove selected preprocessing."""
        reply, del_row = remove_from_listview(
            self,
            self.preprocessing_listview,
            "Are you sure you want to remove the selected preprocessing?",
        )
        if reply:
            del self.preprocessings[del_row]

    def get_input_name(self) -> str:
        """Returns a unique name for the input."""
        num = len(self.input_names) + 1
        name = f"input_{num}"
        while name in self.input_names:
            num += 1
            name = f"input_{num}"

        return name


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = InputTensorWidget()
    win.show()
    sys.exit(app.exec_())
