""" This is the main GUI """

import datetime
import logging
import os

import qdarkstyle
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QDockWidget, QHBoxLayout,
                             QMainWindow, QMenu, QMessageBox, QProgressDialog,
                             QSizePolicy, QSplitter, QVBoxLayout, QMenuBar)

from pyvista.plotting import Plotter, QtInteractor
import pyvista

from pyvista_gui.console import QIPythonWidget
from pyvista_gui.data import Data
from pyvista_gui.dialogs import ColorDialog, LoadMeshDialog, FileDialog, ScaleAxesDialog
from pyvista_gui.options import rcParams
from pyvista_gui.widgets import QTextEditCommands, QTextEditLogger, TreeWidget

from pyvista_gui import assets

# from weakref import proxy
# from functools import wraps


logging.getLogger('ipykernel').setLevel('CRITICAL')
logging.getLogger('traitlets').setLevel('CRITICAL')
logging.getLogger('root').setLevel('CRITICAL')
logging.getLogger('parso').setLevel('CRITICAL')
logging.getLogger('parso.cache').setLevel('CRITICAL')

LOG = logging.getLogger(__name__)
LOG.setLevel('DEBUG')


NOW = datetime.datetime.now()
ABOUT_TEXT = """PyVista Graphical User Interface
Copyright %d

Written by the PyVista Developers
info@pyvista.org

""" % NOW.year


CHANGE_BACKGROUND_MENU_TEXT = 'Change Background'


###############################################################################

class GUIWindow(QMainWindow):
    """ Primary GUI object """
    errorsignal = pyqtSignal(str, str)
    closepbar_signal = pyqtSignal()
    signal_close = pyqtSignal()

    def __init__(self, parent=None, app=None, show=True, off_screen_vtk=False):
        """ Generate window and initialize a scene """
        QMainWindow.__init__(self, parent)
        LOG.debug('Initializing GUI...')
        self.app = app
        self.default_style_sheet = self.styleSheet()
        self.save_commands = True  # stores commands internally when True
        self.hold = False
        self.off_screen_vtk = off_screen_vtk
        self.load_dialog = None


        self.resize(800, 600)
        self.setWindowTitle('PyVista GUI')
        self.update_app_icon()

        # tree and associated queries
        self.data = Data(self)

        # Create docks

        # ipython console
        self.console = QIPythonWidget(self)
        self.dock_console = QDockWidget('Console', self)
        self.dock_console.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)

        # commands
        self.textedit_commands = QTextEditCommands(self)
        self.dock_commands = QDockWidget('Commands', self)
        self.dock_commands.setWidget(self.textedit_commands)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_commands)

        # object tree
        self.tree = TreeWidget(self)
        self.dock_tree = QDockWidget('Object Tree', self)
        self.dock_tree.setWidget(self.tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_tree)

        # log panel
        self.textbox_logger = QTextEditLogger(self)
        formatter = logging.Formatter('%(name)-20s - %(levelname)-8s - %(message)s')
        self.textbox_logger.setFormatter(formatter)
        logging.getLogger().addHandler(self.textbox_logger)
        logging.getLogger().setLevel('DEBUG')
        self.dock_logger = QDockWidget('Log', self)
        self.dock_logger.setWidget(self.textbox_logger.widget)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_logger)

        # vtk frame if available
        if off_screen_vtk:
            self.plotter = Plotter(off_screen=True)
        else:
            self.plotter = QtInteractor(self)
            self.dock_vtk = QDockWidget('Viewer', self)
            self.dock_vtk.setWidget(self.plotter.interactor)
            self.addDockWidget(Qt.RightDockWidgetArea, self.dock_vtk)

            self.splitDockWidget(self.dock_tree, self.dock_vtk, Qt.Horizontal)
            self.splitDockWidget(self.dock_vtk, self.dock_console, Qt.Vertical)

            self.resizeDocks([self.dock_vtk, self.dock_console], [4, 1], Qt.Vertical)
            self.resizeDocks([self.dock_vtk, self.dock_tree], [4, 1],
                             Qt.Horizontal)

            self.plotter.add_toolbars(self)
            # build main menu
            self.main_menu = QMenuBar(parent=self)
            self.main_menu.setNativeMenuBar(False)
            self.setMenuBar(self.main_menu)
            self.signal_close.connect(self.main_menu.clear)
            self.file_menu = self.create_file_menu()
            self.view_menu = self.create_view_menu()
            self.tools_menu = self.create_tools_menu()

        self.tabifyDockWidget(self.dock_console, self.dock_commands)
        self.tabifyDockWidget(self.dock_commands, self.dock_logger)
        self.dock_console.raise_()

        # connects
        self.errorsignal.connect(self.error_dialog)
        self.closepbar_signal.connect(self._closepbar)
        LOG.debug('GUI initialized')

        # Show frame
        self.enable_dark_mode(rcParams['dark_mode'])

        if show:
            self.show()


    def scale_axes_dialog(self, show=True):
        """Open scale axes dialog."""
        return ScaleAxesDialog(self.app_window, self, show=show)


    def create_file_menu(self):
        file_menu = self.main_menu.addMenu('File')
        file_menu.addAction('Take Screenshot', self._qt_screenshot)
        file_menu.addAction('Export as VTKjs', self._qt_export_vtkjs)

        # TODO: place holder until we make this bettter
        mesh_menu = file_menu.addMenu('Add Geometries')
        mesh_menu.addAction('Arrow', lambda: self.plotter.add_mesh(pyvista.Arrow()))
        mesh_menu.addAction('Cone', lambda: self.plotter.add_mesh(pyvista.Cone()))
        mesh_menu.addAction('Cube', lambda: self.plotter.add_mesh(pyvista.Cube()))
        mesh_menu.addAction('Cylinder', lambda: self.plotter.add_mesh(pyvista.Cylinder()))
        mesh_menu.addAction('Sphere', lambda: self.plotter.add_mesh(pyvista.Sphere()))
        mesh_menu.addAction('Wavelet', lambda: self.plotter.add_volume(pyvista.Wavelet()))

        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        return file_menu


    def create_view_menu(self):
        view_menu = self.main_menu.addMenu('View')
        view_menu.addAction('Toggle Eye Dome Lighting', self._toggle_edl)
        view_menu.addAction('Scale Axes', self.scale_axes_dialog)
        view_menu.addAction('Clear All', self.plotter.clear)
        cam_menu = view_menu.addMenu('Camera')
        cam_menu.addAction('Toggle Parallel Projection', self._toggle_parallel_projection)

        view_menu.addSeparator()
        # Orientation marker
        orien_menu = view_menu.addMenu('Orientation Marker')
        orien_menu.addAction('Show All', self.plotter.show_axes_all)
        orien_menu.addAction('Hide All', self.plotter.hide_axes_all)
        # Bounds axes
        axes_menu = view_menu.addMenu('Bounds Axes')
        axes_menu.addAction('Add Bounds Axes (front)', self.plotter.show_bounds)
        axes_menu.addAction('Add Bounds Grid (back)', self.plotter.show_grid)
        axes_menu.addAction('Add Bounding Box', self.plotter.add_bounding_box)
        axes_menu.addSeparator()
        axes_menu.addAction('Remove Bounding Box', self.plotter.remove_bounding_box)
        axes_menu.addAction('Remove Bounds', self.plotter.remove_bounds_axes)

        view_menu.addSeparator()

        action = QAction('Anti-Aliasing', view_menu, checkable=True)
        action.setChecked(True)
        action.triggered.connect(self.plotter.enable_anti_aliasing)
        view_menu.addAction(action)

        self.action_dark_mode = QAction('Dark Mode', view_menu, checkable=True)
        self.action_dark_mode.setChecked(rcParams['dark_mode'])
        self.enable_dark_mode(rcParams['dark_mode'])
        self.action_dark_mode.triggered.connect(self.enable_dark_mode)
        view_menu.addAction(self.action_dark_mode)

        # A final separator to separate OS options
        view_menu.addSeparator()

        return view_menu

    def create_tools_menu(self):
        tool_menu = self.main_menu.addMenu('Tools')
        # TODO: add these when picking is fixed
        # tool_menu.addAction('Enable Cell Picking (through)', self.plotter.enable_cell_picking)
        # tool_menu.addAction('Enable Cell Picking (visible)', lambda: self.plotter.enable_cell_picking(through=False))
        return tool_menu


    def error_dialog(self, txt, textinfo=None):
        """ Creates error dialogue """
        self.err_message_box = QMessageBox(self)
        self.err_message_box.setIcon(QMessageBox.Critical)

        self.err_message_box.setText(txt)
        if textinfo:
            self.err_message_box.setInformativeText(textinfo)
        self.err_message_box.setWindowTitle('Error')
        self.err_message_box.show()

    def _closepbar(self):
        """ Only to be accessed by a signal call """
        self.pbar.signal_close()

    def enable_dark_mode(self, state=True):
        """ sets style sheet to dark mode """
        if state:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            self.setStyleSheet(self.default_style_sheet)
        self.console.enable_dark_mode(state)
        rcParams['dark_mode'] = state

        if hasattr(self, 'action_dark_mode'):
            self.action_dark_mode.blockSignals(True)
            self.action_dark_mode.setChecked(state)
            self.action_dark_mode.blockSignals(False)


    def change_background(self):
        """ Pulls up change background dialog """
        self.color_dlg = ColorDialog(self)
        self.color_dlg.color_picked.connect(self.plotter.set_background)


    def add_menu_item(self, menu, text, func, addsep=False, enabled=True,
                      shortcut=None):
        """ Clean way of adding menu items """
        item = QAction(text, self)
        if func:
            item.triggered.connect(func)

        if addsep:
            menu.insertSeparator(menu.addAction(item))
        else:
            menu.addAction(item)

        if enabled:
            item.setEnabled(True)
        else:
            item.setEnabled(False)

        if shortcut is not None:
            item.setShortcut(shortcut)

        return item


    def load_mesh(self):
        """Loads a mesh from file using a file dialog"""
        self.file_dialog = LoadMeshDialog(self, callback=self.data.load_meesh)


    def _qt_screenshot(self, show=True):
        return FileDialog(self,
                          filefilter=['Image File (*.png)',
                                      'JPEG (*.jpeg)'],
                          show=show,
                          directory=os.getcwd(),
                          callback=self.plotter.screenshot)

    def _qt_export_vtkjs(self, show=True):
        """Spawn an save file dialog to export a vtkjs file."""
        return FileDialog(self,
                          filefilter=['VTK JS File(*.vtkjs)'],
                          show=show,
                          directory=os.getcwd(),
                          callback=self.plotter.export_vtkjs)

    def _toggle_edl(self):
        if hasattr(self.plotter.renderer, 'edl_pass'):
            return self.plotter.disable_eye_dome_lighting()
        return self.plotter.enable_eye_dome_lighting()

    def _toggle_parallel_projection(self):
        if self.plotter.camera.GetParallelProjection():
            return self.disable_parallel_projection()
        return self.plotter.enable_parallel_projection()

    def update_app_icon(self, icon_file=None):
        """Update the app icon to an `ico` file."""
        if os.name == 'nt':  # pragma: no cover
            # DO NOT EVEN ATTEMPT TO UPDATE ICON ON WINDOWS
            return False
        if icon_file is None:
            icon_file = assets.pyvista_logo_file
        if os.path.isfile(icon_file):
            self.setWindowIcon(QIcon(os.path.abspath(icon_file)))
        else:
            LOG.warning('Unable to find icon file: {}'.format(icon_file))
            return False
        return True
