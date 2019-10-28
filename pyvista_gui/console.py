import sys
from pydoc import help

# from qtconsole.manager import QtKernelManager
import qdarkstyle
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

FROZEN = getattr(sys, 'frozen', False)


def _complete(self):
    """ Performs completion at the current cursor location. """
    try:
        # Send the completion request to the kernel
        msg_id = self.kernel_client.complete(
            code=self.input_buffer,
            cursor_pos=self._get_input_buffer_cursor_pos(),
        )
        pos = self._get_cursor().position()
        info = self._CompletionRequest(msg_id, pos)
        self._request_info['complete'] = info
    except:
        pass


# disable completion when frozen
if FROZEN:
    from qtconsole import frontend_widget
    frontend_widget.FrontendWidget._complete = _complete


class QIPythonWidget(RichJupyterWidget):

    def __init__(self, parent, custom_banner=None, *args, **kwargs):
        super(QIPythonWidget, self).__init__(*args, **kwargs)
        if custom_banner is not None:
            self.banner = custom_banner

        self.font_size = 8
        self.default_style_sheet = self.styleSheet()

        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel(show_banner=False)
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()
        self.gui = parent

        # override "exit" function
        def exit():
            """ Exit the pyvista_gui """
            parent.close()

        self.push_vars({'gui': parent,
                        'exit': exit,
                        'quit': exit,
                        'help': help})

    @property
    def variables(self):
        """ Variables local to the qtconsole """
        return self.shell.ns_table['user_local']

    def clear_variables(self):
        varlist = list(self.variables)
        for var in varlist:
            variable = self.variables[var]
            if hasattr(variable, 'remove'):
                try:
                    variable.remove()
                except:
                    pass

    @property
    def shell(self):
        """ Return shell object """
        return self.kernel_manager.kernel.shell

    def enable_dark_mode(self, state):
        if state:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            self.setStyleSheet(self.default_style_sheet)

    def push_vars(self, variables):
        """Given a dictionary containing name / value pairs, push those
        variables to the Jupyter console widget.
        """
        self.shell.push(variables)

    def clear(self):
        """ Clear the terminal """
        self._control.clear()

    def execute_command(self, command):
        """Execute a command in the frame of the console widget"""
        self._execute(command, False)

    def _execute(self, source, hidden):
        """Additional layer on execution to save commands and stop the
        parent gui from doing the same.
        """
        # TODO:
        # if self.gui:
        #     self.gui.data.store_command(source)
        #     self.gui.save_commands = False

        super(QIPythonWidget, self)._execute(source, hidden)

        if self.gui:
            self.gui.save_commands = True
