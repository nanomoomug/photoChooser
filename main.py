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

from InternalException import *
from InternalState import *

import sys
import os
import shutil
from PyQt4 import QtGui, QtCore
from PyQt4 import uic

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

### Load the main window object created with QtDesigner.
app = QtGui.QApplication(sys.argv)
mainWindow = uic.loadUi('./qt/mainWindow.ui')

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
    internalState.rescaleImages(viewportSize)
scrollArea.resizeEvent = f

# TODO: Find a nice icon that I'm allowed to use.
# mainWindow.setWindowIcon(QtGui.QIcon('./img/camera.jpg'))



# A global dialog to select files.
fileDialog = QtGui.QFileDialog(mainWindow)
fileDialog.setFileMode(QtGui.QFileDialog.Directory)
listView = fileDialog.findChild(QtGui.QListView,'listView')
listView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

### Define some function that make up the functionality of the program.
def showImage():
    if not internalState.imageAvailable():
        return
    image = internalState.currentImageScaled()
    imageArea.setPixmap(image)
    text = "" + internalState.currentImageCompletePath()
    pos = internalState.getCurrentImageNumber()
    total = internalState.getTotalNumberImages()
    text += '  [' + str(pos) + '/' + str(total) + ']'
    statusBarLabel.setText(text)

def fitImage():
    if not internalState.imageAvailable():
        return
    pix = internalState.currentImage()
    imageArea.setPixmap(pix.scaled(scrollArea.maximumViewportSize(),
                                   QtCore.Qt.KeepAspectRatio))

def zoom(scaleFactor):
    if not internalState.imageAvailable():
        return
    pix = internalState.currentImage()
    newSize = imageArea.size() * scaleFactor
    imageArea.setPixmap(pix.scaled(newSize, QtCore.Qt.KeepAspectRatio))
    newSize = imageArea.pixmap().size()
    scrollArea.ensureVisible(newSize.width()/2.0,newSize.height()/2.0,
                             scrollArea.maximumViewportSize().width()/2.0,
                             scrollArea.maximumViewportSize().height()/2.0)

def zoomIn():
    zoom(1.25)

def zoomOut():
    zoom(0.8)

def showNextImage():
    internalState.nextImage(scrollArea.maximumViewportSize())
    showImage()

def showPreviousImage():
    internalState.previousImage(scrollArea.maximumViewportSize())
    showImage()

def discardImage():
    if not internalState.imageAvailable():
        return
    
    cd = internalState.currentDirectory();
    if not os.path.exists(cd + '/discarded'):
        os.mkdir(cd + '/discarded')
    if not os.path.isdir(cd + '/discarded'):
        raise InternalException('A file named discarded was found. ' +
                                'A folder of that name to move the photos' +
                                'to could not be created.')
    shutil.move(internalState.currentImageCompletePath(),
                cd + '/discarded/' + internalState.currentImageName())
    internalState.removeCurrentImage(scrollArea.maximumViewportSize())
    if internalState.imageAvailable():
        showImage()
    else:
        clear()

def clear():
    imageArea.clear()
    statusBarLabel.clear()
    imageArea.setText('No images loaded...')

def rotateImage(degrees):
    name = internalState.currentImageCompletePath()
    if name in internalState.transformations:
        matrix = internalState.transformations[name]
    else:
        matrix = QtGui.QMatrix()
    matrix.rotate(degrees)
    pix = internalState.currentImage()
    transformed = pix.transformed(matrix).scaled(
        scrollArea.maximumViewportSize(),
        QtCore.Qt.KeepAspectRatio)
    imageArea.setPixmap(transformed)

    internalState.setScaledImage(transformed)
    internalState.transformations[name] = matrix

def rotateImageRight():
    rotateImage(90)

def rotateImageLeft():
    rotateImage(-90)

# Ask the user to select a direcory and save it in 'internalState.directory'.
def chooseImagesToKeep():
    if not fileDialog.exec_():
        return

    res = fileDialog.selectedFiles()
    internalState.start(res, scrollArea.maximumViewportSize())
    showNextImage()

# Here signal-slot connections are added manually.
actionChoose.connect(actionChoose, QtCore.SIGNAL('triggered()'),
                     chooseImagesToKeep)
actionQuit.connect(actionQuit, QtCore.SIGNAL('triggered()'),
                   QtGui.qApp, QtCore.SLOT('quit()'))
actionFit.connect(actionFit, QtCore.SIGNAL('triggered()'), fitImage)
actionZoomIn.connect(actionZoomIn, QtCore.SIGNAL('triggered()'), zoomIn)
actionZoomOut.connect(actionZoomOut, QtCore.SIGNAL('triggered()'), zoomOut)
actionRotateRight.connect(actionRotateRight, QtCore.SIGNAL('triggered()'),
                          rotateImageRight)
actionRotateLeft.connect(actionRotateLeft, QtCore.SIGNAL('triggered()'),
                         rotateImageLeft)
nextImage = QtGui.QShortcut('N',mainWindow)
nextImage.connect(nextImage, QtCore.SIGNAL('activated()'), showNextImage)
nextImage = QtGui.QShortcut('B',mainWindow)
nextImage.connect(nextImage, QtCore.SIGNAL('activated()'), showPreviousImage)
nextImage = QtGui.QShortcut('D',mainWindow)
nextImage.connect(nextImage, QtCore.SIGNAL('activated()'), discardImage)

# The lines that follow could be seen as the main function.
internalState = InternalState()
clear() #Put the program in its beginning state.
mainWindow.show()
sys.exit(app.exec_())
