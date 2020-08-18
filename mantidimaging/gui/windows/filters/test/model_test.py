import unittest
from functools import partial

import mock
import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operation_history import const
from mantidimaging.gui.windows.filters import FiltersWindowModel
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter, SVParameters)


class FiltersWindowModelTest(unittest.TestCase):
    APPLY_BEFORE_AFTER_MAGIC_NUMBER = 42
    ROI_PARAMETER = (4, 3, 2, 1)

    def __init__(self, *args, **kwargs):
        super(FiltersWindowModelTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images()

    def setUp(self):
        self.sv_view = mock.create_autospec(StackVisualiserView)
        self.sv_view.current_roi = self.ROI_PARAMETER

        self.sv_presenter = StackVisualiserPresenter(self.sv_view, self.test_data)
        self.sv_view.presenter = self.sv_presenter

        self.model = FiltersWindowModel(mock.MagicMock())

    def execute_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4
        return data

    def execute_mock_with_roi(self, data, roi):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4
        self.assertEqual(roi, self.ROI_PARAMETER)
        return data

    def apply_before_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        self.apply_before_mock_variable = \
            self.APPLY_BEFORE_AFTER_MAGIC_NUMBER
        return self.apply_before_mock_variable

    def apply_after_mock(self, data, result_from_before):
        self.assertTrue(isinstance(data, np.ndarray))
        self.assertEqual(result_from_before, self.APPLY_BEFORE_AFTER_MAGIC_NUMBER)

    def setup_mocks(self, execute_mock, do_before_mock=None, do_after_mock=None):
        f = self.model.selected_filter
        orig_exec, orig_validate, orig_before, orig_after = \
            f.execute_wrapper, f.validate_execute_kwargs, f.do_before_wrapper, f.do_after_wrapper
        self.model.setup_filter(0, {})
        f.execute_wrapper = lambda: execute_mock
        f.validate_execute_kwargs = lambda _: True

        return orig_exec, orig_validate, orig_before, orig_after

    def reset_filter_model(self, exec, validate, before, after):
        f = self.model.selected_filter
        f.execute_wrapper = exec
        f.validate_execute_kwargs = validate
        f.do_before_wrapper = before
        f.do_after_wrapper = after

    @staticmethod
    def run_without_gui(task, on_complete):
        task()
        on_complete(None)

    def test_filters_populated(self):
        self.assertTrue(len(self.model.filter_names) > 0)

    @mock.patch("mantidimaging.gui.windows.filters.model.start_async_task_view")
    def test_do_apply_filter(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock))
        originals = self.setup_mocks(execute)
        self.model.do_apply_filter(self.sv_view, self.sv_presenter, callback)
        self.reset_filter_model(*originals)

        execute.assert_called_once()
        callback_mock.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.filters.model.start_async_task_view")
    def test_do_apply_filter_with_roi(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock_with_roi))
        originals = self.setup_mocks(execute)
        self.model.selected_filter.params = lambda: {'roi': SVParameters.ROI}
        self.model.do_apply_filter(self.sv_view, self.sv_presenter, callback)
        self.reset_filter_model(*originals)

        execute.assert_called_once()
        callback_mock.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.filters.model.start_async_task_view")
    def test_operation_recorded_in_image_history(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)
        self.sv_presenter.images.metadata = {}

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock))
        execute.args = ["arg"]
        execute.keywords = {"kwarg": "kwarg"}
        originals = self.setup_mocks(execute)

        self.model.do_apply_filter(self.sv_view, self.sv_presenter, callback)
        self.reset_filter_model(*originals)

        op_history = self.sv_presenter.images.metadata['operation_history']
        self.assertEqual(len(op_history), 1, "One operation should have been recorded")
        self.assertEqual(op_history[0][const.OPERATION_ARGS], ['arg'])
        self.assertEqual(op_history[0][const.OPERATION_KEYWORD_ARGS], {"kwarg": "kwarg"})
        # Recorded operation should not be a qualified module name.
        self.assertNotIn(".", op_history[0][const.OPERATION_NAME])
        callback_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
