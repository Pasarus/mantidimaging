from functools import partial
from typing import List, Any, Dict, Callable, Iterable

import numpy as np

from mantidimaging.core.filters.loader import load_filter_packages
from . import const


class ImageOperation:
    """
    A deserialized representation of an item in a stacks operation_history
    """

    def __init__(self, filter_name, filter_args, filter_kwargs, display_name=None):
        self.filter_class_name: str = filter_name
        self.filter_args: List[Any] = filter_args
        self.filter_kwargs: Dict[str, Any] = filter_kwargs
        self.display_name: str = display_name

    def to_partial(self, filter_funcs: Dict[str, Callable]) -> partial:
        fn = filter_funcs[self.filter_class_name]
        return partial(fn, **self.filter_kwargs)

    @staticmethod
    def deserialize(metadata_entry: Dict[str, Any]) -> 'ImageOperation':
        return ImageOperation(
            filter_name=metadata_entry[const.OPERATION_NAME],
            filter_args=metadata_entry[const.OPERATION_ARGS],
            filter_kwargs=metadata_entry[const.OPERATION_KEYWORD_ARGS],
            display_name=metadata_entry.get(const.OPERATION_DISPLAY_NAME))

    def serialize(self) -> Dict[str, Any]:
        return {
            const.OPERATION_NAME: self.filter_class_name,
            const.OPERATION_ARGS: self.filter_args,
            const.OPERATION_KEYWORD_ARGS: self.filter_kwargs,
            const.OPERATION_DISPLAY_NAME: self.display_name,
        }

    def __str__(self):
        return f"{self.display_name if self.display_name else self.filter_class_name}, " \
               f"args: {self.filter_args}, " \
               f"kwargs: {self.filter_kwargs}"

    @property
    def friendly_name(self):
        return self.display_name if self.display_name else self.filter_class_name


def deserialize_metadata(metadata: Dict[str, Any]) -> List[ImageOperation]:
    return [ImageOperation.deserialize(entry) for entry in metadata[const.OPERATION_HISTORY]] \
        if const.OPERATION_HISTORY in metadata else []


def ops_to_partials(filter_ops: Iterable[ImageOperation]) -> Iterable[partial]:
    filter_funcs = {
        f.__name__: f._filter_func  # type: ignore
        for f in load_filter_packages(ignored_packages=['mantidimaging.core.filters.wip'])
    }
    # TODO: Reconstruction function. Requires reworking cor/proj_angle arguments a little
    funcs = {
        const.OPERATION_NAME_AXES_SWAP: lambda img: np.swapaxes(img, 0, 1),
    }
    funcs.update(filter_funcs)
    return (op.to_partial(funcs) for op in filter_ops)