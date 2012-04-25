#!/usr/bin/env python
"""
Contains the Gui and actions logic of the program.

This file works as the main function of the program. It loads the gui created
with QtDesigner and fetches the different parts into global variables.

Then come all the implementations of the different actions the program can
perform as global functions.

At last all signal and slots are connected with the correct function and
shortcuts and the program is started by calling the qt main loop.
"""

import sys
import os
import shutil

from PyQt4 import QtGui, QtCore
from PyQt4 import uic

from InternalException import InternalException
from InternalState import InternalState
import Actions
from Shortcuts import ShortcutsHandler

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

# Configuration variables, these should later be read from a config file
ROTATION_IN_HISTORY = True
DISCARDING_IN_HISTORY = True
AUTOMATICALLY_SAVE_ROTATIONS = True
ZOOM_POSITIVE_FACTOR = 1.25
ZOOM_NEGATIVE_FACTOR = 0.8

# Global variables to contain the different parts of the GUI
ACTION_CHOOSE_FOLDER = None
ACTION_QUIT = None
ACTION_FIT = None
ACTION_ZOOM_IN = None
ACTION_ZOOM_OUT = None
ACTION_ROTATE_RIGHT = None
ACTION_ROTATE_LEFT = None
ACTION_SAVE = None
SCROLL_AREA = None
IMAGE_AREA = None
STATUS_BAR = None
STATUS_BAR_LABEL = None
FILE_DIALOG = None
LIST_VIEW = None

# Shortcuts container
SHORTCUTS = None

### Define some function that make up the actions that the program can
### perform.
def show_image():
    if not INTERNAL_STATE.image_available():
        return
    image = INTERNAL_STATE.current_image_scaled_and_rotated()
    IMAGE_AREA.setPixmap(image)
    text = "" + INTERNAL_STATE.current_image_complete_path()
    pos = INTERNAL_STATE.get_current_image_number()
    total = INTERNAL_STATE.get_total_number_images()
    text += '  [' + str(pos) + '/' + str(total) + ']'
    STATUS_BAR_LABEL.setText(text)

def fit_image():
    if not INTERNAL_STATE.image_available():
        return
    pix = INTERNAL_STATE.current_image()
    IMAGE_AREA.setPixmap(pix.scaled(SCROLL_AREA.maximumViewportSize(),
                                   QtCore.Qt.KeepAspectRatio))

def zoom(scale_factor):
    if not INTERNAL_STATE.image_available():
        return
    pix = INTERNAL_STATE.current_image()
    new_size = IMAGE_AREA.size() * scale_factor
    IMAGE_AREA.setPixmap(pix.scaled(new_size, QtCore.Qt.KeepAspectRatio))
    new_size = IMAGE_AREA.pixmap().size()
    SCROLL_AREA.ensureVisible(new_size.width()/2.0, new_size.height()/2.0,
                             SCROLL_AREA.maximumViewportSize().width()/2.0,
                             SCROLL_AREA.maximumViewportSize().height()/2.0)

def zoom_in():
    zoom(ZOOM_POSITIVE_FACTOR)

def zoom_out():
    zoom(ZOOM_NEGATIVE_FACTOR)

def show_next_image():
    INTERNAL_STATE.next_image(SCROLL_AREA.maximumViewportSize())
    show_image()

def show_previous_image():
    INTERNAL_STATE.previous_image(SCROLL_AREA.maximumViewportSize())
    show_image()

def discard_image():
    if not INTERNAL_STATE.image_available():
        return
    
    current_directory = INTERNAL_STATE.current_directory()
    if not os.path.exists(current_directory + '/discarded'):
        os.mkdir(current_directory + '/discarded')
    if not os.path.isdir(current_directory + '/discarded'):
        raise InternalException('A file named discarded was found. ' +
                                'A folder of that name to move the photos' +
                                'to could not be created.')
    filename = INTERNAL_STATE.current_image_name()
    position = INTERNAL_STATE.pos
    shutil.move(INTERNAL_STATE.current_image_complete_path(),
                current_directory + '/discarded/' + filename)
    INTERNAL_STATE.discard_current_image(SCROLL_AREA.maximumViewportSize())

    if DISCARDING_IN_HISTORY:
        action = Actions.DeletionAction(INTERNAL_STATE, current_directory,
                                        filename, position)
        INTERNAL_STATE.add_to_history(action)
    
    if INTERNAL_STATE.image_available():
        show_image()
    else:
        clear()

def clear():
    IMAGE_AREA.clear()
    STATUS_BAR_LABEL.clear()
    IMAGE_AREA.setText('No images loaded...')

def rotate_image(degrees):
    INTERNAL_STATE.rotate_current_image(degrees,
                                        SCROLL_AREA.maximumViewportSize())
    show_image()
    if ROTATION_IN_HISTORY:
        action = Actions.RotationAction(INTERNAL_STATE, degrees,
                                        INTERNAL_STATE.pos)
        INTERNAL_STATE.add_to_history(action)

    if AUTOMATICALLY_SAVE_ROTATIONS:
        save_image(False)


def rotate_image_right():
    rotate_image(90)

def rotate_image_left():
    rotate_image(-90)

def save_image(warn=True):
    if not INTERNAL_STATE.image_available():
        return

    image = INTERNAL_STATE.current_image_rotated()
    path = INTERNAL_STATE.current_image_complete_path()
    res = image.save(path)

    if res == 0:
        if not warn:
            print Exception('It is not possible to save changes to the images!')
        else:
            QtGui.QMessageBox.critical(MAIN_WINDOW, 'Error saving image',
                                       'It was not possible to save ' + \
                                       'the changes to the image(s)!')
    else:
        INTERNAL_STATE.set_image(image)
        INTERNAL_STATE.reset_transformation(path)

# Ask the user to select a directory and save it in 'INTERNAL_STATE.directory'.
def choose_images_to_keep():
    if not FILE_DIALOG.exec_():
        return

    res = FILE_DIALOG.selectedFiles()
    INTERNAL_STATE.start(res, SCROLL_AREA.maximumViewportSize())
    show_next_image()

def undo():
    INTERNAL_STATE.undo(SCROLL_AREA.maximumViewportSize())
    show_image()

def redo():
    INTERNAL_STATE.redo(SCROLL_AREA.maximumViewportSize())
    show_image()

# This next block is pretty much an internal configuration file.
if __name__ == '__main__':
    ### Load the main window object created with QtDesigner.
    APP = QtGui.QApplication(sys.argv)
    MAIN_WINDOW = uic.loadUi('./qt/mainWindow.ui')

    # A global dialog to select files.
    FILE_DIALOG = QtGui.QFileDialog(MAIN_WINDOW)
    FILE_DIALOG.setFileMode(QtGui.QFileDialog.Directory)
    LIST_VIEW = FILE_DIALOG.findChild(QtGui.QListView,'listView')
    LIST_VIEW.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

    ### Get all the different parts of the gui that we need.
    # This is done like this in case we change the structure
    # in QtDesigner.
    ACTION_CHOOSE_FOLDER = MAIN_WINDOW.actionChoose
    ACTION_QUIT = MAIN_WINDOW.actionQuit
    ACTION_FIT = MAIN_WINDOW.action_Fit_to_Window
    ACTION_ZOOM_IN = MAIN_WINDOW.actionZoom_In
    ACTION_ZOOM_OUT = MAIN_WINDOW.actionZoom_Out
    ACTION_ROTATE_RIGHT = MAIN_WINDOW.action_Rotate_Right
    ACTION_ROTATE_LEFT = MAIN_WINDOW.action_Rotate_Left
    ACTION_SAVE = MAIN_WINDOW.actionSave
    SCROLL_AREA = MAIN_WINDOW.scrollArea
    IMAGE_AREA = MAIN_WINDOW.imageLabel
    STATUS_BAR = MAIN_WINDOW.statusBar()
    STATUS_BAR_LABEL = QtGui.QLabel('')
    STATUS_BAR.addWidget(STATUS_BAR_LABEL)

    # Initialize the main object that is manipulated by the function of the
    # program.
    INTERNAL_STATE = InternalState()

    # Change the resize event so that the preloaded images are
    # resized.
    ORIGINAL_RESIZE_EVENT = SCROLL_AREA.resizeEvent
    def func(event):
        ORIGINAL_RESIZE_EVENT(event)
        viewport_size = SCROLL_AREA.maximumViewportSize()
        INTERNAL_STATE.rescale_images(viewport_size)
    SCROLL_AREA.resizeEvent = func

    # TODO: Find a nice icon that I'm allowed to use.
    # MAIN_WINDOW.setWindowIcon(QtGui.QIcon('./img/camera.jpg'))

    # Here signal-slot connections are added manually.
    ACTION_QUIT.connect(ACTION_QUIT, QtCore.SIGNAL('triggered()'),
                        QtGui.qApp, QtCore.SLOT('quit()'))

    action_list = []
    def connect_slot(action, action_description, func):
        action.connect(action, QtCore.SIGNAL('triggered()'), func)
        action_list.append((action, action_description))

    connect_slot(ACTION_CHOOSE_FOLDER, 'Choose Folder', choose_images_to_keep)
    connect_slot(ACTION_FIT, 'Choose Folder', fit_image)
    connect_slot(ACTION_ZOOM_IN, 'Choose Folder', zoom_in)
    connect_slot(ACTION_ZOOM_OUT, 'Choose Folder', zoom_out)
    connect_slot(ACTION_ROTATE_RIGHT, 'Choose Folder', rotate_image_right)
    connect_slot(ACTION_ROTATE_LEFT, 'Choose Folder', rotate_image_left)
    connect_slot(ACTION_SAVE, 'Choose Folder', save_image)

    # Make shortcuts work.
    SHORTCUTS = ShortcutsHandler(MAIN_WINDOW, action_list)
    SHORTCUTS.set_shortcuts(show_next_image, show_previous_image,
                            discard_image, undo, redo)

    def get_overlay_element(label):
        label = QtGui.QLabel(label)
        label.setFixedWidth(120)
        label.setFixedHeight(40)
        label.setAlignment(QtCore.Qt.AlignCenter)
        style = 'QLabel { background-color: rgba(211,211,211,80%); \
                          border: 1px solid black; \
                          border-radius: 7px; }'
        label.setStyleSheet(style)
        return label
    
    layout = QtGui.QGridLayout(SCROLL_AREA)
    layout.setSpacing(15)
    layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
    layout.setContentsMargins(0, 0, 0, 50)

    shortcut_list = SHORTCUTS.get_all_shortcuts()

    h = 0
    all_overlays = []
    for s in shortcut_list:
        text = s.action_description + '\n' + s.qt_shortcut.key().toString()
        overlay = get_overlay_element(text)
        layout.addWidget(overlay, 0, h)
        all_overlays.append(overlay)
        h = h + 1
    
    for i in all_overlays:
        i.hide()

    def f1(event):
        if event.key() == QtCore.Qt.Key_Control:
            for i in all_overlays:
                i.show()
        else:
            for i in all_overlays:
                i.hide()

    def f2(event):
        for i in all_overlays:
            i.hide()

    MAIN_WINDOW.keyPressEvent = f1
    MAIN_WINDOW.keyReleaseEvent = f2
    MAIN_WINDOW.focusOutEvent = f2
    MAIN_WINDOW.installEventFilter(MAIN_WINDOW)

    # Put the program in its beginning state and start the main loop.
    clear() 
    MAIN_WINDOW.show()
    sys.exit(APP.exec_())
