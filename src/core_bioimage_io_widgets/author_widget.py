from typing import Dict, List, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QApplication, QCheckBox,
    QComboBox, QCompleter, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QPlainTextEdit,
    QPushButton, QRadioButton, QVBoxLayout,
    QSizePolicy,
)

import nodes
import schemas
from validation_widget import ValidationWidget
from utils import (
    enhance_widget, set_ui_data, get_input_data,
    create_validation_ui
)


class AuthorWidget(QWidget):
    """Author form widget."""

    submit = pyqtSignal(object, name='submit')

    def __init__(self, author: nodes.rdf.Author = None, parent=None):
        super().__init__(parent)

        self.author = author
        self.author_schema = schemas.rdf.Author()

        self.create_ui()
        if self.author is not None:
            set_ui_data(self, self.author)

    def create_ui(self):
        """Creates ui for author's profile."""
        self.name_textbox = QLineEdit()
        name_label, _ = enhance_widget(
            self.name_textbox, 'Name', self.author_schema.fields['name']
        )
        self.email_textbox = QLineEdit()
        email_label, _ = enhance_widget(
            self.email_textbox, 'Email', self.author_schema.fields['email']
        )
        self.affiliation_textbox = QLineEdit()
        affiliation_label, _ = enhance_widget(
            self.affiliation_textbox, 'Affiliation', self.author_schema.fields['affiliation']
        )
        self.git_textbox = QLineEdit()
        git_label, _ = enhance_widget(
            self.git_textbox, 'Github User Name', self.author_schema.fields['github_user']
        )
        self.orcid_textbox = QLineEdit()
        orcid_label, _ = enhance_widget(
            self.orcid_textbox, 'ORCID', self.author_schema.fields['orcid']
        )
        submit_button = QPushButton('&Submit')
        submit_button.clicked.connect(self.submit_author)
        cancel_button = QPushButton('&Cancel')
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
        grid.addWidget(cancel_button, 6, 0, Qt.AlignBottom)
        grid.addWidget(submit_button, 6, 1, Qt.AlignBottom)

        self.setLayout(grid)
        self.setWindowTitle('Author Profile')

    def submit_author(self):
        """Validate and submit the entered author's profile."""
        author_data = get_input_data(self)
        # validation
        errors = self.author_schema.validate(author_data)
        if errors:
            self.validation_widget.update_content(create_validation_ui(errors))
            return

        # emit submit signal and send author data
        author = self.author_schema.load(author_data)
        self.submit.emit(author)
        self.close()




if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    win = AuthorWidget()
    win.show()
    sys.exit(app.exec_())
