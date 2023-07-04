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
    set_ui_data_from_dict,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class AuthorWidget(QWidget):
    """Author form widget."""

    submit = Signal(object, name="submit")

    def __init__(
        self, author_data: Optional[dict] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self.author_schema = schemas.rdf.Author()

        self.create_ui()
        if author_data is not None:
            set_ui_data_from_dict(self, author_data)

    def create_ui(self) -> None:
        """Creates ui for author's profile."""
        self.name_textbox = QLineEdit()
        name_label, _ = enhance_widget(
            self.name_textbox, "Name", self.author_schema.fields["name"]
        )
        self.email_textbox = QLineEdit()
        email_label, _ = enhance_widget(
            self.email_textbox, "Email", self.author_schema.fields["email"]
        )
        self.affiliation_textbox = QLineEdit()
        affiliation_label, _ = enhance_widget(
            self.affiliation_textbox,
            "Affiliation",
            self.author_schema.fields["affiliation"],
        )
        self.git_textbox = QLineEdit()
        git_label, _ = enhance_widget(
            self.git_textbox,
            "Github User Name",
            self.author_schema.fields["github_user"],
        )
        self.orcid_textbox = QLineEdit()
        orcid_label, _ = enhance_widget(
            self.orcid_textbox, "ORCID", self.author_schema.fields["orcid"]
        )
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_author)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())

        self.validation_widget = ValidationWidget()

        grid = QGridLayout()
        grid.addWidget(name_label, 0, 0)
        grid.addWidget(self.name_textbox, 0, 1)
        grid.addWidget(email_label, 1, 0)
        grid.addWidget(self.email_textbox, 1, 1)
        grid.addWidget(affiliation_label, 2, 0)
        grid.addWidget(self.affiliation_textbox, 2, 1)
        grid.addWidget(git_label, 3, 0)
        grid.addWidget(self.git_textbox, 3, 1)
        grid.addWidget(orcid_label, 4, 0)
        grid.addWidget(self.orcid_textbox, 4, 1)
        grid.addWidget(self.validation_widget, 5, 0, 1, 2)
        hbox = QHBoxLayout()
        hbox.addWidget(cancel_button)
        hbox.addWidget(submit_button)
        grid.addLayout(hbox, 6, 1, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(grid)
        self.setWindowTitle("Author Profile")
        self.setMinimumWidth(340)

    def submit_author(self) -> None:
        """Validate and submit the entered author's profile."""
        author_data = get_ui_input_data(self)
        # validation
        errors = self.author_schema.validate(author_data)
        # NOTE: handling empty string
        if len(self.name_textbox.text().strip()) == 0:
            errors["name"] = ["Author's name is required."]
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        # emit submit signal and send author data
        self.submit.emit(author_data)
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = AuthorWidget()
    win.show()
    sys.exit(app.exec_())
