import datetime as dt
import sys
from typing import List, Optional

import yaml
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core_bioimage_io_widgets.utils import (
    FORMAT_VERSION,
    PYTORCH_STATE_DICT,
    WEIGHT_FORMATS,
    build_model_zip,
    get_predefined_tags,
    get_spdx_licenses,
    nodes,
    schemas,
)
from core_bioimage_io_widgets.widgets.author_widget import AuthorWidget
from core_bioimage_io_widgets.widgets.cite_widget import CiteWidget
from core_bioimage_io_widgets.widgets.inputs_widget import InputTensorWidget
from core_bioimage_io_widgets.widgets.outputs_widget import OutputTensorWidget
from core_bioimage_io_widgets.widgets.single_input_widget import SingleInputWidget
from core_bioimage_io_widgets.widgets.tags_input_widget import TagsInputWidget
from core_bioimage_io_widgets.widgets.ui_helper import (
    create_validation_ui,
    enhance_widget,
    get_ui_input_data,
    remove_from_listview,
    save_file_as,
    select_file,
    set_ui_data_from_dict,
    set_widget_text,
)
from core_bioimage_io_widgets.widgets.validation_widget import ValidationWidget


class BioImageModelWidget(QWidget):
    """A QT widget for bioimage.io model specifications."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.model: nodes.model.Model = None
        self.model_schema = schemas.model.Model()
        self.authors: List[dict] = []
        self.input_tensors: List[dict] = []
        self.test_inputs: List[str] = []
        self.output_tensors: List[dict] = []
        self.test_outputs: List[str] = []
        self.cites: List[dict] = []

        tabs = QTabWidget()
        tabs.addTab(self.create_required_specs_ui(), "Required Fields")
        tabs.addTab(self.create_other_spec_ui(), "Optional Fields")
        #
        load_button = QPushButton("&Load Config")
        load_button.setToolTip("To load a model specifications from a YAML file.")
        load_button.clicked.connect(self.load_from_file)
        save_button = QPushButton("&Save Config")
        save_button.setToolTip("To save the model specifications to a YAML file.")
        save_button.clicked.connect(self.save_specs)
        build_button = QPushButton("&Build Model")
        build_button.setToolTip(
            "To export the model to the zip format compatible with the BioImage model"
            " zoo."
        )
        build_button.clicked.connect(self.build_model)
        btn_hbox = QHBoxLayout()
        btn_hbox.addWidget(load_button)
        btn_hbox.addWidget(save_button)
        btn_hbox.addWidget(build_button)

        grid = QGridLayout()
        grid.addWidget(tabs, 0, 0)
        grid.addLayout(btn_hbox, 1, 0, alignment=Qt.AlignRight)

        self.setLayout(grid)
        self.setWindowTitle("Bioimage.io Model Specification")

    def save_specs(self) -> None:
        """Save the model specs into a YAML file."""
        model_data = self.collect_specs()
        if model_data:
            dest_file = save_file_as(
                "Yaml file (*.yaml)",
                f"./{model_data['name'].replace(' ', '_')}.yaml",
                self,
            )
            if dest_file:
                with open(dest_file, mode="w") as f:
                    yaml.safe_dump(model_data, f, default_flow_style=False)
                QMessageBox.information(
                    self, "BioImage.io", "Model data saved successfully."
                )

    def load_from_file(self) -> None:
        """Open a file dialog to select model YAML file."""
        selected_yml = select_file("Yaml file (*.yaml)", self)
        if selected_yml:
            with open(selected_yml) as f:
                model_data = yaml.safe_load(f)
                self.load_specs(model_data)

    def collect_specs(self) -> Optional[dict]:
        """Collect and validate model specifications from ui."""
        # collect part of data from ui-entries with a schema fields attached to them:
        model_data = get_ui_input_data(self)
        # remove 'architecture' and 'architecture_sha256' fields
        # from model_data direct properties.
        if "architecture" in model_data.keys():
            del model_data["architecture"]
        if "architecture_sha256" in model_data.keys():
            del model_data["architecture_sha256"]
        # set the model's weights data
        weights = {
            self.weights_combo.currentText(): {"source": self.weights_textbox.text()}
        }
        # on pytorch_state_dict format must add architecture & sha256 fields
        if self.weights_combo.currentText() == PYTORCH_STATE_DICT:
            weights[self.weights_combo.currentText()][
                "architecture"
            ] = self.model_source_textbox.text()
            weights[self.weights_combo.currentText()][
                "architecture_sha256"
            ] = self.model_source_sha256_textbox.text()
        # add other required data
        model_data.update(
            {
                "type": "model",
                "format_version": FORMAT_VERSION,
                "timestamp": dt.datetime.now().isoformat(),
                "authors": self.authors,
                "cite": self.cites,
                "weights": weights,
                "test_inputs": self.test_inputs,
                "inputs": self.input_tensors,
                "test_outputs": self.test_outputs,
                "outputs": self.output_tensors,
            }
        )
        # add optional data
        if self.covers_listview.count() > 0:
            model_data["covers"] = [
                self.covers_listview.item(i).text()
                for i in range(self.covers_listview.count())
            ]
        if len(self.tags_widget.tags) > 0:
            model_data["tags"] = self.tags_widget.tags
        # validate the model data
        if self.is_valid(model_data):
            return model_data

        return None

    def load_specs(self, model_data: dict) -> None:
        """
        Fill ui with the the given model's specifications.

        Parameters
        ----------
        model_data: dict
            a dictionary contains all required and optional fields
            for validationg a model RDF specs.
        """
        # model_data should be a valid specs (only show potential errors)
        self.is_valid(model_data)
        # set ui data
        set_ui_data_from_dict(self, model_data)  # handles basic direct inputs
        # weights
        weight_type = list(model_data["weights"].keys())[0]
        weight_specs = model_data["weights"][weight_type]
        set_widget_text(self.weights_combo, weight_type)
        self.weights_textbox.setText(weight_specs["source"])
        if weight_type == PYTORCH_STATE_DICT:
            self.model_source_textbox.setText(weight_specs["architecture"])
            self.model_source_sha256_textbox.setText(
                weight_specs.get("architecture_sha256", "")
            )
        # authors
        self.authors = model_data["authors"]
        self.populate_authors_list()
        # cites
        self.cites = model_data["cite"]
        self.populate_cites_list()
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

    def build_model(self) -> None:
        """Build bioimage model zip file."""
        model_data = self.collect_specs()
        if model_data is None:
            return

        dest_file = save_file_as(
            "Zip file (*.zip)", f"./{model_data['name'].replace(' ', '_')}.zip", self
        )
        if dest_file:
            # buil model zip file
            build_model_zip(model_data, dest_file)
            QMessageBox.information(
                self, "BioImage.io", "Model zip file created successfully."
            )

    def is_valid(self, model_data: dict) -> bool:
        """Validate passed model_data against the model schema."""
        model_schema = schemas.model.Model()
        errors = model_schema.validate(model_data)
        # NOTE: check for the model's name to be not empty.
        if len(errors) == 0:
            if len(model_data["name"]) == 0:
                errors["name"] = ["Model's name is required."]

        if errors:
            validation_win = ValidationWidget()
            validation_win.update_content(create_validation_ui(errors))
            validation_win.setMinimumHeight(300)
            validation_win.show()
            return False

        return True

    def create_required_specs_ui(self) -> QWidget:
        """Create ui for the required specifications and fields."""
        # model name
        name_textbox = QLineEdit()
        name_label, _ = enhance_widget(
            name_textbox, "Model Name", self.model_schema.fields["name"]
        )

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
        license_label, _ = enhance_widget(
            license_combo, "License", self.model_schema.fields["license"]
        )

        # documentation
        doc_textbox = QLineEdit()
        doc_textbox.setPlaceholderText("Select Documentation file (*.md)")
        doc_textbox.setReadOnly(True)
        doc_label, _ = enhance_widget(
            doc_textbox, "Documentation", self.model_schema.fields["documentation"]
        )
        doc_button = QPushButton("Browse...")
        doc_button.clicked.connect(
            lambda: select_file("Mark Down files (*.md)", self, doc_textbox)
        )

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
        weights_button.clicked.connect(
            lambda: select_file("*.*", self, self.weights_textbox)
        )
        # if weight format selected as pytorch_state_dict
        pytorch_state_dict_schema = schemas.model.PytorchStateDictWeightsEntry()
        self.model_source_textbox = QLineEdit()
        self.model_src_label, _ = enhance_widget(
            self.model_source_textbox,
            "Model Source Code",
            pytorch_state_dict_schema.fields["architecture"],
        )
        self.model_source_sha256_textbox = QLineEdit()
        self.model_src_sha256_label, _ = enhance_widget(
            self.model_source_sha256_textbox,
            "Model Source Code SHA256",
            pytorch_state_dict_schema.fields["architecture_sha256"],
        )

        # authors
        authors_label = QLabel("Authors<sup>*</sup>:")
        self.authors_listview = QListWidget()
        self.authors_listview.setFixedHeight(70)
        authors_button_add = QPushButton("Add")
        authors_button_add.clicked.connect(self.new_author)
        authors_button_edit = QPushButton("Edit")
        authors_button_edit.clicked.connect(self.edit_author)
        authors_button_del = QPushButton("Remove")
        authors_button_del.clicked.connect(self.del_author)
        authors_btn_vbox = QVBoxLayout()
        authors_btn_vbox.addWidget(authors_button_add)
        authors_btn_vbox.addWidget(authors_button_edit)
        authors_btn_vbox.addWidget(authors_button_del)

        # citations
        cites_label = QLabel("Citations<sup>*</sup>:")
        self.cites_listview = QListWidget()
        self.cites_listview.setFixedHeight(70)
        cites_button_add = QPushButton("Add")
        cites_button_add.clicked.connect(self.new_cite)
        cites_button_edit = QPushButton("Edit")
        cites_button_edit.clicked.connect(self.edit_cite)
        cites_button_del = QPushButton("Remove")
        cites_button_del.clicked.connect(self.del_cite)
        cites_btn_vbox = QVBoxLayout()
        cites_btn_vbox.addWidget(cites_button_add)
        cites_btn_vbox.addWidget(cites_button_edit)
        cites_btn_vbox.addWidget(cites_button_del)

        # inputs
        inputs_label = QLabel("Inputs<sup>*</sup>:")
        self.inputs_listview = QListWidget()
        self.inputs_listview.setFixedHeight(70)
        inputs_button_add = QPushButton("Add")
        inputs_button_add.clicked.connect(self.new_model_input)
        inputs_button_edit = QPushButton("Edit")
        inputs_button_edit.clicked.connect(self.edit_model_input)
        inputs_button_del = QPushButton("Remove")
        inputs_button_del.clicked.connect(self.del_input)
        inputs_btn_vbox = QVBoxLayout()
        inputs_btn_vbox.addWidget(inputs_button_add)
        inputs_btn_vbox.addWidget(inputs_button_edit)
        inputs_btn_vbox.addWidget(inputs_button_del)

        # outputs
        outputs_label = QLabel("Outputs<sup>*</sup>:")
        self.outputs_listview = QListWidget()
        self.outputs_listview.setFixedHeight(70)
        outputs_button_add = QPushButton("Add")
        outputs_button_add.clicked.connect(self.new_model_output)
        outputs_button_edit = QPushButton("Edit")
        outputs_button_edit.clicked.connect(self.edit_model_output)
        outputs_button_del = QPushButton("Remove")
        outputs_button_del.clicked.connect(self.del_output)
        outputs_btn_vbox = QVBoxLayout()
        outputs_btn_vbox.addWidget(outputs_button_add)
        outputs_btn_vbox.addWidget(outputs_button_edit)
        outputs_btn_vbox.addWidget(outputs_button_del)

        # add widgets to the layout
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
        # put the rest into tabs
        tabs = QTabWidget()
        # authors
        page = QWidget()
        page_grid = QGridLayout()
        page.setLayout(page_grid)
        page_grid.addWidget(authors_label, 0, 0)
        page_grid.addWidget(self.authors_listview, 0, 1)
        page_grid.addLayout(authors_btn_vbox, 0, 2)
        tabs.addTab(page, "Authors")
        # cites
        page = QWidget()
        page_grid = QGridLayout()
        page.setLayout(page_grid)
        page_grid.addWidget(cites_label, 0, 0)
        page_grid.addWidget(self.cites_listview, 0, 1)
        page_grid.addLayout(cites_btn_vbox, 0, 2)
        tabs.addTab(page, "Citations")
        # weights
        page = QWidget()
        page_grid = QGridLayout()
        page.setLayout(page_grid)
        page_grid.addWidget(weights_type_label, 0, 0)
        page_grid.addWidget(self.weights_combo, 0, 1)
        page_grid.addWidget(weights_label, 1, 0)
        page_grid.addWidget(self.weights_textbox, 1, 1)
        page_grid.addWidget(weights_button, 1, 2)
        page_grid.addWidget(self.model_src_label, 2, 0)
        page_grid.addWidget(self.model_source_textbox, 2, 1)
        page_grid.addWidget(self.model_src_sha256_label, 3, 0)
        page_grid.addWidget(self.model_source_sha256_textbox, 3, 1)
        tabs.addTab(page, "Weights")
        # inputs
        page = QWidget()
        page_grid = QGridLayout()
        page.setLayout(page_grid)
        page_grid.addWidget(inputs_label, 0, 0)
        page_grid.addWidget(self.inputs_listview, 0, 1)
        page_grid.addLayout(inputs_btn_vbox, 0, 2)
        tabs.addTab(page, "Inputs")
        # outputs
        page = QWidget()
        page_grid = QGridLayout()
        page.setLayout(page_grid)
        page_grid.addWidget(outputs_label, 0, 0)
        page_grid.addWidget(self.outputs_listview, 0, 1)
        page_grid.addLayout(outputs_btn_vbox, 0, 2)
        tabs.addTab(page, "Outputs")

        required_layout.addWidget(tabs, 4, 0, 1, 3)
        # required_layout.setRowStretch(-1, 1)  # BUG: causes segmentation fault crash!!
        #
        frame = QFrame()
        frame.setFrameStyle(QFrame.NoFrame)
        frame.setLayout(required_layout)

        return frame

    def create_other_spec_ui(self) -> QWidget:
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
            lambda: remove_from_listview(
                self,
                self.covers_listview,
                "Are you sure you want to remove the selected cover?",
            )
        )
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
        grid.addWidget(
            self.tags_widget, 1, 0, 1, 3, alignment=Qt.AlignTop | Qt.AlignLeft
        )

        frame = QFrame()
        frame.setFrameStyle(QFrame.NoFrame)
        frame.setLayout(grid)

        return frame

    def check_weight_format(self) -> None:
        """Disable model source code/sha256 input boxes.

        if the weight format is 'pytorch_state_dict'.
        """
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

    def new_author(self) -> None:
        """Show author's form to add a new author."""
        author_win = AuthorWidget()
        author_win.setWindowModality(Qt.ApplicationModal)
        author_win.submit.connect(self.add_author)
        author_win.show()

    def edit_author(self) -> None:
        """Show author's form to modify an existing author."""
        selected_index = self.authors_listview.currentRow()
        if selected_index > -1:
            author_data = self.authors[selected_index]
            author_win = AuthorWidget(author_data=author_data)
            author_win.setWindowModality(Qt.ApplicationModal)
            author_win.submit.connect(
                lambda author_data: self.update_author(selected_index, author_data)
            )
            author_win.show()

    def del_author(self) -> None:
        """Remove the selected author."""
        selected_index = self.authors_listview.currentRow()
        if selected_index > -1:
            reply, del_row = remove_from_listview(
                self,
                self.authors_listview,
                "Are you sure you want to remove the selected author?",
            )
            if reply:
                del self.authors[del_row]
                self.populate_authors_list()

    def populate_authors_list(self) -> None:
        """Populates the authors' listview widget with the list of authors."""
        self.authors_listview.clear()
        self.authors_listview.addItems(author["name"] for author in self.authors)

    def add_author(self, author_data: dict) -> None:
        """Add a new author to the list."""
        self.authors.append(author_data)
        self.populate_authors_list()

    def update_author(self, index: int, author_data: dict) -> None:
        """Update the author at the given index with the given data."""
        self.authors[index] = author_data
        self.populate_authors_list()

    def add_cover_images(self) -> None:
        """Select cover images by a file dialog, and add them to the listview."""
        selected_files, _ = QFileDialog.getOpenFileNames(
            self, "Select Cover Image(s)", ".", "Images(*.png *.jpg *.gif)"
        )
        for file in selected_files:
            self.covers_listview.addItem(file)

    def add_cover_from_uri(self) -> None:
        """Shows a simple form to get a URI string."""

        def _get_uri(uri: str) -> None:
            if len(uri) > 0:
                self.covers_listview.addItem(uri)

        input_win = SingleInputWidget(label="Cover Image URI:", title="Cover Image")
        input_win.setWindowModality(Qt.ApplicationModal)
        input_win.submit.connect(_get_uri)
        input_win.show()

    def select_add_npy_to_listview(self, list_widget: QListWidget) -> None:
        """Select a numpy file as a test input/outpu and add it to the listview."""
        selected_file = select_file("Numpy File (*.npy)", parent=self)
        list_widget.addItem(selected_file)

    def new_model_input(self) -> None:
        """Shows the input form to add a new model's input."""
        input_win = InputTensorWidget(
            input_names=[item["name"] for item in self.input_tensors]
        )
        input_win.setWindowModality(Qt.ApplicationModal)
        input_win.submit.connect(self.add_model_input)
        input_win.show()

    def edit_model_input(self) -> None:
        """Shows the input's form to modify selected model's input."""
        selected_index = self.inputs_listview.currentRow()
        if selected_index > -1:
            input_data = {
                "test_input": self.test_inputs[selected_index],
                "input_tensor": self.input_tensors[selected_index],
            }
            input_win = InputTensorWidget(
                input_names=[  # pass all other names except selected one
                    item["name"]
                    for item in self.input_tensors
                    if item["name"] != self.input_tensors[selected_index]["name"]
                ],
                input_data=input_data,
            )
            input_win.setWindowModality(Qt.ApplicationModal)
            input_win.submit.connect(
                lambda input_data: self.update_model_input(selected_index, input_data)
            )
            input_win.show()

    def populate_inputs_list(self) -> None:
        """Populates the inputs' listview widget with the list of model's inputs."""
        self.inputs_listview.clear()
        self.inputs_listview.addItems(
            f"{in_tensor['name']} ({in_test})"
            for in_tensor, in_test in zip(self.input_tensors, self.test_inputs)
        )

    def add_model_input(self, model_input: dict) -> None:
        """Add model's input to the list."""
        # model_input keys: 'test_input', 'input_tensor'
        self.input_tensors.append(model_input["input_tensor"])
        self.test_inputs.append(model_input["test_input"])
        self.populate_inputs_list()

    def update_model_input(self, index: int, input_data: dict) -> None:
        """Update model's input at given index with given data."""
        self.test_inputs[index] = input_data["test_input"]
        self.input_tensors[index] = input_data["input_tensor"]
        self.populate_inputs_list()

    def del_input(self) -> None:
        """Remove the selected input."""
        selected_index = self.inputs_listview.currentRow()
        if selected_index > -1:
            reply, del_row = remove_from_listview(
                self,
                self.inputs_listview,
                "Are you sure you want to remove the selected input?",
            )
            if reply:
                del self.input_tensors[del_row]
                del self.test_inputs[del_row]
                self.populate_inputs_list()

    def new_model_output(self) -> None:
        """Shows the output form to add a new model's output."""
        output_win = OutputTensorWidget(
            output_names=[item["name"] for item in self.output_tensors]
        )
        output_win.setWindowModality(Qt.ApplicationModal)
        output_win.submit.connect(self.add_model_output)
        output_win.show()

    def edit_model_output(self) -> None:
        """Shows the output's form to modify selected model's output."""
        selected_index = self.outputs_listview.currentRow()
        if selected_index > -1:
            output_data = {
                "test_output": self.test_outputs[selected_index],
                "output_tensor": self.output_tensors[selected_index],
            }
            output_win = OutputTensorWidget(
                output_names=[  # pass all other names except selected one
                    item["name"]
                    for item in self.output_tensors
                    if item["name"] != self.output_tensors[selected_index]["name"]
                ],
                output_data=output_data,
            )
            output_win.setWindowModality(Qt.ApplicationModal)
            output_win.submit.connect(
                lambda output_data: self.update_model_output(
                    selected_index, output_data
                )
            )
            output_win.show()

    def populate_outputs_list(self) -> None:
        """Populates the outputs' listview widget with the list of model's outputs."""
        self.outputs_listview.clear()
        self.outputs_listview.addItems(
            f"{out_tensor['name']} ({out_test})"
            for out_tensor, out_test in zip(self.output_tensors, self.test_outputs)
        )

    def add_model_output(self, model_output: dict) -> None:
        """Add a new model's output to the list."""
        # model_output keys: 'test_output', 'output_tensor'
        self.output_tensors.append(model_output["output_tensor"])
        self.test_outputs.append(model_output["test_output"])
        self.populate_outputs_list()

    def update_model_output(self, index: int, output_data: dict) -> None:
        """Update model's output at given index with given data."""
        self.test_outputs[index] = output_data["test_output"]
        self.output_tensors[index] = output_data["output_tensor"]
        self.populate_outputs_list()

    def del_output(self) -> None:
        """Remove the selected output."""
        selected_index = self.outputs_listview.currentRow()
        if selected_index > -1:
            reply, del_row = remove_from_listview(
                self,
                self.outputs_listview,
                "Are you sure you want to remove the selected output?",
            )
            if reply:
                del self.output_tensors[del_row]
                del self.test_outputs[del_row]
                self.populate_outputs_list()

    def new_cite(self) -> None:
        """Show cite form to add a new citation."""
        win = CiteWidget()
        win.setWindowModality(Qt.ApplicationModal)
        win.submit.connect(self.add_cite)
        win.show()

    def edit_cite(self) -> None:
        """Show citations' form to modify an existing citation."""
        selected_index = self.cites_listview.currentRow()
        if selected_index > -1:
            cite_data = self.cites[selected_index]
            win = CiteWidget(cite_data=cite_data)
            win.setWindowModality(Qt.ApplicationModal)
            win.submit.connect(
                lambda cite_data: self.update_cite(selected_index, cite_data)
            )
            win.show()

    def del_cite(self) -> None:
        """Remove the selected citation."""
        selected_index = self.cites_listview.currentRow()
        if selected_index > -1:
            reply, del_row = remove_from_listview(
                self,
                self.cites_listview,
                "Are you sure you want to remove the selected citation?",
            )
            if reply:
                del self.cites[del_row]
                self.populate_cites_list()

    def populate_cites_list(self) -> None:
        """Populates the citations' listview widget with the list of citations."""
        self.cites_listview.clear()
        self.cites_listview.addItems(cite["text"] for cite in self.cites)

    def add_cite(self, cite_data: dict) -> None:
        """Add a new citation to the list."""
        self.cites.append(cite_data)
        self.populate_cites_list()

    def update_cite(self, index: int, cite_data: dict) -> None:
        """Update the citation at the given index with the given data."""
        self.cites[index] = cite_data
        self.populate_cites_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
