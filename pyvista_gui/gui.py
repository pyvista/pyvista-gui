""" This is the main GUI """

import datetime
import logging

import qdarkstyle
from PyQt5.QtCore import Qt, pyqtSignal
# from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QDockWidget, QHBoxLayout,
                             QMainWindow, QMenu, QMessageBox, QProgressDialog,
                             QSizePolicy, QSplitter, QVBoxLayout)

from pyvista.plotting import Plotter
from pyvistaqt import QtInteractor

from pyvista_gui.console import QIPythonWidget
from pyvista_gui.data import Data
from pyvista_gui.dialogs import ColorDialog, LoadMeshDialog
from pyvista_gui.options import rcParams
from pyvista_gui.widgets import QTextEditCommands, QTextEditLogger, TreeWidget

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
    trigger_render = pyqtSignal()
    errorsignal = pyqtSignal(str, str)
    closepbar_signal = pyqtSignal()

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

            # self.plotter.add_toolbars(self)

        self.tabifyDockWidget(self.dock_console, self.dock_commands)
        self.tabifyDockWidget(self.dock_commands, self.dock_logger)
        self.dock_console.raise_()

        # Create menu
        self.make_menu()

        # connects
        self.trigger_render.connect(self.plotter.render)
        self.errorsignal.connect(self.error_dialog)
        self.closepbar_signal.connect(self._closepbar)
        LOG.debug('GUI initialized')

        # Show frame
        self.enable_dark_mode(rcParams['dark_mode'])

        if show:
            self.show()


    def make_menu(self):
        """ Generates menus """
        self.menu = self.menuBar()
        self.menu.setNativeMenuBar(False)

        # main menu
        # self.file_menu = self._build_file_menu()
        self.view_menu = self._build_view_menu()
        # self.panels_menu = self._build_panels_menu()
        # self.help_menu = self._build_help_menu()


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

    def _build_view_menu(self):
        """ Creates view menu """
        menu = self.menu.addMenu('View')
        if not self.off_screen_vtk:
            self.add_menu_item(menu, CHANGE_BACKGROUND_MENU_TEXT,
                               self.change_background)

            # Camera views
            sub_menu = QMenu('Camera Positions', parent=self)
            menu.addMenu(sub_menu)

            _view_vector = lambda *args: self.plotter.view_vector(*args)
            cvec_setters = {
                # Viewing vector then view up vector - PyVista handles the rest
                'Top (-Z)': lambda: _view_vector((0,0,1), (0,1,0)),
                'Bottom (+Z)': lambda: _view_vector((0,0,-1), (0,1,0)),
                'Front (-Y)': lambda: _view_vector((0,1,0), (0,0,1)),
                'Back (+Y)': lambda: _view_vector((0,-1,0), (0,0,1)),
                'Left (-X)': lambda: _view_vector((1,0,0), (0,0,1)),
                'Right (+X)': lambda: _view_vector((-1,0,0), (0,0,1)),
            }

            for key in cvec_setters.keys():
                self.add_menu_item(sub_menu, key, cvec_setters[key])

            action = QAction('Anti-Aliasing', menu, checkable=True)
            action.setChecked(True)
            action.triggered.connect(self.plotter.enable_anti_aliasing)
            menu.addAction(action)

        self.action_dark_mode = QAction('Dark Mode', menu, checkable=True)
        self.action_dark_mode.setChecked(rcParams['dark_mode'])
        self.enable_dark_mode(rcParams['dark_mode'])
        self.action_dark_mode.triggered.connect(self.enable_dark_mode)
        menu.addAction(self.action_dark_mode)

        self.view_menu = menu


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
