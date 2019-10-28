import logging
import os
import sys

from PyQt5.QtWidgets import QApplication

from pyvista_gui.gui import GUIWindow

LOG = logging.getLogger(__name__)
LOG.setLevel('DEBUG')



def main(debug=False, loglevel='DEBUG', script=None, off_screen_vtk=False):  # pragma: no cover
    """ Starts the PyVista GUI """

    logging.getLogger().setLevel('CRITICAL')

    app = QApplication(sys.argv)
    gui = GUIWindow(app=app, off_screen_vtk=off_screen_vtk)

    # icon_file = resource_path('icon.ico')
    # if os.path.isfile(icon_file):
    #     icon = QIcon(icon_file)
    #     gui.setWindowIcon(icon)
    # else:
    #     LOG.warning('Unable to find icon file')

    # if script is not None:
    #     if os.path.isfile(script):
    #         exec('gui.data.load_script("%s")' % script)
    #     else:
    #         gui.show_error('Unable to find python script file "%s"\n' % str(script)
    #                        + 'Try using absolute paths or loading it from '
    #                        + 'the GUI.')

    # always start in home directory
    try:
        from pathlib import Path
        home = str(Path.home())
        os.chdir(home)
    except:
        LOG.warning('Unable to change to home directory')

    app.exec_()





if __name__ == '__main__':
    main()
