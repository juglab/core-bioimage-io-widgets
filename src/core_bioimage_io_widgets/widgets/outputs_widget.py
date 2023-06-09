from typing import List, Optional

import numpy as np
from qtpy.QtCore import QRegExp, Qt, Signal
from qtpy.QtGui import QRegExpValidator
from qtpy.QtWidgets import (
    QApplication,
    # QComboBox,
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

from core_bioimage_io_widgets.utils import (
    AXES_REGEX,
    # OUTPUT_TYPES,
    nodes,
    safe_cast,
    schemas,
)
from core_bioimage_io_widgets.widgets.postprocessing_widget import PostprocessingWidget
from core_bioimage_io_widgets.widgets.ui_helper import (
    create_validation_ui,
    enhance_widget,
    remove_from_listview,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class OutputTensorWidget(QWidget):
    """Model's output form widget."""

    submit = Signal(object, name="submit")

    def __init__(
        self,
        output_names: Optional[list] = None,
        output_data: Optional[dict] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.output_tensor_schema = schemas.model.OutputTensor()
        if output_names is None:
            self.output_names = []
        else:
            self.output_names = output_names
        self.output_shape: List[int] = []
        self.output_type: str = "float32"
        self.postprocessings: List[dict] = []

        self.create_ui()
        # check edit mode
        if output_data is not None:
            self.set_ui_data(output_data)

    def create_ui(self) -> None:
        """Creates ui for model's output tensor."""
        self.test_output_textbox = QLineEdit()
        self.test_output_textbox.setPlaceholderText("select Test Output file (*.npy)")
        self.test_output_textbox.setReadOnly(True)
        test_output_label, _ = enhance_widget(
            self.test_output_textbox, "Test Output<sup>*</sup>"
        )
        test_output_button = QPushButton("Browse...")
        test_output_button.clicked.connect(self.select_test_output)
        test_output_hbox = QHBoxLayout()
        test_output_hbox.addWidget(test_output_label)
        test_output_hbox.addWidget(self.test_output_textbox)
        test_output_hbox.addWidget(test_output_button)
        #
        self.name_textbox = QLineEdit()
        self.name_textbox.setMinimumWidth(180)
        name_label, _ = enhance_widget(
            self.name_textbox, "Name", self.output_tensor_schema.fields["name"]
        )
        #
        self.shape_textbox = QLineEdit()
        self.shape_textbox.setMinimumWidth(180)
        self.shape_textbox.setReadOnly(True)
        shape_label, _ = enhance_widget(
            self.shape_textbox, "Shape", self.output_tensor_schema.fields["shape"]
        )
        #
        self.axes_textbox = QLineEdit()
        self.axes_textbox.setMinimumWidth(180)
        axes_label, _ = enhance_widget(
            self.axes_textbox, "Axes", self.output_tensor_schema.fields["axes"]
        )
        # halo
        self.halo_textbox = QLineEdit()
        self.halo_textbox.setMinimumWidth(180)
        self.halo_textbox.setValidator(QRegExpValidator(QRegExp(r"^[\d\,]*$")))
        self.halo_textbox.setPlaceholderText("Empty or comma separated integers")
        halo_label, _ = enhance_widget(
            self.halo_textbox, "Halo", self.output_tensor_schema.fields["halo"]
        )
        # data type
        # self.data_type_combo = QComboBox()
        # self.data_type_combo.setMinimumWidth(180)
        # self.data_type_combo.addItems(OUTPUT_TYPES)
        # data_type_label, _ = enhance_widget(
        #     self.data_type_combo,
        #     "Data Type",
        #     self.output_tensor_schema.fields["data_type"],
        # )
        #
        postprocessing_label = QLabel("Postprocessing:")
        self.postprocessing_listview = QListWidget()
        self.postprocessing_listview.setMaximumHeight(120)
        postprocessing_button_add = QPushButton("Add")
        postprocessing_button_add.clicked.connect(self.show_postprocessing)
        postprocessing_button_del = QPushButton("Remove")
        postprocessing_button_del.clicked.connect(self.remove_postprocessing)
        postprocessing_btn_vbox = QVBoxLayout()
        postprocessing_btn_vbox.addWidget(postprocessing_button_add)
        postprocessing_btn_vbox.addWidget(postprocessing_button_del)
        postprocessing_btn_vbox.insertStretch(-1, 1)
        #
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_output_tensor)
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
        grid.addWidget(halo_label, 3, 0)
        grid.addWidget(self.halo_textbox, 3, 1, alignment=Qt.AlignLeft)
        # grid.addWidget(data_type_label, 4, 0)
        # grid.addWidget(self.data_type_combo, 4, 1, alignment=Qt.AlignLeft)
        grid.addWidget(postprocessing_label, 5, 0, alignment=Qt.AlignTop)
        grid.addWidget(self.postprocessing_listview, 5, 1, alignment=Qt.AlignTop)
        grid.addLayout(postprocessing_btn_vbox, 5, 2)
        grid.addWidget(self.validation_widget, 6, 0, 1, 3)
        grid.addLayout(form_btn_hbox, 7, 1, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 6)

        vbox = QVBoxLayout()
        vbox.addLayout(test_output_hbox)
        #
        self.output_groupbox = QGroupBox("Output Specifications")
        self.output_groupbox.setLayout(grid)
        self.output_groupbox.setEnabled(False)
        vbox.addWidget(self.output_groupbox)
        #
        self.setLayout(vbox)
        self.setMinimumWidth(400)
        self.setMaximumWidth(700)
        self.setWindowTitle("Output Tensor")

    def set_ui_data(self, output_data: dict) -> None:
        """Fill ui fields with given data."""
        self.test_output_selected(output_data["test_output"])
        output_tensor_data: dict = output_data["output_tensor"]
        self.name_textbox.setText(output_tensor_data["name"])
        self.axes_textbox.setText(output_tensor_data["axes"])
        self.halo_textbox.setText(
            ",".join(str(h) for h in output_tensor_data.get("halo", []))
        )
        # index = self.data_type_combo.findText(
        #     output_tensor_data.get("data_type", "float32")
        # )
        # if index > -1:
        #     self.data_type_combo.setCurrentIndex(index)
        for process in output_tensor_data.get("postprocessing", []):
            self.add_postprocessing(process)

    def submit_output_tensor(self) -> None:
        """Validate and submit the output tensor."""
        output_data = {
            "name": self.name_textbox.text(),
            "data_type": self.output_type,
            "shape": self.output_shape,
            "axes": self.axes_textbox.text(),
        }
        if len(self.halo_textbox.text()) > 0:
            output_data["halo"] = [
                safe_cast(s, int) for s in self.halo_textbox.text().split(",")
            ]
        # output_data["data_type"] = self.data_type_combo.currentText()
        if len(self.postprocessings) > 0:
            output_data["postprocessing"] = self.postprocessings
        # validation
        errors = self.output_tensor_schema.validate(output_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return
        # check output name is unique
        if self.name_textbox.text() in self.output_names:
            errors = {"name": ["Output name must be unique."]}
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        # emit submit signal and send output data
        self.submit.emit(
            {
                "test_output": self.test_output_textbox.text(),
                "output_tensor": output_data,
            }
        )
        self.close()

    def select_test_output(self) -> None:
        """Show a file dialog to select a npy file for test output.

        Then reads the output shape.
        """
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Browse", ".", "Numpy file (*.npy)"
        )
        if selected_file is not None:
            self.test_output_selected(selected_file)

    def test_output_selected(self, selected_file: str) -> None:
        """Read selected numpy file and update corresponding ui."""
        self.test_output_textbox.setText(selected_file)
        self.output_groupbox.setEnabled(True)
        self.test_output = selected_file
        # read numpy file
        with open(selected_file, mode="rb") as f:
            arr = np.load(f)
        _max_len = len(arr.shape)
        # output shape
        self.output_shape = arr.shape
        self.output_type = str(arr.dtype)
        self.shape_textbox.setText(" x ".join(str(d) for d in arr.shape))
        # set axes textbox validator based on the test output array shape:
        self.axes_textbox.setMaxLength(_max_len)
        validator = QRegExpValidator(QRegExp(AXES_REGEX.replace("LEN", str(_max_len))))
        self.axes_textbox.setValidator(validator)
        # set output name
        self.name_textbox.setText(self.get_output_name())

    def show_postprocessing(self) -> None:
        """Show postprocessing form."""
        preprocess_form = PostprocessingWidget()
        preprocess_form.setWindowModality(Qt.ApplicationModal)
        preprocess_form.submit.connect(self.add_postprocessing)
        preprocess_form.show()

    def add_postprocessing(self, postprocess: nodes.model.Postprocessing) -> None:
        """Add created postprocessing to the listview."""
        self.postprocessings.append(
            {"name": postprocess["name"], "kwargs": postprocess["kwargs"]}
        )
        text = f"{postprocess['name']} {postprocess['kwargs']}"
        self.postprocessing_listview.addItem(text)

    def remove_postprocessing(self) -> None:
        """Remove selected postprocessing."""
        reply, del_row = remove_from_listview(
            self,
            self.postprocessing_listview,
            "Are you sure you want to remove the selected postprocessing?",
        )
        if reply:
            del self.postprocessings[del_row]

    def get_output_name(self) -> str:
        """Returns a unique name for the output."""
        num = len(self.output_names) + 1
        name = f"output_{num}"
        while name in self.output_names:
            num += 1
            name = f"output_{num}"

        return name


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = OutputTensorWidget()
    win.show()
    sys.exit(app.exec_())
