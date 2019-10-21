from typing import TYPE_CHECKING, Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QDockWidget, QVBoxLayout, QWidget, QMenu, QInputDialog

from mantidimaging.core.data import Images
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.external.pyqtgraph.imageview.ImageView import ImageView
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.stack_visualiser.presenter import StackVisualiserPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class StackVisualiserView(BaseMainWindowView):
    # Signal that signifies when the ROI is updated. Used to update previews in Filter views
    roi_updated = pyqtSignal(SensibleROI)

    image_view: ImageView
    presenter: StackVisualiserPresenter
    dock: QDockWidget
    layout: QVBoxLayout

    def __init__(self, parent: 'MainWindowView', dock: QDockWidget, images: Images):
        # enforce not showing a single image
        assert images.sample.ndim == 3, \
            "Data does NOT have 3 dimensions! Dimensions found: {0}".format(images.sample.ndim)

        # We set the main window as the parent, the effect is the same as
        # having no parent, the window will be inside the QDockWidget. If the
        # dock is set as a parent the window will be an independent floating
        # window
        super(StackVisualiserView, self).__init__(parent, None)
        self.central_widget = QWidget(self)
        self.layout = QVBoxLayout(self)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # capture the QDockWidget reference so that we can access the Qt widget
        # and change things like the title
        self.dock = dock
        # Swap out the dock close event with our own provided close event. This
        # is needed to manually delete the data reference, otherwise it is left
        # hanging in the presenter
        dock.closeEvent = self.closeEvent

        self.presenter = StackVisualiserPresenter(self, images)

        self.image_view = ImageView(self)
        self.image_view.imageItem.menu = self.build_context_menu()
        self.actionCloseStack = QAction("Close window", self)
        self.actionCloseStack.triggered.connect(self.close_view)
        self.actionCloseStack.setShortcut("Ctrl+W")
        self.dock.addAction(self.actionCloseStack)
        self.image_view.setImage(self.presenter.images.sample)
        self.image_view.roi_changed_callback = self.roi_changed_callback
        self.layout.addWidget(self.image_view)

    @property
    def name(self):
        return self.dock.windowTitle()

    @name.setter
    def name(self, name: str):
        self.dock.setWindowTitle(name)

    @property
    def current_roi(self) -> Tuple[int, int, int, int]:
        roi = SensibleROI.from_points(*self.image_view.get_roi())
        return roi.left, roi.top, roi.right, roi.bottom

    def show_current_image(self):
        self.image_view.setImage(self.presenter.images.sample)

    def closeEvent(self, event):
        # this removes all references to the data, allowing it to be GC'ed
        # otherwise there is a hanging reference
        self.presenter.delete_data()

        # setting floating to false makes window() to return the MainWindow
        # because the window will be docked in, however we delete it
        # immediately after so no visible change occurs
        self.dock.setFloating(False)

        # this could happen if run without a parent through see(..)
        if not isinstance(self.window(), QDockWidget):
            self.window().remove_stack(self)  # refers to MainWindow

        self.deleteLater()
        # refers to the QDockWidget within which the stack is contained
        self.dock.deleteLater()

    def roi_changed_callback(self, roi: SensibleROI):
        self.roi_updated.emit(roi)

    def close_view(self):
        self.close()

    def build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        action = QAction("Change window name", menu)
        action.triggered.connect(self.change_window_name_clicked)
        menu.addAction(action)
        return menu

    def change_window_name_clicked(self):
        input_window = QInputDialog()
        new_window_name, ok = input_window.getText(self,
                                                   "Change window name",
                                                   "Name:")
        if ok:
            self.name = new_window_name
