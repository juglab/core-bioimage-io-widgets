import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QApplication,
    QComboBox, QCompleter, QFileDialog,
    QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout, QFrame,
    QListWidget, QMessageBox, QTabWidget
)

from core_bioimage_io_widgets.utils import nodes, schemas
from core_bioimage_io_widgets.resources import SPDX_LICENSES
from core_bioimage_io_widgets.widgets.ui_helper import (
    enhance_widget,
    TAGS
)
from core_bioimage_io_widgets.widgets.author import AuthorWidget
from core_bioimage_io_widgets.widgets.single_input import SingleInputWidget
from core_bioimage_io_widgets.widgets.tags_input import TagsInputWidget


class BioImageModelWidget(QWidget):
    """A QT widget for bioimage.io model specs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model: nodes.model.Model = None
        self.model_schema = schemas.model.Model()
        self.authors: List[nodes.rdf.Author] = []

        tabs = QTabWidget()
        tabs.addTab(self.create_required_specs_ui(), "Required Fields")
        tabs.addTab(self.create_other_spec_ui(), "Optional Fields")

        grid = QGridLayout()
        grid.addWidget(tabs, 0, 0)
        # grid.addWidget(self.create_required_specs_ui(), 0, 0)
        # grid.addWidget(self.create_other_spec_ui(), 1, 0)

        self.setLayout(grid)
        self.setWindowTitle("Bioimage.io Model Specification")

        self.populate_authors_list()

    def save_specs(self):
        """Save the user-entered model specs into a YAML file."""
        pass

    def create_required_specs_ui(self):
        """Create ui for the required specs."""
        version_combo = QComboBox()
        version_label, _ = enhance_widget(
            version_combo, "Format Version", self.model_schema.fields["format_version"]
        )
        version_combo.addItem("0.4.9")
        version_combo.addItem("0.3")
        version_combo.setEnabled(False)
        #
        name_textbox = QLineEdit()
        name_label, _ = enhance_widget(name_textbox, "Name", self.model_schema.fields["name"])
        #
        description_textbox = QPlainTextEdit()
        description_textbox.setFixedHeight(65)
        description_label, _ = enhance_widget(
            description_textbox, "Description", self.model_schema.fields["description"]
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
        license_label, _ = enhance_widget(license_combo, "License", self.model_schema.fields["license"])
        #
        doc_textbox = QLineEdit()
        doc_textbox.setPlaceholderText("Select Documentation (*.md) file")
        doc_textbox.setReadOnly(True)
        doc_label, _ = enhance_widget(doc_textbox, "Documentation", self.model_schema.fields["documentation"])
        doc_button = QPushButton("Browse...")
        doc_button.clicked.connect(lambda: self.select_file("Mark Down files (*.md)", doc_textbox))
        #
        authors_label = QLabel("Authors<sup>*</sup>:")
        self.authors_listview = QListWidget()
        self.authors_listview.setFixedHeight(70)
        authors_button_add = QPushButton("Add")
        authors_button_add.clicked.connect(lambda: self.show_author_form(edit=False))
        authors_button_edit = QPushButton("Edit")
        authors_button_edit.clicked.connect(lambda: self.show_author_form(edit=True))
        authors_button_del = QPushButton("Remove")
        authors_button_del.clicked.connect(self.del_author)
        authors_btn_vbox = QVBoxLayout()
        authors_btn_vbox.addWidget(authors_button_add)
        authors_btn_vbox.addWidget(authors_button_edit)
        authors_btn_vbox.addWidget(authors_button_del)
        #
        self.test_inputs_listview = QListWidget()
        self.test_inputs_listview.setFixedHeight(70)
        test_inputs_label, _ = enhance_widget(
            self.test_inputs_listview, "Test Inputs", self.model_schema.fields["test_inputs"]
        )
        test_inputs_button_add = QPushButton("Add")
        test_inputs_button_add.clicked.connect(lambda: self.select_npy_file(self.test_inputs_listview))
        test_inputs_button_del = QPushButton("Remove")
        test_inputs_button_del.clicked.connect(lambda: self.del_test_io(self.test_inputs_listview))
        test_inputs_vbox = QVBoxLayout()
        test_inputs_vbox.addWidget(test_inputs_button_add)
        test_inputs_vbox.addWidget(test_inputs_button_del)
        #
        self.test_outputs_listview = QListWidget()
        self.test_outputs_listview.setFixedHeight(70)
        test_outputs_label, _ = enhance_widget(
            self.test_outputs_listview, "Test Outputs", self.model_schema.fields["test_outputs"]
        )
        test_outputs_button_add = QPushButton("Add")
        test_outputs_button_add.clicked.connect(lambda: self.select_npy_file(self.test_outputs_listview))
        test_outputs_button_del = QPushButton("Remove")
        test_outputs_button_del.clicked.connect(lambda: self.del_test_io(self.test_outputs_listview))
        test_outputs_vbox = QVBoxLayout()
        test_outputs_vbox.addWidget(test_outputs_button_add)
        test_outputs_vbox.addWidget(test_outputs_button_del)
        #
        required_layout = QGridLayout()
        # required_layout.addWidget(version_label, 0, 0)
        # required_layout.addWidget(version_combo, 0, 1)
        required_layout.addWidget(name_label, 0, 0)
        required_layout.addWidget(name_textbox, 0, 1)
        required_layout.addWidget(description_label, 1, 0)
        required_layout.addWidget(description_textbox, 1, 1)
        required_layout.addWidget(license_label, 2, 0)
        required_layout.addWidget(license_combo, 2, 1)
        required_layout.addWidget(doc_label, 3, 0)
        required_layout.addWidget(doc_textbox, 3, 1)
        required_layout.addWidget(doc_button, 3, 2)
        required_layout.addWidget(authors_label, 4, 0)
        required_layout.addWidget(self.authors_listview, 4, 1)
        required_layout.addLayout(authors_btn_vbox, 4, 2)
        required_layout.addWidget(test_inputs_label, 5, 0)
        required_layout.addWidget(self.test_inputs_listview, 5, 1)
        required_layout.addLayout(test_inputs_vbox, 5, 2)
        required_layout.addWidget(test_outputs_label, 6, 0)
        required_layout.addWidget(self.test_outputs_listview, 6, 1)
        required_layout.addLayout(test_outputs_vbox, 6, 2)
        required_layout.setRowStretch(-1, 1)
        #
        frame = QFrame()
        frame.setFrameStyle(QFrame.NoFrame)
        frame.setLayout(required_layout)

        return frame

    def create_other_spec_ui(self):
        """Create ui for optional specs."""
        covers_label = QLabel("Covers:")
        self.covers_listview = QListWidget()
        self.covers_listview.setFixedHeight(100)
        covers_button_add = QPushButton("Add Image File")
        covers_button_add.clicked.connect(self.add_cover_image)
        covers_button_add_uri = QPushButton("Add from URI")
        covers_button_add_uri.clicked.connect(self.add_cover_from_uri)
        covers_button_del = QPushButton("Remove")
        covers_button_del.clicked.connect(self.del_cover)
        covers_btn_vbox = QVBoxLayout()
        covers_btn_vbox.addWidget(covers_button_add)
        covers_btn_vbox.addWidget(covers_button_add_uri)
        covers_btn_vbox.addWidget(covers_button_del)
        #
        tags_widget = TagsInputWidget(predefined_tags=TAGS)
        #
        grid = QGridLayout()
        grid.addWidget(covers_label, 0, 0)
        grid.addWidget(self.covers_listview, 0, 1)
        grid.addLayout(covers_btn_vbox, 0, 2)
        grid.addWidget(tags_widget, 1, 0, 1, 3, alignment=Qt.AlignTop | Qt.AlignLeft)

        frame = QFrame()
        frame.setFrameStyle(QFrame.NoFrame)
        frame.setLayout(grid)

        return frame

    def select_file(self, filter: str, output_widget: QWidget = None):
        """Opens a file dialog and set the selected file into given widget's text."""
        selected_file, _filter = QFileDialog.getOpenFileName(self, "Browse", ".", filter)
        if output_widget is not None:
            output_widget.setText(selected_file)

        return selected_file

    def get_spdx_licenses(self):
        """Read the licenses identifier from the json file aquired from https://github.com/spdx/license-list-data/tree/main/json."""
        with open(SPDX_LICENSES) as f:
            licenses: List[Dict] = json.load(f).get("licenses", [])
        return [lic["licenseId"] for lic in licenses]

    def show_author_form(self, edit: bool = False):
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

    def update_authors(self, author: nodes.rdf.Author):
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
            reply = QMessageBox.warning(
                self, "Bioimage.io", "Are you sure you want to remove the selected author?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.authors[curr_row]
                self.populate_authors_list()

    def add_cover_image(self):
        """Select cover image(s) by a file dialog."""
        selected_files, _ = QFileDialog.getOpenFileNames(
            self, "Select Cover Image(s)", ".", "Images(*.png *.jpg *.gif)"
        )
        for file in selected_files:
            self.covers_listview.addItem(file)

    def add_cover_from_uri(self):
        """Shows a simple form to get a URI string."""
        def _get_uri(uri):
            if len(uri) > 0:
                self.covers_listview.addItem(uri)

        input_win = SingleInputWidget(label="Cover Image URI:", title="Cover Image")
        input_win.setWindowModality(Qt.ApplicationModal)
        input_win.submit.connect(_get_uri)
        input_win.show()

    def del_cover(self):
        """Delete the selected cover url/file."""
        curr_row = self.covers_listview.currentRow()
        if curr_row > -1:
            reply = QMessageBox.warning(
                self, "Bioimage.io", "Are you sure you want to remove the selected cover?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.covers_listview.takeItem(curr_row)

    def select_npy_file(self, list_widget: QListWidget):
        """Select a numpy file as a test input."""
        selected_file = self.select_file("Numpy File (*.npy)")
        list_widget.addItem(selected_file)

    def del_test_io(self, list_widget: QListWidget):
        """Delete the selected test input file."""
        curr_row = list_widget.currentRow()
        if curr_row > -1:
            reply = QMessageBox.warning(
                self, "Bioimage.io", "Are you sure you want to remove the selected test input?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                list_widget.takeItem(curr_row)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
