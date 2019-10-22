import unittest

import mock
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDockWidget, QMainWindow

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class StackVisualiserViewTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StackVisualiserViewTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images_class_random_shared_array()

    def setUp(self):
        # mock the view so it has the same methods
        self.window = QMainWindow()
        self.window.remove_stack = mock.Mock()

        self.dock = QDockWidget()
        self.dock.setWindowTitle("Potatoes")

        self.view = StackVisualiserView(self.window, self.dock, self.test_data)
        self.dock.setWidget(self.view)
        self.window.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dock)

    def test_name(self):
        title = "Potatoes"
        self.dock.setWindowTitle(title)
        self.assertEqual(title, self.view.name)

    def test_show_current_image(self):
        self.view.image_view = mock.Mock()
        self.view.show_current_image()

        self.view.image_view.setImage.assert_called_once_with(self.test_data.sample)

    def test_closeEvent_deletes_images(self):
        self.dock.setFloating = mock.Mock()
        self.dock.deleteLater = mock.Mock()

        self.view.close()

        self.dock.setFloating.assert_called_once_with(False)
        self.dock.deleteLater.assert_called_once_with()
        self.assertEqual(None, self.view.presenter.images)
        self.window.remove_stack.assert_called_once_with(self.view)

    def _roi_updated_callback(self, roi):
        self.assertIsInstance(roi, SensibleROI)

        self.assertEqual(roi.left, 1)
        self.assertEqual(roi.top, 2)
        self.assertEqual(roi.right, 3)
        self.assertEqual(roi.bottom, 4)

        self.roi_callback_was_called = True

    def test_roi_changed_callback(self):
        self.roi_callback_was_called = False
        self.view.roi_updated.connect(self._roi_updated_callback)

        self.view.roi_changed_callback(SensibleROI(1, 2, 3, 4))

        self.assertTrue(self.roi_callback_was_called)


if __name__ == '__main__':
    unittest.main()