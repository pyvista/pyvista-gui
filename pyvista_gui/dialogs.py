"""Widgets and associated tooltips"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QBoxLayout, QCheckBox, QColorDialog,
                             QDialog, QFileDialog, QFormLayout,
                             QFrame, QGroupBox, QLabel, QSlider,
                             QVBoxLayout, QHBoxLayout, QDoubleSpinBox)

LOG = logging.getLogger(__name__)
LOG.setLevel('DEBUG')


class ColorDialog(QColorDialog):
    """
    Color dialog query that emits a signal when a color is selected
    the dialog was property closed.
    """
    color_picked = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super(ColorDialog, self).__init__(parent=parent)
        self.setOption(QColorDialog.DontUseNativeDialog)
        self.colorSelected.connect(self.trigger_accepted)

    def trigger_accepted(self, color):
        """
        Sends signal that the fem file dialog was closed properly.

        Sends:
        fem_filename, has_thickness, is_rotor
        """
        rgb = (color.red()/255.0, color.green()/255.0, color.blue()/255.0)
        self.color_picked.emit(rgb)


class FileDialog(QFileDialog):
    """Generic file query that emits a signal when a file is selected
    and the dialog was property closed.

    Examples
    --------

    >>> dlg = FileDialog(filefilter=["Text files (*.txt)", "Images (*.png *.jpg)"])
    """
    dlg_accepted = pyqtSignal(str)

    def __init__(self, parent=None, filefilter=None, save_mode=False,
                 show=True, callback=None, directory=False):
        super(FileDialog, self).__init__(parent)

        if filefilter is not None:
            self.setNameFilters(filefilter)
        self.setOption(QFileDialog.DontUseNativeDialog)
        self.accepted.connect(self.emit_accepted)
        if show:
            self.show()

        if directory:
            self.FileMode(QFileDialog.DirectoryOnly)
            self.setOption(QFileDialog.ShowDirsOnly, True)

        if save_mode:
            self.setAcceptMode(QFileDialog.AcceptSave)

        if callback is not None:
            self.dlg_accepted.connect(callback)

    def emit_accepted(self):
        """
        Sends signal that the file dialog was closed properly.

        Sends:
        filename
        """
        if self.result():
            self.dlg_accepted.emit(self.selectedFiles()[0])


class ColorBox(QFrame):

    colorChanged = pyqtSignal(tuple)

    def __init__(self, parent=None, rgb=[1, 1, 1]):
        super(ColorBox, self).__init__(parent)

        self.bgColor = Qt.white
        self.setStyleSheet("margin:5px; border:1px; ")

        self.set_background(self.upscale_rgb(rgb))

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            col = QColorDialog.getColor(self.bgColor, self)
            if col.isValid():
                rgb = (col.red(), col.green(), col.blue())
                self.set_background(rgb)
                self.bgColor = col
                self.colorChanged.emit(self.downscale_rgb(rgb))

    def upscale_rgb(self, rgb):
        return (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

    def downscale_rgb(self, rgb):
        return (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

    def set_background(self, rgb):
        self.setStyleSheet("QWidget { background-color: rgb(%d,%d,%d); border:1px solid rgb(0, 0, 0); }" % rgb)


class LoadMeshDialog(QDialog):
    """ Custom file dialog to open up PyVista-supported files """
    accepted = pyqtSignal(str, bool)

    def __init__(self, parent=None, show=True, callback=None):
        super().__init__(parent)
        main_dialog = QDialog()
        main_dialog.setWindowTitle('Select CFD File')
        layout = QVBoxLayout(main_dialog)

        self.file_dialog = QFileDialog(main_dialog, Qt.Widget)
        # self.file_dialog.setNameFilters(FILE_FILTER)
        self.file_dialog.setWindowFlags(self.file_dialog.windowFlags() & ~Qt.Dialog)
        self.file_dialog.setOption(QFileDialog.DontUseNativeDialog)

        # close all when main closes
        self.file_dialog.finished.connect(self.close)
        layout.addWidget(self.file_dialog)

        form_layout = QFormLayout(self)
        settings_groupbox = QGroupBox('Settings')

        self.isrotor_checkbox = QCheckBox(self)
        self.isrotor_checkbox.setChecked(False)
        self.isrotor_checkbox.setToolTip('CFD grids are a sector of a rotor')
        form_layout.addRow('Sector', self.isrotor_checkbox)

        settings_groupbox.setLayout(form_layout)
        layout.addWidget(settings_groupbox)
        self.setLayout(layout)
        self.file_dialog.finished.connect(self.emit_accepted)

        if show:
            self.show()

        if callback is not None:
            self.accepted.connect(callback)

    @property
    def is_rotor(self):
        return self.isrotor_checkbox.isChecked()

    def emit_accepted(self, result):
        """Sends signal that the fem file dialog was closed properly.

        Sends:
        cfd_filename, is_rotor
        """
        if result:
            self.accepted.emit(self.file_dialog.selectedFiles()[0],
                               self.is_rotor)


class SlidersGroup(QGroupBox):

    nocheckvalueChanged = pyqtSignal(int)
    fixedvalueChanged = pyqtSignal(int)

    def __init__(self, orientation, title, parent=None):
        super(SlidersGroup, self).__init__(title, parent)

        def MakeSlider(orientation):
            slider = QSlider(orientation)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(100)
            slider.setSingleStep(1)
            return slider

        # nocheck slider
        self.nocheck_slider = MakeSlider(orientation)
        self.nocheck_slider.valueChanged.connect(self.nocheckvalueChanged)

        self.fixed_slider = MakeSlider(orientation)
        self.fixed_slider.valueChanged.connect(self.fixedvalueChanged)

        slidersLayout = QBoxLayout(QBoxLayout.TopToBottom)
        slidersLayout.addWidget(self.nocheck_slider)
        slidersLayout.addWidget(self.fixed_slider)
        slidersLayout.addWidget(QLabel(''))
        self.setLayout(slidersLayout)

    def setEnabled(self, value):
        self.fixed_slider.setEnabled(value)
        self.nocheck_slider.setEnabled(value)

    def set_fixed_value(self, value):
        value = value*1000
        self.fixed_slider.setValue(value)
        if self.nocheck_slider.value() > value:
            self.nocheck_slider.setValue(value)

    def set_nocheck_value(self, value):
        value = value*1000
        self.nocheck_slider.setValue(value)
        if self.fixed_slider.value() < value:
            self.fixed_slider.setValue(value)

    def setMinimum(self, value):
        self.fixed_slider.setMinimum(value*1000)
        self.nocheck_slider.setMinimum(value*1000)

    def setMaximum(self, value):
        self.fixed_slider.setMaximum(value*1000)
        self.nocheck_slider.setMaximum(value*1000)




class DoubleSlider(QSlider):
    """Double precision slider.

    Reference:
    https://gist.github.com/dennis-tra/994a65d6165a328d4eabaadbaedac2cc

    """

    def __init__(self, *args, **kwargs):
        """Initialize the double slider."""
        super().__init__(*args, **kwargs)
        self.decimals = 5
        self._max_int = 10 ** self.decimals

        super().setMinimum(0)
        super().setMaximum(self._max_int)

        self._min_value = 0.0
        self._max_value = 20.0

    @property
    def _value_range(self):
        """Return the value range of the slider."""
        return self._max_value - self._min_value

    def value(self):
        """Return the value of the slider."""
        return float(super().value()) / self._max_int * self._value_range + self._min_value

    def setValue(self, value):
        """Set the value of the slider."""
        super().setValue(int((value - self._min_value) / self._value_range * self._max_int))

    def setMinimum(self, value):
        """Set the minimum value of the slider."""
        if value > self._max_value:  # pragma: no cover
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._min_value = value
        self.setValue(self.value())

    def setMaximum(self, value):
        """Set the maximum value of the slider."""
        if value < self._min_value:  # pragma: no cover
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._max_value = value
        self.setValue(self.value())


# this is redefined from above because the above object is a dummy object
# we use dummy objects to allow the module to import when PyQt5 isn't installed
class RangeGroup(QHBoxLayout):
    """Range group box widget."""

    def __init__(self, parent, callback, minimum=0.0, maximum=20.0,
                 value=1.0):
        """Initialize the range widget."""
        super(RangeGroup, self).__init__(parent)
        self.slider = DoubleSlider(QtCore.Qt.Horizontal)
        self.slider.setTickInterval(0.1)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setValue(value)

        self.minimum = minimum
        self.maximum = maximum

        self.spinbox = QDoubleSpinBox(value=value, minimum=minimum,
                                      maximum=maximum, decimals=4)

        self.addWidget(self.slider)
        self.addWidget(self.spinbox)

        # Connect slider to spinbox
        self.slider.valueChanged.connect(self.update_spinbox)
        self.spinbox.valueChanged.connect(self.update_value)
        self.spinbox.valueChanged.connect(callback)

    def update_spinbox(self, value):
        """Set the value of the internal spinbox."""
        self.spinbox.setValue(self.slider.value())

    def update_value(self, value):
        """Update the value of the internal slider."""
        # if self.spinbox.value() < self.minimum:
        #     self.spinbox.setValue(self.minimum)
        # elif self.spinbox.value() > self.maximum:
        #     self.spinbox.setValue(self.maximum)

        self.slider.blockSignals(True)
        self.slider.setValue(self.spinbox.value())
        self.slider.blockSignals(False)

    @property
    def value(self):
        """Return the value of the internal spinbox."""
        return self.spinbox.value()

    @value.setter
    def value(self, new_value):
        """Set the value of the internal slider."""
        self.slider.setValue(new_value)


class ScaleAxesDialog(QDialog):
    """Dialog to control axes scaling."""

    accepted = pyqtSignal(float)
    signal_close = pyqtSignal()

    def __init__(self, parent, plotter, show=True):
        """Initialize the scaling dialog."""
        super(ScaleAxesDialog, self).__init__(parent)
        self.setGeometry(300, 300, 50, 50)
        self.setMinimumWidth(500)
        self.signal_close.connect(self.close)
        self.plotter = plotter

        self.x_slider_group = RangeGroup(parent, self.update_scale,
                                         value=plotter.scale[0])
        self.y_slider_group = RangeGroup(parent, self.update_scale,
                                         value=plotter.scale[1])
        self.z_slider_group = RangeGroup(parent, self.update_scale,
                                         value=plotter.scale[2])

        form_layout = QFormLayout(self)
        form_layout.addRow('X Scale', self.x_slider_group)
        form_layout.addRow('Y Scale', self.y_slider_group)
        form_layout.addRow('Z Scale', self.z_slider_group)

        self.setLayout(form_layout)

        if show:  # pragma: no cover
            self.show()

    def update_scale(self, value):
        """Update the scale of all actors in the plotter."""
        self.plotter.set_scale(self.x_slider_group.value,
                               self.y_slider_group.value,
                               self.z_slider_group.value)
