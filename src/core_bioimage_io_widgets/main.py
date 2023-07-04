import sys

from qtpy.QtWidgets import QApplication

from core_bioimage_io_widgets.widgets import BioImageModelWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BioImageModelWidget()
    win.show()
    sys.exit(app.exec_())
