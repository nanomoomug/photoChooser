#!/usr/bin/env python
"""
A class containing all the different shortcuts that this program
uses and some logic to handle them.
"""

from PyQt4 import QtGui, QtCore

class Shortcut:
    def __init__(self, qt_shortcut, action_description):
        self.qt_shortcut = qt_shortcut
        self.action_description = action_description

    def connect(self, func):
        self.qt_shortcut.connect(self.qt_shortcut, QtCore.SIGNAL('activated()'), func)

class ShortcutsHandler:
    def __init__(self, window):
        # All strings representing shortcuts should end with
        # '_shortcut'.
        next_image_qt_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence.MoveToNextPage, window)
        previous_image_qt_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence.MoveToPreviousPage, window)
        discard_image_qt_shortcut = QtGui.QShortcut(QtGui.QKeySequence.Delete,
                                                    window)
        undo_qt_shortcut = QtGui.QShortcut(QtGui.QKeySequence.Undo, window)
        redo_qt_shortcut = QtGui.QShortcut(QtGui.QKeySequence.Redo, window)

        self.all_shortcuts = []

        def new_shortcut(qt_shortcut, action_description):
            shortcut = Shortcut(qt_shortcut, action_description)
            self.all_shortcuts.append(shortcut)
            return shortcut
            
        self.next_image_shortcut = new_shortcut(next_image_qt_shortcut,
                                                'Next Image')
        self.previous_image_shortcut = new_shortcut(previous_image_qt_shortcut,
                                                    'Previous Image')
        self.discard_image_shortcut = new_shortcut(discard_image_qt_shortcut,
                                                   'Discard Image')
        self.undo_shortcut = new_shortcut(undo_qt_shortcut, 'Undo')
        self.redo_shortcut = new_shortcut(redo_qt_shortcut, 'Redo')

    def set_shortcuts(self, next_image_func, previous_image_func,
                      discard_image_func, undo_func, redo_func):
        self.next_image_shortcut.connect(next_image_func)
        self.previous_image_shortcut.connect(previous_image_func)
        self.discard_image_shortcut.connect(discard_image_func)
        self.undo_shortcut.connect(undo_func)
        self.redo_shortcut.connect(redo_func)

    def get_all_shortcuts(self):
        return self.all_shortcuts

