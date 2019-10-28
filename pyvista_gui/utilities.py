import logging
import sys
import time
import traceback
from functools import wraps
from threading import Thread

log = logging.getLogger(__name__)
log.setLevel('DEBUG')


# python 2/3 string compatability
if sys.version[0] == '2':
    from past.builtins import basestring
else:
    basestring = str


def build_command(obj, func, *args, **kwargs):
    """ build a command for a non-gui session of pyvista """
    import pyvista

    func_name = func.__name__
    if func_name[0] == '_':
       func_name = func_name[1:]

    # verify function is a method in a morph class
    if not hasattr(obj, 'class_name'):
        return

    if hasattr(pyvista, obj.class_name):
        pyvista_class = eval('pyvista.%s' % obj.class_name)
    else:
        return

    if not hasattr(pyvista_class, func_name):
        return

    # convert args to strings
    varname = obj.varname
    str_args = []
    for arg in args[1:]:
        # if isinstance(arg, GuiCommon):
        #     str_args.append(arg.varname)
        if isinstance(arg, basestring):
            str_args.append('"%s"' % arg)
        else:
            str_args.append(str(arg))

    return '%s.%s(%s)' % (varname, func_name, ', '.join(str_args))


def protected_thread(fn):
    """
    Calls a function using a thread.  Reports error under the
    assumption the first argument is a GuiCommon class.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        self = args[0]

        def protected_fn():
            try:
                fn(*args, **kwargs)
                command = build_command(self, fn, *args, **kwargs)
                self.store_command(command)
            except Exception as exception:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                log.error(exception)
                if hasattr(self, 'exceptions'):
                    self.exceptions.append(exception)
                self.parent.show_error(exception)

        thread = Thread(target=protected_fn)
        thread.start()

        if self.parent.hold:
            while thread.is_alive():
                # self.parent.render()
                self.parent.app.processEvents()
                time.sleep(0.1)

        if hasattr(self, 'threads'):
            self.threads.append(thread)
        return thread

    # wrapper.__doc__ = fn.__doc__
    # wrapper.__name__ = fn.__name__

    return wrapper


def threaded(fn):
    """ calls a function using a thread """
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper
