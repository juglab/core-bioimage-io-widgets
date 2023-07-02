from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QWidget, QApplication,
    QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)


class SingleInputWidget(QWidget):
    """Simple form to get a single input."""

    submit = Signal(object, name="submit")

    def __init__(self, label: str = "", title: str = "", parent=None):
        super().__init__(parent)

        lbl = QLabel(label)
        self.input_textbox = QLineEdit()
        self.input_textbox.setMinimumWidth(420)
        submit_button = QPushButton("&Submit")
        submit_button.clicked.connect(self.submit_input)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(lambda: self.close())

        hbox = QHBoxLayout()
        hbox.addWidget(cancel_button)
        hbox.addWidget(submit_button)

        grid = QGridLayout()
        grid.addWidget(lbl, 0, 0)
        grid.addWidget(self.input_textbox, 0, 1)
        grid.addLayout(hbox, 1, 1, Qt.AlignRight)

        self.setLayout(grid)
        self.setWindowTitle(title)

    def submit_input(self):
        """Emit the submit event with the input text as data."""
        text_input = self.input_textbox.text().strip()
        if len(text_input) > 0:
            self.submit.emit(text_input)
            self.close()




if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = SingleInputWidget(label="Cover Image URI:", title="Cover Image")
    win.show()
    sys.exit(app.exec_())
