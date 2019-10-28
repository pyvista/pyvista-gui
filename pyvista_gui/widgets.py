import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QPlainTextEdit, QTreeView


class QTextEditLogger(QPlainTextEdit, logging.Handler):
    write_text_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.write_text_signal.connect(self.widget.appendPlainText)

        self.widget.setFont(QFont("Courier", 12))

    def emit(self, record):
        msg = self.format(record)
        self.write_text_signal.emit(msg)


class QTextEditCommands(QPlainTextEdit):
    """ Displays commands as they are run by the GUI """
    write_text_signal = pyqtSignal(str)

    def __init__(self, parent):
        super(QTextEditCommands, self).__init__(parent)
        self.setReadOnly(True)
        self.write_text_signal.connect(self.appendPlainText)

        self.setFont(QFont("Courier", 12))

    def add_command(self, command):
        """ Writes a command to the panel """
        if command:
            self.write_text_signal.emit('%s\n' % command)


class TreeWidget(QTreeView):
    """ Displays objects as an object tree """

    def __init__(self, parent):
        super(TreeWidget, self).__init__(parent)
        self.parent = parent

        # add menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(["Objects"])
        self.model.itemChanged.connect(self.edit_name)

    def edit_name(self, item):
        """ Makes the name of the item in the tree matches the object name """
        obj = item.data()
        if obj:
            obj.name = item.text()

    def addItem(self, item, header, mainheader=None, editable=True):
        """ Adds item to tree """
        if mainheader is None:
            finds = self.model.findItems(header)
            if not finds:
                itemheader = QStandardItem(header)
                self.model.appendRow(itemheader)
            else:
                itemheader = finds[0]
        else:
            finds = self.model.findItems(mainheader)
            if not finds:
                raise Exception('main header %s does not exist' % mainheader)
            main_itemheader = finds[0]

            for i in range(main_itemheader.rowCount()):
                itemheader = main_itemheader.child(i, 0)
                if itemheader:
                    if header is itemheader.data():
                        break

        standardItem = QStandardItem(item.name)
        standardItem.setEditable(editable)
        standardItem.setData(item)
        itemheader.appendRow(standardItem)

    def open_menu(self, position):  # pragma: no cover
        """ Activates when right click in tree """
        index = self.selectedIndexes()

        if not index:
            return
        item = self.model.itemFromIndex(index[0])
        obj = item.data()

        if hasattr(obj, 'menu'):
            menu = obj.menu
            menu.exec_(self.viewport().mapToGlobal(position))
            return menu

    def remove_item(self, data):
        """ removes an item from the modal list """
        removed = False
        # check each header for a match
        for i in range(self.model.rowCount()):
            header = self.model.item(i)
            for i in range(header.rowCount()):
                item = header.child(i, 0)
                if item:
                    if data is item.data():
                        item.setData(None)
                        header.removeRow(i)
                        removed = removed or True
                        break

                if item.hasChildren():
                    for j in range(item.rowCount()):
                        subitem = item.child(j, 0)
                        if data is subitem.data():
                            subitem.setData(None)
                            item.removeRow(j)
                            removed = removed or True
                            break

            # remove empty headers
            if not header.rowCount():
                self.model.removeRow(header.row())
                break

        return removed
