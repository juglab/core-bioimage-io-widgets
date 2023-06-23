import sys
from typing import List

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QApplication, 
    QGridLayout, QVBoxLayout, QHBoxLayout,
    QComboBox, QCompleter, QFileDialog,
    QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QFrame, QListWidget,
    QMessageBox, QTabWidget
)

from core_bioimage_io_widgets.utils import (
    nodes, schemas,
    get_spdx_licenses, get_predefined_tags,
    FORMAT_VERSION, WEIGHT_FORMATS,
)
from core_bioimage_io_widgets.widgets.ui_helper import (
    enhance_widget, remove_from_list
)
from core_bioimage_io_widgets.widgets.author_widget import AuthorWidget
from core_bioimage_io_widgets.widgets.single_input_widget import SingleInputWidget
from core_bioimage_io_widgets.widgets.tags_input_widget import TagsInputWidget
from core_bioimage_io_widgets.widgets.inputs_widget import InputTensorWidget


class BioImageModelWidget(QWidget):
    """A QT widget for bioimage.io model specs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model: nodes.model.Model = None
        self.model_schema = schemas.model.Model()
        self.authors: List[nodes.rdf.Author] = []
        self.input_tensors: List[nodes.model.InputTensor] = []
        self.test_inputs: List[str] = []

        tabs = QTabWidget()
        tabs.addTab(self.create_required_specs_ui(), "Required Fields")
        tabs.addTab(self.create_other_spec_ui(), "Optional Fields")
        #
        load_button = QPushButton("&Load config")
        save_button = QPushButton("&Save config")
        btn_hbox = QHBoxLayout()
        btn_hbox.addWidget(load_button)
        btn_hbox.addWidget(save_button)

        grid = QGridLayout()
        grid.addWidget(tabs, 0, 0)
        grid.addLayout(btn_hbox, 1, 0, alignment=Qt.AlignRight)

        self.setLayout(grid)
        self.setWindowTitle("Bioimage.io Model Specification")

        self.populate_authors_list()
        self.populate_inputs_list()

    def save_specs(self):
        """Save the user-entered model specs into a YAML file."""
        pass

    def create_required_specs_ui(self):
        """Create ui for the required specs."""
        name_textbox = QLineEdit()
        name_label, _ = enhance_widget(name_textbox, "Model Name", self.model_schema.fields["name"])
        #
        description_textbox = QPlainTextEdit()
        description_textbox.setFixedHeight(65)
        description_label, _ = enhance_widget(
            description_textbox, "Description", self.model_schema.fields["description"]
        )
        #
        license_combo = QComboBox()
        license_combo.addItems(get_spdx_licenses())
        license_combo.setEditable(True)
        license_combo.setInsertPolicy(QComboBox.NoInsert)
        license_completer = QCompleter(get_spdx_licenses())
        license_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        license_completer.setCaseSensitivity(Qt.CaseInsensitive)
        license_combo.setCompleter(license_completer)
        license_label, _ = enhance_widget(license_combo, "License", self.model_schema.fields["license"])
        #
        doc_textbox = QLineEdit()
        doc_textbox.setPlaceholderText("Select Documentation file (*.md)")
        doc_textbox.setReadOnly(True)
        doc_label, _ = enhance_widget(doc_textbox, "Documentation", self.model_schema.fields["documentation"])
        doc_button = QPushButton("Browse...")
        doc_button.clicked.connect(lambda: self.select_file("Mark Down files (*.md)", doc_textbox))
        #
        weights_type_label = QLabel("Weights Format<sup>*</sup>:")
        weights_combo = QComboBox()
        weights_combo.addItems(WEIGHT_FORMATS)
        weights_label = QLabel("Weights File<sup>*</sup>:")
        weights_textbox = QLineEdit()
        weights_textbox.setPlaceholderText("Select model's weights file")
        weights_textbox.setReadOnly(True)
        # weight_label, _ = enhance_widget(weight_textbox, "Weights", self.model_schema.fields["weights"])
        weights_button = QPushButton("Browse...")
        weights_button.clicked.connect(lambda: self.select_file("*.*", weights_textbox))
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
        inputs_label = QLabel("Inputs<sup>*</sup>:")
        self.inputs_listview = QListWidget()
        self.inputs_listview.setFixedHeight(70)
        inputs_button_add = QPushButton("Add")
        inputs_button_add.clicked.connect(lambda: self.show_input_form())
        # inputs_button_edit = QPushButton("Edit")
        # inputs_button_edit.clicked.connect(lambda: self.show_input_form())
        inputs_button_del = QPushButton("Remove")
        inputs_button_del.clicked.connect(self.del_input)
        self.inputs_btn_vbox = QVBoxLayout()
        self.inputs_btn_vbox.addWidget(inputs_button_add)
        # self.inputs_btn_vbox.addWidget(inputs_button_edit)
        self.inputs_btn_vbox.addWidget(inputs_button_del)
        #
        self.test_outputs_listview = QListWidget()
        self.test_outputs_listview.setFixedHeight(70)
        test_outputs_label, _ = enhance_widget(
            self.test_outputs_listview, "Test Outputs", self.model_schema.fields["test_outputs"]
        )
        test_outputs_button_add = QPushButton("Add")
        test_outputs_button_add.clicked.connect(
            lambda: self.select_add_npy_to_listview(self.test_outputs_listview)
        )
        test_outputs_button_del = QPushButton("Remove")
        test_outputs_button_del.clicked.connect(
            lambda: remove_from_list(self.test_outputs_listview)
        )
        test_outputs_vbox = QVBoxLayout()
        test_outputs_vbox.addWidget(test_outputs_button_add)
        test_outputs_vbox.addWidget(test_outputs_button_del)
        #
        required_layout = QGridLayout()
        required_layout.addWidget(name_label, 0, 0)
        required_layout.addWidget(name_textbox, 0, 1)
        required_layout.addWidget(description_label, 1, 0)
        required_layout.addWidget(description_textbox, 1, 1)
        required_layout.addWidget(license_label, 2, 0)
        required_layout.addWidget(license_combo, 2, 1)
        required_layout.addWidget(doc_label, 3, 0)
        required_layout.addWidget(doc_textbox, 3, 1)
        required_layout.addWidget(doc_button, 3, 2)
        required_layout.addWidget(weights_type_label, 4, 0)
        required_layout.addWidget(weights_combo, 4, 1)
        required_layout.addWidget(weights_label, 5, 0)
        required_layout.addWidget(weights_textbox, 5, 1)
        required_layout.addWidget(weights_button, 5, 2)
        required_layout.addWidget(authors_label, 6, 0)
        required_layout.addWidget(self.authors_listview, 6, 1)
        required_layout.addLayout(authors_btn_vbox, 6, 2)
        required_layout.addWidget(inputs_label, 7, 0)
        required_layout.addWidget(self.inputs_listview, 7, 1)
        required_layout.addLayout(self.inputs_btn_vbox, 7, 2)
        required_layout.addWidget(test_outputs_label, 8, 0)
        required_layout.addWidget(self.test_outputs_listview, 8, 1)
        required_layout.addLayout(test_outputs_vbox, 8, 2)
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
        covers_button_add.clicked.connect(self.add_cover_images)
        covers_button_add_uri = QPushButton("Add from URI")
        covers_button_add_uri.clicked.connect(self.add_cover_from_uri)
        covers_button_del = QPushButton("Remove")
        covers_button_del.clicked.connect(
            lambda: remove_from_list(self.covers_listview,
                                          "Are you sure you want to remove the selected cover?")
        )
        covers_btn_vbox = QVBoxLayout()
        covers_btn_vbox.addWidget(covers_button_add)
        covers_btn_vbox.addWidget(covers_button_add_uri)
        covers_btn_vbox.addWidget(covers_button_del)
        #
        tags_widget = TagsInputWidget(predefined_tags=get_predefined_tags())
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

    def show_author_form(self, edit=False):
        """Shows the author form to add a new or modify selected author."""
        author: nodes.rdf.Author = None
        if edit:
            curr_row = self.authors_listview.currentRow()
            if curr_row > -1:
                author = self.authors[curr_row]
            else:
                return
        else:
            # new entry: unselect current row
            self.authors_listview.setCurrentRow(-1)
        # show the author's form
        author_win = AuthorWidget(author=author)
        author_win.setWindowModality(Qt.ApplicationModal)
        author_win.submit.connect(self.update_author)
        author_win.show()

    def populate_authors_list(self):
        """Populates the authors' listview widget with the list of authors."""
        self.authors_listview.clear()
        self.authors_listview.addItems(author.name for author in self.authors)

    def update_author(self, author: nodes.rdf.Author):
        """Modify or add new author to the list."""
        curr_row = self.authors_listview.currentRow()
        if curr_row > -1:
            self.authors[curr_row] = author
        else:
            self.authors.append(author)
        self.populate_authors_list()

    def del_author(self):
        """Remove the selected author."""
        reply, del_row = remove_from_list(
            self.authors_listview, "Are you sure you want to remove the selected author?"
        )
        if reply:
            del self.authors[del_row]
            self.populate_authors_list()

    def select_file(self, filter: str, output_widget: QWidget = None):
        """Opens a file dialog and set the selected file into given widget's text."""
        selected_file, _filter = QFileDialog.getOpenFileName(self, "Browse", ".", filter)
        if output_widget is not None:
            output_widget.setText(selected_file)

        return selected_file

    def add_cover_images(self):
        """Select cover images by a file dialog, and add them to the Cover's listview."""
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

    def select_add_npy_to_listview(self, list_widget: QListWidget):
        """Select a numpy file as a test input/outpu and add it to the listview."""
        selected_file = self.select_file("Numpy File (*.npy)")
        list_widget.addItem(selected_file)

    def show_input_form(self):
        """Shows the input form to add a new model's input."""
        # show the input's form
        input_win = InputTensorWidget(
            model_input=None,
            input_names=[item.name for item in self.input_tensors]
        )
        input_win.setWindowModality(Qt.ApplicationModal)
        input_win.submit.connect(self.update_input)
        input_win.show()

    def populate_inputs_list(self):
        """Populates the inputs' listview widget with the list of model's inputs."""
        self.inputs_listview.clear()
        self.inputs_listview.addItems(
            f"{in_tensor.name} ({in_test})"
            for in_tensor, in_test in zip(self.input_tensors, self.test_inputs)
        )

    def update_input(self, model_input: dict):
        """Add a new model input to the list."""
        # model_input keys: 'test_input', 'input_tensor'
        self.input_tensors.append(model_input['input_tensor'])
        self.test_inputs.append(model_input['test_input'])
        self.populate_inputs_list()

    def del_input(self):
        """Remove the selected input."""
        reply, del_row = remove_from_list(
            self, self.inputs_listview, "Are you sure you want to remove the selected input?"
        )
        if reply:
            del self.input_tensors[del_row]
            del self.test_inputs[del_row]
            self.populate_inputs_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
