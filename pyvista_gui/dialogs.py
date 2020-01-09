"""Widgets and associated tooltips"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QBoxLayout, QCheckBox, QColorDialog,
                             QDialog, QFileDialog, QFormLayout,
                             QFrame, QGroupBox, QLabel, QSlider,
                             QVBoxLayout)

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
