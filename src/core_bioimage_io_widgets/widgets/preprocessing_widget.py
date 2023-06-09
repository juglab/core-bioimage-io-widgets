from typing import Optional

from marshmallow import missing
from qtpy.QtCore import QRegExp, Qt, Signal
from qtpy.QtGui import QDoubleValidator, QRegExpValidator
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from core_bioimage_io_widgets.utils import PREPROCESSING_TYPES, schemas
from core_bioimage_io_widgets.widgets.ui_helper import (
    clear_layout,
    create_validation_ui,
    enhance_widget,
    get_ui_input_data,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class PreprocessingWidget(QWidget):
    """Input Preprocessing widget."""

    submit = Signal(object, name="submit")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.process_schema: schemas.rdf.SharedBioImageIOSchema = None

        process_label = QLabel("Preprocess:")
        self.process_description_label = QLabel()
        self.process_description_label.setWordWrap(True)
        self.process_combo = QComboBox()
        self.process_combo.addItems(PREPROCESSING_TYPES)
        self.process_combo.currentIndexChanged.connect(self.select_preprocessing)
        #
        self.fields_grid = QGridLayout()
        #
        self.validation_widget = ValidationWidget()
        #
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_process)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())
        form_btn_hbox = QHBoxLayout()
        form_btn_hbox.addWidget(cancel_button)
        form_btn_hbox.addWidget(submit_button)
        #
        grid = QGridLayout()
        grid.addWidget(process_label, 0, 0, alignment=Qt.AlignTop)
        grid.addWidget(self.process_combo, 0, 1, alignment=Qt.AlignTop)
        grid.addWidget(
            self.process_description_label, 1, 1, 1, 2, alignment=Qt.AlignTop
        )
        grid.addLayout(self.fields_grid, 2, 1, alignment=Qt.AlignTop)
        grid.addWidget(self.validation_widget, 3, 0, 1, 3)
        grid.addLayout(form_btn_hbox, 4, 1, 1, 2, alignment=Qt.AlignBottom)
        grid.setRowStretch(4, 1)

        self.setLayout(grid)
        self.setMaximumWidth(470)
        self.setMinimumHeight(360)
        self.setWindowTitle("Preprocessing Parameters")

        self.select_preprocessing()

    def select_preprocessing(self) -> None:
        """Create input fields based on selected preprocessing parameters."""
        class_name = self.process_combo.currentText()
        process_type_class: schemas.rdf.SharedBioImageIOSchema = getattr(
            schemas.model.Preprocessing, class_name, None
        )
        assert process_type_class is not None, "process_type_class is None!"

        # create ui for the selected preprocessing type's parameters:
        clear_layout(self.fields_grid)
        self.validation_widget.clear_content_area()
        self.process_schema = process_type_class()
        self.process_description_label.setText(
            self.process_schema.bioimageio_description
        )
        for i, (_, field) in enumerate(sorted(self.process_schema.fields.items())):
            if isinstance(field, schemas.ProcMode):
                qinput = QComboBox()
                qinput.addItems(field.valid_modes)
            else:
                qinput = QLineEdit()
                # set input validator
                if field.type_name.endswith("Float"):
                    qinput.setValidator(QDoubleValidator())
                    if field.default is not missing:
                        qinput.setText(str(field.default))
                elif field.type_name.startswith("Axes"):
                    regex = QRegExp(
                        r"^(?!.*(.).*\1)[CHARS]*$".replace(
                            "CHARS", field.metadata["valid_axes"]
                        )
                    )
                    qinput.setValidator(QRegExpValidator(regex))
                elif field.type_name.startswith("Array"):
                    qinput.setValidator(QRegExpValidator(QRegExp(r"^[\d\.\,]*$")))
                    qinput.setPlaceholderText("a number or comma separated numbers")

            lbl, _ = enhance_widget(qinput, field.name, field)
            self.fields_grid.addWidget(lbl, i, 0, alignment=Qt.AlignTop)
            self.fields_grid.addWidget(qinput, i, 1, alignment=Qt.AlignTop)
        self.update()

    def submit_process(self) -> None:
        """Validate the process parameters and submit it."""
        process_data = get_ui_input_data(self)
        errors = self.process_schema.validate(process_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
        else:
            # submit preprocess data
            preprocess = {
                "name": self.process_combo.currentText(),
                "kwargs": process_data,
            }
            self.submit.emit(preprocess)
            self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = PreprocessingWidget()
    win.show()
    sys.exit(app.exec_())
