from functools import partial
from logging import getLogger
from typing import Callable, TYPE_CHECKING, List, Any, Dict

from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.filters.loader import load_filter_packages
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import get_parameters_from_stack
from mantidimaging.gui.windows.stack_visualiser import SVNotification

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401
    from mantidimaging.gui.windows.filters import FiltersWindowPresenter


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val, )


class FiltersWindowModel(object):
    filters: List[BaseFilter]
    selected_filter: BaseFilter
    filter_widget_kwargs: Dict[str, Any]

    def __init__(self, presenter: 'FiltersWindowPresenter'):
        super(FiltersWindowModel, self).__init__()

        self.presenter = presenter
        # Update the local filter registry
        self.filters = load_filter_packages(ignored_packages=['mantidimaging.core.filters.wip'])

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack = None
        self.selected_filter = self.filters[0]
        self.filter_widget_kwargs = {}

    @property
    def filter_names(self):
        return [f.filter_name for f in self.filters]

    def filter_registration_func(
            self, filter_idx: int) -> Callable[['QFormLayout', Callable, BaseMainWindowView], Dict[str, Any]]:
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_idx: Index of the filter in the registry
        """
        return self.filters[filter_idx].register_gui

    @property
    def stack_presenter(self):
        return self.stack.presenter if self.stack else None

    @property
    def num_images_in_stack(self):
        num_images = self.stack_presenter.images.sample.shape[0] if self.stack_presenter is not None else 0
        return num_images

    @property
    def params_needed_from_stack(self):
        return self.selected_filter.sv_params()

    def setup_filter(self, filter_idx, filter_widget_kwargs):
        self.selected_filter = self.filters[filter_idx]
        self.filter_widget_kwargs = filter_widget_kwargs

    def apply_filter(self, images: Images, stack_params: Dict[str, Any], progress=None):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)
        log.info(f"Filter kwargs: {stack_params}")

        input_kwarg_widgets = self.filter_widget_kwargs.copy()

        # Validate required kwargs are supplied so pre-processing does not happen unnecessarily
        if not self.selected_filter.validate_execute_kwargs(input_kwarg_widgets):
            raise ValueError("Not all required parameters specified")

        # Run filter
        exec_func: partial = self.selected_filter.execute_wrapper(**input_kwarg_widgets)
        exec_func.keywords["progress"] = progress
        exec_func(images, **stack_params)

        # store the executed filter in history if it all executed successfully
        exec_func.keywords.update(stack_params)
        images.record_operation(
            self.selected_filter.__name__,  # type: ignore
            self.selected_filter.filter_name,
            *exec_func.args,
            **exec_func.keywords)

    def do_apply_filter(self):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack_presenter:
            raise ValueError('No stack selected')

        # Get auto parameters
        stack_params = get_parameters_from_stack(self.stack_presenter, self.params_needed_from_stack)
        apply_func = partial(self.apply_filter, self.stack_presenter.images, stack_params)

        def post_filter(_):
            self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)
            self.presenter.do_update_previews()

        start_async_task_view(self.stack_presenter.view, apply_func, post_filter)
