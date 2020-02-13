"""pyvista_gui data module"""
import logging
import os

# from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog,
                             QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
                             QFormLayout, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QListWidget, QMenu,
                             QPushButton, QSlider, QSpinBox, QStackedWidget,
                             QVBoxLayout)

import pyvista

import pyvista_gui
from pyvista_gui.constants import PY_FILE_FILTER
from pyvista_gui.dialogs import FileDialog
from pyvista_gui.utilities import protected_thread

LOG = logging.getLogger(__name__)
LOG.setLevel('DEBUG')


class Data():
    """ Holds active data for the gui """

    def __init__(self, parent):
        self.parent = parent
        self.meshes = []
        self.commands = []
        self.load_script_dlg = None

        # initialize cached commands
        self.reset_stored_commands()

        self.varcount = {'Mesh': 0,}

    def reset_stored_commands(self):
        """resets stored commands"""
        self.commands = []

    def list_commands(self):
        for command in self.commands:
            print(command)

    @property
    def items(self):
        items = []
        items.extend(self.meshes)
        return items

    def save_commands_dialog(self):
        """ Saves commands to a python script """
        self.save_commands_dlg = FileDialog(self.parent,
                                            PY_FILE_FILTER,
                                            save_mode=True,
                                            callback=self._save_commands)
        return self.save_commands_dlg

    def _save_commands(self, filename):
        """ Save commands to file """
        header = '"""\nAuto-generated script for PyVista-GUI\n'
        header += 'Using pyvista     v%s\n' % pyvista.__version__
        header += '      pyvista_gui v%s\n' % pyvista_gui.__version__
        header += '"""\n'

        # determine extra imports
        import_modules = []
        test_modules = []
        for command in self.commands:
            for module in test_modules:
                if '%s.' % module in command:
                    if module not in import_modules:
                        import_modules.append(module)

        for module in import_modules:
            self.commands.insert(0, 'import %s' % module)

        LOG.info('Writing auto-generated script for PyVista to %s', filename)

        with open(filename, 'w') as f:
            f.write(header + '\n')
            for command in self.commands:
                if command is not None:
                    command = command.replace('\\', '/')
                    f.write(command + '\n')

    def store_command(self, command):
        """ Stores a command """
        if command is not None:
            self.commands.append(command)

    @protected_thread
    def load_mesh(self, uinput, name=None, reset_camera=True):
        """ Adds a surface to self """
        raise NotImplementedError()
        # TODO
        # return GuiSurface(uinput, self.parent, name=name, reset_camera=reset_camera)



    def remove(self, item):
        """ Removes an item from the database """
        if item in self.meshes:
            self.meshes.remove(item)


    def reset(self):
        """ removes all items from database """
        for item in self.items:
            item.remove()

        # reset commands
        self.reset_stored_commands()
        if hasattr(self.parent.plotter, 'reset'):
            self.parent.plotter.reset()
        self.parent.textedit_commands.clear()

        # clear gui widgets
        self.parent.textbox_logger.widget.clear()
        self.parent.console.clear()

    # def save(self, filename):  # pragma: no cover
    #     """ save all data """
    #     with zipfile.ZipFile(filename, 'w') as zipfile:
    #         for item in self.items:
    #             item.write_to_zip(zipfile)

    def load_script_dialog(self):
        """ Open up a file dialog to load a Python script """
        self.load_script_dlg = FileDialog(self.parent, PY_FILE_FILTER,
                                          callback=self.load_script)
        return self.load_script_dlg

    def load_script(self, filename):
        """ Run a Python script from the qtconsole """
        if not os.path.isfile(filename):
            err_str = 'Unable to find python script file "%s"\n' % str(filename) +\
                      'Try using absolute paths or loading it from '+\
                      'the GUI.'
            LOG.error(err_str)
            self.parent.show_error(err_str)
            return

        # execute script and don't save internal commands
        self.parent.save_commands = False
        self.parent.hold = True

        # set hold parameter to False when complete to let main know
        # the script is complete
        command = 'exec(open("%s").read()); gui.hold = False' % filename
        command += ';gui.save_commands = True'
        self.parent.console.execute(command)

        with open(filename) as f:
            text = f.read()
        self.store_command(text)

        note = '# commands from %s' % filename
        self.parent.textedit_commands.add_command(note)
        self.parent.textedit_commands.add_command(text)
        note = '# finished with commands from %s' % filename
        self.parent.textedit_commands.add_command(note)
