import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QApplication, QCheckBox,
    QComboBox, QCompleter, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QPlainTextEdit,
    QPushButton, QRadioButton, QVBoxLayout,
    QListWidget, QMessageBox
)

import nodes
import schemas
from utils import (
    enhance_widget, set_ui_data, get_input_data,
    create_validation_ui
)
from validation_widget import ValidationWidget
from author_widget import AuthorWidget


class BioImageModelWidget(QWidget):
    """A QT widget for bioimage.io model specs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model: nodes.model.Model = None
        self.model_schema = schemas.model.Model()
        self.authors: List[nodes.rdf.Author] = []

        grid = QGridLayout()
        grid.addWidget(self.create_required_specs_ui(), 0, 0)

        self.setLayout(grid)
        self.setWindowTitle('Bioimage.io Model Specification')

        self.populate_authors_list()

    def save_specs(self):
        """Save the user-entered model specs into a YAML file."""
        pass

    def create_required_specs_ui(self):
        """Create ui for the required specs."""
        version_combo = QComboBox()
        version_label, _ = enhance_widget(
            version_combo, 'Format Version', self.model_schema.fields['format_version']
        )
        version_combo.addItem('0.4.9')
        version_combo.addItem('0.3')
        version_combo.setEnabled(False)
        #
        name_textbox = QLineEdit()
        name_label, _ = enhance_widget(name_textbox, 'Name', self.model_schema.fields['name'])
        #
        description_textbox = QPlainTextEdit()
        description_textbox.setFixedHeight(65)
        description_label, _ = enhance_widget(
            description_textbox, 'Description', self.model_schema.fields['description']
        )
        #
        license_combo = QComboBox()
        license_combo.addItems(self.get_spdx_licenses())
        license_combo.setEditable(True)
        license_combo.setInsertPolicy(QComboBox.NoInsert)
        license_completer = QCompleter(self.get_spdx_licenses())
        license_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        license_completer.setCaseSensitivity(Qt.CaseInsensitive)
        license_combo.setCompleter(license_completer)
        license_label, _ = enhance_widget(license_combo, 'License', self.model_schema.fields['license'])
        #
        doc_textbox = QLineEdit()
        doc_textbox.setPlaceholderText('Select Documentation (*.md) file')
        doc_textbox.setReadOnly(True)
        doc_label, _ = enhance_widget(doc_textbox, 'Documentation', self.model_schema.fields['documentation'])
        doc_button = QPushButton('Browse...')
        doc_button.clicked.connect(lambda: self.select_file('Mark Down files (*.md)', doc_textbox))
        #
        authors_label = QLabel('Authors<sup>*</sup>:')
        authors_label.setStyleSheet('color: rgb(250,200,200)')
        self.authors_listview = QListWidget()
        self.authors_listview.setFixedHeight(100)
        authors_button_add = QPushButton('Add')
        authors_button_add.clicked.connect(lambda: self.show_author_form(edit=False))
        authors_button_edit = QPushButton('Edit')
        authors_button_edit.clicked.connect(lambda: self.show_author_form(edit=True))
        authors_button_del = QPushButton('Remove')
        authors_button_del.clicked.connect(self.del_author)
        authors_btn_vbox = QVBoxLayout()
        authors_btn_vbox.addWidget(authors_button_add)
        authors_btn_vbox.addWidget(authors_button_edit)
        authors_btn_vbox.addWidget(authors_button_del)
        authors_btn_vbox.insertStretch(-1, 1)
        #
        required_layout = QGridLayout()
        required_layout.addWidget(version_label, 0, 0)
        required_layout.addWidget(version_combo, 0, 1)
        required_layout.addWidget(name_label, 1, 0)
        required_layout.addWidget(name_textbox, 1, 1)
        required_layout.addWidget(description_label, 2, 0)
        required_layout.addWidget(description_textbox, 2, 1)
        required_layout.addWidget(license_label, 3, 0)
        required_layout.addWidget(license_combo, 3, 1)
        required_layout.addWidget(doc_label, 4, 0)
        required_layout.addWidget(doc_textbox, 4, 1)
        required_layout.addWidget(doc_button, 4, 2)
        required_layout.addWidget(authors_label, 5, 0, alignment=Qt.AlignTop)
        required_layout.addWidget(self.authors_listview, 5, 1, alignment=Qt.AlignTop)
        required_layout.addLayout(authors_btn_vbox, 5, 2)
        #
        group = QGroupBox('Required Fields')
        group.setLayout(required_layout)

        return group

    def select_file(self, filter: str, output_widget: QWidget=None):
        """Opens a file dialog and set the selected file into given widget's text."""
        selected_file, _filter = QFileDialog.getOpenFileName(self, 'Browse', '.', filter)
        if output_widget is not None:
            output_widget.setText(selected_file)

        return selected_file

    def get_spdx_licenses(self):
        """Read the licenses identifier from the json file aquired from https://github.com/spdx/license-list-data/tree/main/json."""
        root_path = Path(__file__).parent
        with open(root_path.joinpath('./spdx_licenses.json')) as f:
            licenses: List[Dict] = json.load(f).get('licenses', [])
        return [lic['licenseId'] for lic in licenses]

    def show_author_form(self, edit: bool=False):
        """Shows the author form to add a new or modify selected author."""
        author: nodes.rdf.Author = None
        if edit:
            curr_row = self.authors_listview.currentRow()
            if curr_row > -1:
                author = self.authors[curr_row]
        else:
            # new entry: unselect current row
            self.authors_listview.setCurrentRow(-1)
        # show the author's form
        author_win = AuthorWidget(author=author)
        author_win.setWindowModality(Qt.ApplicationModal)
        author_win.submit.connect(self.update_authors)
        author_win.show()

    def populate_authors_list(self):
        """Populates the authors' listview widget with the list of authors."""
        curr_row = self.authors_listview.currentRow()
        self.authors_listview.clear()
        self.authors_listview.addItems(author.name for author in self.authors)
        self.authors_listview.setCurrentRow(curr_row)

    def update_authors(self, author:nodes.rdf.Author):
        """Update the list of authors after a modification."""
        curr_row = self.authors_listview.currentRow()
        if curr_row > -1:
            self.authors[curr_row] = author
        else:
            self.authors.append(author)
        self.populate_authors_list()

    def del_author(self):
        """Delete the selected author."""
        curr_row = self.authors_listview.currentRow()
        if curr_row > -1:
            reply = QMessageBox.question(
                self, 'Bioimage.io', 'Are you sure you want to delete the selected author?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.authors[curr_row]
                self.populate_authors_list()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
