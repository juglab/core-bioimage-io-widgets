import sys

from qtpy.QtWidgets import QApplication

from core_bioimage_io_widgets.widgets import BioImageModelWidget


def main() -> None:
    """Initialize the widget."""
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
