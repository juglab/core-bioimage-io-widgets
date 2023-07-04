from typing import Optional

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from core_bioimage_io_widgets.utils import schemas
from core_bioimage_io_widgets.widgets.ui_helper import (
    create_validation_ui,
    enhance_widget,
    get_ui_input_data,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class CiteWidget(QWidget):
    """Citation widget form."""

    submit = Signal(object, name="submit")

    def __init__(
        self, cite_data: Optional[dict] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self.cite_schema = schemas.rdf.CiteEntry()

        self.create_ui()
        # check edit mode
        if cite_data is not None:
            self.set_ui_data(cite_data)

    def create_ui(self) -> None:
        """Create ui for the citation entry."""
        self.cite_textbox = QLineEdit()
        cite_label, _ = enhance_widget(
            self.cite_textbox, "Cite Text", self.cite_schema.fields["text"]
        )
        self.doi_textbox = QLineEdit()
        doi_label, _ = enhance_widget(
            self.doi_textbox, "DOI", self.cite_schema.fields["doi"]
        )
        self.url_textbox = QLineEdit()
        url_label, _ = enhance_widget(
            self.url_textbox, "URL", self.cite_schema.fields["url"]
        )
        #
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_cite)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())
        form_btn_hbox = QHBoxLayout()
        form_btn_hbox.addWidget(cancel_button)
        form_btn_hbox.addWidget(submit_button)
        #
        self.validation_widget = ValidationWidget()
        #
        grid = QGridLayout()
        grid.addWidget(cite_label, 0, 0)
        grid.addWidget(self.cite_textbox, 0, 1)
        grid.addWidget(doi_label, 1, 0)
        grid.addWidget(self.doi_textbox, 1, 1)
        grid.addWidget(url_label, 2, 0)
        grid.addWidget(self.url_textbox, 2, 1)
        grid.addWidget(self.validation_widget, 3, 0, 1, 2)
        grid.addLayout(form_btn_hbox, 4, 1, alignment=Qt.AlignRight)
        #
        self.setLayout(grid)
        self.setMinimumWidth(450)
        self.setWindowTitle("Cite")

    def set_ui_data(self, cite_data: dict) -> None:
        """Fill ui fields with given data."""
        self.cite_textbox.setText(cite_data["text"])
        self.doi_textbox.setText(cite_data.get("doi"))
        self.url_textbox.setText(cite_data.get("url"))

    def submit_cite(self) -> None:
        """Validate and submit the citation."""
        cite_data = get_ui_input_data(self)
        errors = self.cite_schema.validate(cite_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        self.submit.emit(cite_data)
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = CiteWidget()
    win.show()
    sys.exit(app.exec_())
