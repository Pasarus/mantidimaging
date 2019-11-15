import os
import uuid
from collections import namedtuple
from logging import getLogger
from typing import Dict, List, Any, Optional

from mantidimaging.core.io import loader, saver
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

StackId = namedtuple('StackId', ['id', 'name'])


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.active_stacks: Dict[uuid.UUID, StackVisualiserView] = {}

    def do_load_stack(self, sample_path, image_format, parallel_load, indices,
                      progress, in_prefix, flat_path=None, dark_path=None):
        images = loader.load(
            sample_path,
            flat_path,
            dark_path,
            in_prefix=in_prefix,
            in_format=image_format,
            parallel_load=parallel_load,
            indices=indices,
            progress=progress)

        return images

    def do_saving(self, stack_uuid, output_dir, name_prefix, image_format,
                  overwrite, swap_axes, indices, progress):
        svp = self.get_stack_visualiser(stack_uuid).presenter
        saver.save(
            data=svp.images,
            output_dir=output_dir,
            name_prefix=name_prefix,
            swap_axes=swap_axes,
            overwrite_all=overwrite,
            out_format=image_format,
            indices=indices,
            progress=progress)

        return True

    def create_name(self, filename):
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        current_names = self.stack_names
        num = 1
        while name in current_names:
            num += 1
            name = filename + '_{}'.format(num)

        return name

    @property
    def stack_list(self) -> List[StackId]:
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def stack_names(self):
        return [stack.name for stack in self.stack_list]

    def add_stack(self, stack_visualiser, dock_widget):
        # generate unique ID for this stack
        stack_visualiser.uuid = uuid.uuid1()
        self.active_stacks[stack_visualiser.uuid] = dock_widget
        getLogger(__name__).debug(
            "Active stacks {}".format(self.active_stacks))

    def get_stack(self, stack_uuid: uuid.UUID):
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The QDockWidget that contains the Stack Visualiser.
                For direct access to the Stack Visualiser widget use
                get_stack_visualiser
        """
        return self.active_stacks[stack_uuid]

    def get_stack_by_name(self, search_name: str):
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.get_stack(stack_id.id)
        return None

    def get_stack_visualiser(self, stack_uuid: uuid.UUID) -> StackVisualiserView:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The Stack Visualiser widget that contains the data.
        """
        return self.active_stacks[stack_uuid].widget()

    def get_stack_history(self, stack_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        return self.get_stack_visualiser(stack_uuid).presenter.images.metadata

    def do_remove_stack(self, stack_uuid) -> None:
        """
        Removes the stack from the active_stacks dictionary.

        :param stack_uuid: The unique ID of the stack that will be removed.
        """
        del self.active_stacks[stack_uuid]

    @property
    def have_active_stacks(self):
        return len(self.active_stacks) > 0
