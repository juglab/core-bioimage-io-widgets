from qtpy import QtCore, QtWidgets


class ValidationWidget(QtWidgets.QWidget):
    """A widget to show form validation errors."""

    def __init__(self,  parent=None):
        super().__init__(parent)

        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setLayout(self.content_layout)
        scroller = QtWidgets.QScrollArea(minimumHeight=20)  # maximumHeight=100
        scroller.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroller.setWidgetResizable(True)
        scroller.setWidget(scroll_widget)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(scroller)

        group = QtWidgets.QGroupBox(title="Validation Errors:")
        group.setLayout(vbox)

        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.setSpacing(0)
        vbox2.setContentsMargins(0, 0, 0, 0)
        vbox2.addWidget(group)

        self.setLayout(vbox2)

    def update_content(self, widget_list):
        """Clears the content area, and then adds new widgets to it."""
        self._clear_content_area()
        # add widgets
        for widget in widget_list:
            self.content_layout.addWidget(widget, alignment=QtCore.Qt.AlignLeft)
        self.update()

    def _clear_content_area(self):
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().deleteLater()
