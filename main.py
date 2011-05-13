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

# Global variables to contain the different parts of the GUI
ACTION_CHOOSE = None
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

### Define some function that make up the functionality of the program.
def show_image():
    if not internalState.image_available():
        return
    image = internalState.current_image_scaled_and_rotated()
    IMAGE_AREA.setPixmap(image)
    text = "" + internalState.current_image_complete_path()
    pos = internalState.get_current_image_number()
    total = internalState.get_total_number_images()
    text += '  [' + str(pos) + '/' + str(total) + ']'
    STATUS_BAR_LABEL.setText(text)

def fit_image():
    if not internalState.image_available():
        return
    pix = internalState.current_image()
    IMAGE_AREA.setPixmap(pix.scaled(SCROLL_AREA.maximumViewportSize(),
                                   QtCore.Qt.KeepAspectRatio))

def zoom(scaleFactor):
    if not internalState.image_available():
        return
    pix = internalState.current_image()
    newSize = IMAGE_AREA.size() * scaleFactor
    IMAGE_AREA.setPixmap(pix.scaled(newSize, QtCore.Qt.KeepAspectRatio))
    newSize = IMAGE_AREA.pixmap().size()
    SCROLL_AREA.ensureVisible(newSize.width()/2.0, newSize.height()/2.0,
                             SCROLL_AREA.maximumViewportSize().width()/2.0,
                             SCROLL_AREA.maximumViewportSize().height()/2.0)

def zoom_in():
    zoom(1.25)

def zoom_out():
    zoom(0.8)

def show_next_image():
    internalState.next_image(SCROLL_AREA.maximumViewportSize())
    show_image()

def show_previous_image():
    internalState.previous_image(SCROLL_AREA.maximumViewportSize())
    show_image()

def discard_image():
    if not internalState.image_available():
        return
    
    cd = internalState.current_directory()
    if not os.path.exists(cd + '/discarded'):
        os.mkdir(cd + '/discarded')
    if not os.path.isdir(cd + '/discarded'):
        raise InternalException('A file named discarded was found. ' +
                                'A folder of that name to move the photos' +
                                'to could not be created.')
    filename = internalState.current_image_name()
    position = internalState.pos
    shutil.move(internalState.current_image_complete_path(),
                cd + '/discarded/' + filename)
    internalState.discard_current_image(SCROLL_AREA.maximumViewportSize())

    if DISCARDING_IN_HISTORY:
        action = Actions.DeletionAction(internalState, cd, filename, position)
        internalState.add_to_history(action)
    
    if internalState.image_available():
        show_image()
    else:
        clear()

def clear():
    IMAGE_AREA.clear()
    STATUS_BAR_LABEL.clear()
    IMAGE_AREA.setText('No images loaded...')

def rotate_image(degrees):
    internalState.rotate_current_image(degrees,
                                       SCROLL_AREA.maximumViewportSize())
    show_image()
    if ROTATION_IN_HISTORY:
        action = Actions.RotationAction(internalState, degrees,
                                        internalState.pos)
        internalState.add_to_history(action)

    if AUTOMATICALLY_SAVE_ROTATIONS:
        save_image(False)


def rotate_image_right():
    rotate_image(90)

def rotate_image_left():
    rotate_image(-90)

def save_image(warn=True):
    if not internalState.image_available():
        return

    image = internalState.current_image_rotated()
    path = internalState.current_image_complete_path()
    res = image.save(path)

    if res == 0:
        if not warn:
            print Exception('It is not possible to save changes to the images!')
        else:
            QtGui.QMessageBox.critical(mainWindow, 'Error saving image',
                                       'It was not possible to save ' + \
                                       'the changes to the image(s)!')
    else:
        internalState.reset_transformation(path)

# Ask the user to select a directory and save it in 'internalState.directory'.
def choose_images_to_keep():
    if not FILE_DIALOG.exec_():
        return

    res = FILE_DIALOG.selectedFiles()
    internalState.start(res, SCROLL_AREA.maximumViewportSize())
    show_next_image()

def undo():
    internalState.undo(SCROLL_AREA.maximumViewportSize())
    show_image()

def redo():
    internalState.redo(SCROLL_AREA.maximumViewportSize())
    show_image()

if __name__ == '__main__':
    ### Load the main window object created with QtDesigner.
    app = QtGui.QApplication(sys.argv)
    mainWindow = uic.loadUi('./qt/mainWindow.ui')

    # A global dialog to select files.
    FILE_DIALOG = QtGui.QFileDialog(mainWindow)
    FILE_DIALOG.setFileMode(QtGui.QFileDialog.Directory)
    LIST_VIEW = FILE_DIALOG.findChild(QtGui.QListView,'listView')
    LIST_VIEW.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

    ### Get all the different parts of the gui that we need.
    # This is done like this in case we change the structure
    # in QtDesigner.
    ACTION_CHOOSE = mainWindow.actionChoose
    ACTION_QUIT = mainWindow.actionQuit
    ACTION_FIT = mainWindow.action_Fit_to_Window
    ACTION_ZOOM_IN = mainWindow.actionZoom_In
    ACTION_ZOOM_OUT = mainWindow.actionZoom_Out
    ACTION_ROTATE_RIGHT = mainWindow.action_Rotate_Right
    ACTION_ROTATE_LEFT = mainWindow.action_Rotate_Left
    ACTION_SAVE = mainWindow.actionSave
    SCROLL_AREA = mainWindow.scrollArea
    IMAGE_AREA = mainWindow.imageLabel
    STATUS_BAR = mainWindow.statusBar()
    STATUS_BAR_LABEL = QtGui.QLabel('')
    STATUS_BAR.addWidget(STATUS_BAR_LABEL)

    # Change the resize event so that the preloaded images are
    # resized.
    originalResizeEvent = SCROLL_AREA.resizeEvent
    def f(event):
        originalResizeEvent(event)
        viewportSize = SCROLL_AREA.maximumViewportSize()
        internalState.rescale_images(viewportSize)
    SCROLL_AREA.resizeEvent = f

    # TODO: Find a nice icon that I'm allowed to use.
    # mainWindow.setWindowIcon(QtGui.QIcon('./img/camera.jpg'))

    # Here signal-slot connections are added manually.
    ACTION_CHOOSE.connect(ACTION_CHOOSE, QtCore.SIGNAL('triggered()'),
                         choose_images_to_keep)
    ACTION_QUIT.connect(ACTION_QUIT, QtCore.SIGNAL('triggered()'),
                       QtGui.qApp, QtCore.SLOT('quit()'))
    ACTION_FIT.connect(ACTION_FIT, QtCore.SIGNAL('triggered()'), fit_image)
    ACTION_ZOOM_IN.connect(ACTION_ZOOM_IN, QtCore.SIGNAL('triggered()'), zoom_in)
    ACTION_ZOOM_OUT.connect(ACTION_ZOOM_OUT, QtCore.SIGNAL('triggered()'), zoom_out)
    ACTION_ROTATE_RIGHT.connect(ACTION_ROTATE_RIGHT, QtCore.SIGNAL('triggered()'),
                              rotate_image_right)
    ACTION_ROTATE_LEFT.connect(ACTION_ROTATE_LEFT, QtCore.SIGNAL('triggered()'),
                             rotate_image_left)
    ACTION_SAVE.connect(ACTION_SAVE, QtCore.SIGNAL('triggered()'),
                             save_image)
    shortcut = QtGui.QShortcut('N',mainWindow)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'), show_next_image)
    shortcut = QtGui.QShortcut('B',mainWindow)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'),
                      show_previous_image)
    shortcut = QtGui.QShortcut('D',mainWindow)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'), discard_image)
    shortcut = QtGui.QShortcut('Z',mainWindow)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'), undo)
    shortcut = QtGui.QShortcut('Y',mainWindow)
    shortcut.connect(shortcut, QtCore.SIGNAL('activated()'), redo)
    
    internalState = InternalState()
    clear() #Put the program in its beginning state.
    mainWindow.show()
    sys.exit(app.exec_())
