from functools import partial
from typing import List, Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class TagsInputWidget(QWidget):
    """A widget for displaying/adding tags."""

    def __init__(
        self,
        predefined_tags: Optional[list] = None,
        label: str = "Tags",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self._tags: List[str] = []

        lbl = QLabel(label + ":")
        self.input_textbox = QLineEdit()
        self.input_textbox.returnPressed.connect(self.add_tag)
        self.input_textbox.setFixedWidth(150)
        self.input_textbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        if predefined_tags is None:
            predefined_tags = []
        completer = QCompleter(predefined_tags)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input_textbox.setCompleter(completer)
        self.tags_layout = QHBoxLayout()
        self.tags_layout.setSpacing(2)

        grid = QGridLayout()
        grid.addWidget(lbl, 0, 0)
        grid.addLayout(self.tags_layout, 0, 1, alignment=Qt.AlignLeft)
        grid.addWidget(self.input_textbox, 1, 1, alignment=Qt.AlignTop | Qt.AlignLeft)
        grid.setRowStretch(-1, 1)

        self.setLayout(grid)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    @property
    def tags(self) -> List[str]:
        """Return a list of tags."""
        return self._tags

    @tags.setter
    def tags(self, tags: List[str]) -> None:
        """Set tags and refresh the ui."""
        self._tags = tags
        self.refresh_tags()

    def add_tag(self) -> None:
        """Add a new tag to the tags list."""
        _tag = self.input_textbox.text().lower().strip()
        if len(_tag) > 0 and _tag not in self.tags:
            self.tags.append(_tag)
            self.refresh_tags()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the tags list."""
        self.tags.remove(tag)
        self.refresh_tags()

    def refresh_tags(self) -> None:
        """Re-create tags ui."""
        # clear all
        for i in reversed(range(self.tags_layout.count())):
            self.tags_layout.itemAt(i).widget().deleteLater()
        # re-create
        for tag in self.tags:
            tag_ui = self._create_tag_ui(tag)
            self.tags_layout.addWidget(tag_ui, alignment=Qt.AlignLeft)

        self.input_textbox.setText("")
        # print(self.tags_layout.sizeHint().width())

    def _create_tag_ui(self, tag: str) -> QFrame:
        tag_label = QLabel(tag)
        tag_label.setStyleSheet("border:0px")
        x_button = QPushButton("X")
        x_button.setFixedSize(20, 20)
        x_button.setStyleSheet(
            "border:0px; font-weight:bold; color: rgb(192, 192, 232)"
        )
        x_button.clicked.connect(partial(self.remove_tag, tag))
        layout = QHBoxLayout()
        # layout.setSpacing(3)
        layout.addWidget(tag_label)
        layout.addWidget(x_button)
        frame = QFrame()
        frame.setStyleSheet("border:1px solid rgb(192, 192, 232); border-radius: 4px;")
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setFixedHeight(40)
        frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        frame.setLayout(layout)

        return frame


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = TagsInputWidget(predefined_tags=["Mehdi", "Joran", "Florian", "John"])
    win.show()
    sys.exit(app.exec_())
