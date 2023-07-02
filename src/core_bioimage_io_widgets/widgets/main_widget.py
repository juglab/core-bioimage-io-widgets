import sys
import datetime as dt
from typing import List

import yaml
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
    FORMAT_VERSION, WEIGHT_FORMATS, PYTORCH_STATE_DICT
)
from core_bioimage_io_widgets.widgets.ui_helper import (
    enhance_widget, remove_from_listview,
    get_ui_input_data, select_file,
    create_validation_ui, save_file_as,
    set_ui_data_from_dict, set_widget_text
)
from core_bioimage_io_widgets.widgets.author_widget import AuthorWidget
from core_bioimage_io_widgets.widgets.single_input_widget import SingleInputWidget
from core_bioimage_io_widgets.widgets.tags_input_widget import TagsInputWidget
from core_bioimage_io_widgets.widgets.inputs_widget import InputTensorWidget
from core_bioimage_io_widgets.widgets.outputs_widget import OutputTensorWidget
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class BioImageModelWidget(QWidget):
    """A QT widget for bioimage.io model specifications."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model: nodes.model.Model = None
        self.model_schema = schemas.model.Model()
        self.authors: List[dict] = []
        self.input_tensors: List[dict] = []
        self.test_inputs: List[str] = []
        self.output_tensors: List[dict] = []
        self.test_outputs: List[str] = []

        tabs = QTabWidget()
        tabs.addTab(self.create_required_specs_ui(), "Required Fields")
        tabs.addTab(self.create_other_spec_ui(), "Optional Fields")
        #
        load_button = QPushButton("&Load config")
        load_button.clicked.connect(self.load_specs)
        save_button = QPushButton("&Save config")
        save_button.clicked.connect(self.save_specs)
        btn_hbox = QHBoxLayout()
        btn_hbox.addWidget(load_button)
        btn_hbox.addWidget(save_button)

        grid = QGridLayout()
        grid.addWidget(tabs, 0, 0)
        grid.addLayout(btn_hbox, 1, 0, alignment=Qt.AlignRight)

        self.setLayout(grid)
        self.setWindowTitle("Bioimage.io Model Specification")

    def save_specs(self):
        """Save the user-entered model specs into a YAML file."""
        # collect part of data from ui-entries with a schema fields attached to them:
        model_data = get_ui_input_data(self)
        # remove 'architecture' and 'architecture_sha256' fields from model_data direct properties.
        if "architecture" in model_data.keys():
            del model_data["architecture"]
        if "architecture_sha256" in model_data.keys():
            del model_data["architecture_sha256"]
        # set the model's weights data
        weights = {
                self.weights_combo.currentText(): {
                    'source': self.weights_textbox.text()
                }
        }
        # on pytorch_state_dict format must add architecture & sha256 fields
        if self.weights_combo.currentText() == PYTORCH_STATE_DICT:
            weights[self.weights_combo.currentText()]["architecture"] = self.model_source_textbox.text()
            weights[self.weights_combo.currentText()]["architecture_sha256"] = \
                self.model_source_sha256_textbox.text()
        # add other required data
        model_data.update({
            "type": "model",
            "format_version": FORMAT_VERSION,
            "timestamp": dt.datetime.now().isoformat(),
            "authors": self.authors,
            "weights": weights,
            "test_inputs": self.test_inputs,
            "inputs": self.input_tensors,
            "test_outputs": self.test_outputs,
            "outputs": self.output_tensors,
        })
        # add optional data
        if self.covers_listview.count() > 0:
            model_data["covers"] = [
                self.covers_listview.item(i).text()
                for i in range(self.covers_listview.count())
            ]
        if len(self.tags_widget.tags) > 0:
            model_data["tags"] = self.tags_widget.tags
        # validate the model data
        model_schema = schemas.model.Model()
        errors = model_schema.validate(model_data)
        if errors:
            validation_win = ValidationWidget()
            validation_win.update_content(create_validation_ui(errors))
            validation_win.setMinimumHeight(300)
            validation_win.show()
            return

        dest_file = save_file_as("Yaml file (*.yaml)", f"./{model_data['name'].replace(' ', '_')}.yaml", self)
        if dest_file:
            with open(dest_file, mode="w") as f:
                yaml.safe_dump(model_data, f, default_flow_style=False)

    def load_specs(self):
        """Load the model's specifications from a yaml file."""
        selected_yml = select_file("Yaml file (*.yaml)", self)
        with open(selected_yml) as f:
            model_data = yaml.safe_load(f)
        print(model_data)
        # TODO: model_data should be valid specs
        # set ui data
        set_ui_data_from_dict(self, model_data)  # handles basic direct inputs
        # weights
        weight_type = list(model_data["weights"].keys())[0]
        weight_specs = model_data["weights"][weight_type]
        set_widget_text(self.weights_combo, weight_type)
        self.weights_textbox.setText(weight_specs["source"])
        if weight_type == PYTORCH_STATE_DICT:
            self.model_source_textbox.setText(weight_specs["architecture"])
            self.model_source_sha256_textbox.setText(weight_specs.get("architecture_sha256", ""))
        # authors
        self.authors = model_data["authors"]
        self.populate_authors_list()
        # inputs
        self.input_tensors = model_data["inputs"]
        self.test_inputs = model_data["test_inputs"]
        self.populate_inputs_list()
        # outputs
        self.output_tensors = model_data["outputs"]
        self.test_outputs = model_data["test_outputs"]
        self.populate_outputs_list()
        # covers
        for cover in model_data.get("covers", []):
            self.covers_listview.addItem(cover)
        # tags
        self.tags_widget.tags = model_data["tags"]
        self.tags_widget.refresh_tags()

    def create_required_specs_ui(self):
        """Create ui for the required specs."""
        # model name
        name_textbox = QLineEdit()
        name_label, _ = enhance_widget(name_textbox, "Model Name", self.model_schema.fields["name"])
        # model's description
        description_textbox = QPlainTextEdit()
        description_textbox.setFixedHeight(65)
        description_label, _ = enhance_widget(
            description_textbox, "Description", self.model_schema.fields["description"]
        )
        # license
        license_combo = QComboBox()
        license_combo.addItems(get_spdx_licenses())
        license_combo.setEditable(True)
        license_combo.setInsertPolicy(QComboBox.NoInsert)
        license_completer = QCompleter(get_spdx_licenses())
        license_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        license_completer.setCaseSensitivity(Qt.CaseInsensitive)
        license_combo.setCompleter(license_completer)
        license_label, _ = enhance_widget(license_combo, "License", self.model_schema.fields["license"])
        # documentation
        doc_textbox = QLineEdit()
        doc_textbox.setPlaceholderText("Select Documentation file (*.md)")
        doc_textbox.setReadOnly(True)
        doc_label, _ = enhance_widget(doc_textbox, "Documentation", self.model_schema.fields["documentation"])
        doc_button = QPushButton("Browse...")
        doc_button.clicked.connect(lambda: select_file("Mark Down files (*.md)", self, doc_textbox))
        # model's weights
        weights_type_label = QLabel("Weights Format<sup>*</sup>:")
        self.weights_combo = QComboBox()
        self.weights_combo.addItems(WEIGHT_FORMATS)
        self.weights_combo.currentIndexChanged.connect(self.check_weight_format)
        weights_label = QLabel("Weights File<sup>*</sup>:")
        self.weights_textbox = QLineEdit()
        self.weights_textbox.setPlaceholderText("Select model's weights file")
        self.weights_textbox.setReadOnly(True)
        weights_button = QPushButton("Browse...")
        weights_button.clicked.connect(lambda: select_file("*.*", self, self.weights_textbox))
        # if weight format selected as pytorch_state_dict
        pytorch_state_dict_schema = schemas.model.PytorchStateDictWeightsEntry()
        self.model_source_textbox = QLineEdit()
        self.model_src_label, _ = enhance_widget(
            self.model_source_textbox, "Model Source Code",
            pytorch_state_dict_schema.fields["architecture"]
        )
        self.model_source_sha256_textbox = QLineEdit()
        self.model_src_sha256_label, _ = enhance_widget(
            self.model_source_sha256_textbox, "Model Source Code SHA256",
            pytorch_state_dict_schema.fields["architecture_sha256"]
        )
        # authors
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
        # inputs
        inputs_label = QLabel("Inputs<sup>*</sup>:")
        self.inputs_listview = QListWidget()
        self.inputs_listview.setFixedHeight(70)
        inputs_button_add = QPushButton("Add")
        inputs_button_add.clicked.connect(lambda: self.show_input_form())
        inputs_button_del = QPushButton("Remove")
        inputs_button_del.clicked.connect(self.del_input)
        self.inputs_btn_vbox = QVBoxLayout()
        self.inputs_btn_vbox.addWidget(inputs_button_add)
        self.inputs_btn_vbox.addWidget(inputs_button_del)
        # outputs
        outputs_label = QLabel("Outputs<sup>*</sup>:")
        self.outputs_listview = QListWidget()
        self.outputs_listview.setFixedHeight(70)
        outputs_button_add = QPushButton("Add")
        outputs_button_add.clicked.connect(lambda: self.show_output_form())
        outputs_button_del = QPushButton("Remove")
        outputs_button_del.clicked.connect(self.del_output)
        self.outputs_btn_vbox = QVBoxLayout()
        self.outputs_btn_vbox.addWidget(outputs_button_add)
        self.outputs_btn_vbox.addWidget(outputs_button_del)
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
        required_layout.addWidget(self.weights_combo, 4, 1)
        required_layout.addWidget(weights_label, 5, 0)
        required_layout.addWidget(self.weights_textbox, 5, 1)
        required_layout.addWidget(weights_button, 5, 2)
        required_layout.addWidget(self.model_src_label, 6, 0)
        required_layout.addWidget(self.model_source_textbox, 6, 1)
        required_layout.addWidget(self.model_src_sha256_label, 7, 0)
        required_layout.addWidget(self.model_source_sha256_textbox, 7, 1)
        required_layout.addWidget(authors_label, 8, 0)
        required_layout.addWidget(self.authors_listview, 8, 1)
        required_layout.addLayout(authors_btn_vbox, 8, 2)
        required_layout.addWidget(inputs_label, 9, 0)
        required_layout.addWidget(self.inputs_listview, 9, 1)
        required_layout.addLayout(self.inputs_btn_vbox, 9, 2)
        required_layout.addWidget(outputs_label, 10, 0)
        required_layout.addWidget(self.outputs_listview, 10, 1)
        required_layout.addLayout(self.outputs_btn_vbox, 10, 2)
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
        covers_button_del.clicked.connect(lambda: remove_from_listview(
                self.covers_listview, "Are you sure you want to remove the selected cover?"
        ))
        covers_btn_vbox = QVBoxLayout()
        covers_btn_vbox.addWidget(covers_button_add)
        covers_btn_vbox.addWidget(covers_button_add_uri)
        covers_btn_vbox.addWidget(covers_button_del)
        #
        self.tags_widget = TagsInputWidget(predefined_tags=get_predefined_tags())
        #
        grid = QGridLayout()
        grid.addWidget(covers_label, 0, 0)
        grid.addWidget(self.covers_listview, 0, 1)
        grid.addLayout(covers_btn_vbox, 0, 2)
        grid.addWidget(self.tags_widget, 1, 0, 1, 3, alignment=Qt.AlignTop | Qt.AlignLeft)

        frame = QFrame()
        frame.setFrameStyle(QFrame.NoFrame)
        frame.setLayout(grid)

        return frame

    def check_weight_format(self):
        """Disable model source code/sha256 input boxes if the weight format is 'pytorch_state_dict'."""
        if self.weights_combo.currentText() == PYTORCH_STATE_DICT:
            self.model_source_textbox.setEnabled(True)
            self.model_source_sha256_textbox.setEnabled(True)
            self.model_src_label.setEnabled(True)
            self.model_src_sha256_label.setEnabled(True)
        else:
            self.model_source_textbox.setText("")
            self.model_source_textbox.setEnabled(False)
            self.model_source_sha256_textbox.setText("")
            self.model_source_sha256_textbox.setEnabled(False)
            self.model_src_label.setEnabled(False)
            self.model_src_sha256_label.setEnabled(False)

    def show_author_form(self, edit=False):
        """Shows the author form to add a new or modify selected author."""
        author_data: dict = None
        if edit:
            curr_row = self.authors_listview.currentRow()
            if curr_row > -1:
                author_data = self.authors[curr_row]
            else:
                return
        else:
            # new entry: unselect current row
            self.authors_listview.setCurrentRow(-1)
        # show the author's form
        author_win = AuthorWidget(author_data=author_data)
        author_win.setWindowModality(Qt.ApplicationModal)
        author_win.submit.connect(self.update_author)
        author_win.show()

    def populate_authors_list(self):
        """Populates the authors' listview widget with the list of authors."""
        self.authors_listview.clear()
        self.authors_listview.addItems(author["name"] for author in self.authors)

    def update_author(self, author_data: dict):
        """Modify or add new author to the list."""
        curr_row = self.authors_listview.currentRow()
        if curr_row > -1:
            self.authors[curr_row] = author_data
        else:
            self.authors.append(author_data)
        self.populate_authors_list()

    def del_author(self):
        """Remove the selected author."""
        reply, del_row = remove_from_listview(
            self, self.authors_listview, "Are you sure you want to remove the selected author?"
        )
        if reply:
            del self.authors[del_row]
            self.populate_authors_list()

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
        selected_file = select_file("Numpy File (*.npy)", parent=self)
        list_widget.addItem(selected_file)

    def show_input_form(self):
        """Shows the input form to add a new model's input."""
        input_win = InputTensorWidget(
            input_names=[item["name"] for item in self.input_tensors]
        )
        input_win.setWindowModality(Qt.ApplicationModal)
        input_win.submit.connect(self.update_input)
        input_win.show()

    def populate_inputs_list(self):
        """Populates the inputs' listview widget with the list of model's inputs."""
        self.inputs_listview.clear()
        self.inputs_listview.addItems(
            f"{in_tensor['name']} ({in_test})"
            for in_tensor, in_test in zip(self.input_tensors, self.test_inputs)
        )

    def update_input(self, model_input: dict):
        """Add a new model's input to the list."""
        # model_input keys: 'test_input', 'input_tensor'
        self.input_tensors.append(model_input['input_tensor'])
        self.test_inputs.append(model_input['test_input'])
        self.populate_inputs_list()

    def del_input(self):
        """Remove the selected input."""
        reply, del_row = remove_from_listview(
            self, self.inputs_listview, "Are you sure you want to remove the selected input?"
        )
        if reply:
            del self.input_tensors[del_row]
            del self.test_inputs[del_row]
            self.populate_inputs_list()

    def show_output_form(self):
        """Shows the output form to add a new model's output."""
        output_win = OutputTensorWidget(
            output_names=[item["name"] for item in self.output_tensors]
        )
        output_win.setWindowModality(Qt.ApplicationModal)
        output_win.submit.connect(self.update_output)
        output_win.show()

    def populate_outputs_list(self):
        """Populates the outputs' listview widget with the list of model's outputs."""
        self.outputs_listview.clear()
        self.outputs_listview.addItems(
            f"{out_tensor['name']} ({out_test})"
            for out_tensor, out_test in zip(self.output_tensors, self.test_outputs)
        )

    def update_output(self, model_output: dict):
        """Add a new model's output to the list."""
        # model_output keys: 'test_output', 'output_tensor'
        self.output_tensors.append(model_output['output_tensor'])
        self.test_outputs.append(model_output['test_output'])
        self.populate_outputs_list()

    def del_output(self):
        """Remove the selected output."""
        reply, del_row = remove_from_listview(
            self, self.outputs_listview, "Are you sure you want to remove the selected output?"
        )
        if reply:
            del self.output_tensors[del_row]
            del self.test_outputs[del_row]
            self.populate_outputs_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
