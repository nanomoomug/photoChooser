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
from Actions import *

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

### Define some function that make up the functionality of the program.
def show_image():
    if not internalState.image_available():
        return
    image = internalState.current_image_scaled()
    imageArea.setPixmap(image)
    text = "" + internalState.current_image_complete_path()
    pos = internalState.get_current_image_number()
    total = internalState.get_total_number_images()
    text += '  [' + str(pos) + '/' + str(total) + ']'
    statusBarLabel.setText(text)

def fit_image():
    if not internalState.image_available():
        return
    pix = internalState.current_image()
    imageArea.setPixmap(pix.scaled(scrollArea.maximumViewportSize(),
                                   QtCore.Qt.KeepAspectRatio))

def zoom(scaleFactor):
    if not internalState.image_available():
        return
    pix = internalState.current_image()
    newSize = imageArea.size() * scaleFactor
    imageArea.setPixmap(pix.scaled(newSize, QtCore.Qt.KeepAspectRatio))
    newSize = imageArea.pixmap().size()
    scrollArea.ensureVisible(newSize.width()/2.0,newSize.height()/2.0,
                             scrollArea.maximumViewportSize().width()/2.0,
                             scrollArea.maximumViewportSize().height()/2.0)

def zoom_in():
    zoom(1.25)

def zoom_out():
    zoom(0.8)

def show_next_image():
    internalState.next_image(scrollArea.maximumViewportSize())
    show_image()

def show_previous_image():
    internalState.previous_image(scrollArea.maximumViewportSize())
    show_image()

def discard_image():
    if not internalState.image_available():
        return
    
    cd = internalState.current_directory();
    if not os.path.exists(cd + '/discarded'):
        os.mkdir(cd + '/discarded')
    if not os.path.isdir(cd + '/discarded'):
        raise InternalException('A file named discarded was found. ' +
                                'A folder of that name to move the photos' +
                                'to could not be created.')
    shutil.move(internalState.current_image_complete_path(),
                cd + '/discarded/' + internalState.current_image_name())
    internalState.discard_current_image(scrollArea.maximumViewportSize())
    if internalState.image_available():
        show_image()
    else:
        clear()

def clear():
    imageArea.clear()
    statusBarLabel.clear()
    imageArea.setText('No images loaded...')

def rotate_image(degrees):
    internalState.rotate_current_image(degrees,
                                       scrollArea.maximumViewportSize())
    show_image()

def rotate_image_right():
    rotate_image(90)

def rotate_image_left():
    rotate_image(-90)

# Ask the user to select a direcory and save it in 'internalState.directory'.
def choose_images_to_keep():
    if not fileDialog.exec_():
        return

    res = fileDialog.selectedFiles()
    internalState.start(res, scrollArea.maximumViewportSize())
    show_next_image()

if __name__ == '__main__':
    global actionChoose
    global actionQuit
    global actionFit
    global actionZoomIn
    global actionZoomOut
    global actionRotateRight
    global actionRotateLeft
    global scrollArea
    global imageArea
    global statusBar
    global statusBarLabel
    global fileDialog
    global listView

    ### Load the main window object created with QtDesigner.
    app = QtGui.QApplication(sys.argv)
    mainWindow = uic.loadUi('./qt/mainWindow.ui')

    # A global dialog to select files.
    fileDialog = QtGui.QFileDialog(mainWindow)
    fileDialog.setFileMode(QtGui.QFileDialog.Directory)
    listView = fileDialog.findChild(QtGui.QListView,'listView')
    listView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

    ### Get all the different parts of the gui that we need.
    # This is done like this in case we change the strucuture
    # in QtDesigner.
    actionChoose = mainWindow.actionChoose
    actionQuit = mainWindow.actionQuit
    actionFit = mainWindow.action_Fit_to_Window
    actionZoomIn = mainWindow.actionZoom_In
    actionZoomOut = mainWindow.actionZoom_Out
    actionRotateRight = mainWindow.action_Rotate_Right
    actionRotateLeft = mainWindow.action_Rotate_Left
    scrollArea = mainWindow.scrollArea
    imageArea = mainWindow.imageLabel
    statusBar = mainWindow.statusBar()
    statusBarLabel = QtGui.QLabel('')
    statusBar.addWidget(statusBarLabel)

    # Change the resize event so that the preloaded images are
    # resized.
    originalResizeEvent = scrollArea.resizeEvent
    def f(event):
        originalResizeEvent(event)
        viewportSize = scrollArea.maximumViewportSize()
        internalState.rescale_images(viewportSize)
    scrollArea.resizeEvent = f

    # TODO: Find a nice icon that I'm allowed to use.
    # mainWindow.setWindowIcon(QtGui.QIcon('./img/camera.jpg'))

    # Here signal-slot connections are added manually.
    actionChoose.connect(actionChoose, QtCore.SIGNAL('triggered()'),
                         choose_images_to_keep)
    actionQuit.connect(actionQuit, QtCore.SIGNAL('triggered()'),
                       QtGui.qApp, QtCore.SLOT('quit()'))
    actionFit.connect(actionFit, QtCore.SIGNAL('triggered()'), fit_image)
    actionZoomIn.connect(actionZoomIn, QtCore.SIGNAL('triggered()'), zoom_in)
    actionZoomOut.connect(actionZoomOut, QtCore.SIGNAL('triggered()'), zoom_out)
    actionRotateRight.connect(actionRotateRight, QtCore.SIGNAL('triggered()'),
                              rotate_image_right)
    actionRotateLeft.connect(actionRotateLeft, QtCore.SIGNAL('triggered()'),
                             rotate_image_left)
    nextImage = QtGui.QShortcut('N',mainWindow)
    nextImage.connect(nextImage, QtCore.SIGNAL('activated()'), show_next_image)
    nextImage = QtGui.QShortcut('B',mainWindow)
    nextImage.connect(nextImage, QtCore.SIGNAL('activated()'),
                      show_previous_image)
    nextImage = QtGui.QShortcut('D',mainWindow)
    nextImage.connect(nextImage, QtCore.SIGNAL('activated()'), discard_image)
    
    internalState = InternalState()
    clear() #Put the program in its beginning state.
    mainWindow.show()
    sys.exit(app.exec_())
