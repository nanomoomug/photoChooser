#!/usr/bin/env python
"""
A class containing all the different shortcuts that this program
uses and some logic to handle them.
"""

from PyQt4 import QtGui, QtCore

def set_shortcut(window, shortcut_string, func):
    shortcut = QtGui.QShortcut(shortcut_string, window)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'), func)

class ShortcutsHandler:
    def __init__(self):
        # All strings representing shortcuts should end with
        # '_shortcut'.
        self.next_image_shortcut = QtGui.QKeySequence.MoveToNextPage
        self.previous_image_shortcut = QtGui.QKeySequence.MoveToPreviousPage
        self.discard_image_shortcut = QtGui.QKeySequence.Delete
        self.undo_shortcut = QtGui.QKeySequence.Undo
        self.redo_shortcut = QtGui.QKeySequence.Redo

    def set_shortcuts(self, window, next_image_func, previous_image_func,
                      discard_image_func, undo_func, redo_func):
        set_shortcut(window, self.next_image_shortcut, next_image_func)
        set_shortcut(window, self.previous_image_shortcut, previous_image_func)
        set_shortcut(window, self.discard_image_shortcut, discard_image_func)
        set_shortcut(window, self.undo_shortcut, undo_func)
        set_shortcut(window, self.redo_shortcut, redo_func)

