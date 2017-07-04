from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui as gcu
from isis_imaging.gui.algorithm_dialog import AlgorithmDialog

from . import clip_values

GUI_MENU_NAME = 'Clip Values'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_clip_min = Qt.QLabel("Clip Min")
    label_clip_max = Qt.QLabel("Clip Max")
    clip_min_field = Qt.QDoubleSpinBox()
    clip_min_field.setDecimals(7)
    clip_min_field.setMinimum(-1000000)
    clip_max_field = Qt.QDoubleSpinBox()
    clip_max_field.setDecimals(7)
    clip_max_field.setMaximum(1000000)

    dialog.formLayout.addRow(label_clip_min, clip_min_field)
    dialog.formLayout.addRow(label_clip_max, clip_max_field)

    def decorate_execute():
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        from functools import partial
        return partial(clip_values.execute, clip_min=clip_min, clip_max=clip_max)

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog
