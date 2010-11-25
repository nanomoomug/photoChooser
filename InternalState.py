#!/usr/bin/env python
"""
A class to represent the internal state of the program.

The internal state keeps track of:
- A list will all the loaded images.
- The position of the current image being shown in the list.
- A copy of the current image being shown, untouched.
- A scaled version of the current image.
- The same for the next image or the previous image, depending on the last
  operation having been 'next image' or 'previous image'
- The transformations(rotations) that where performed on the images.

The images are never fetched locally, they are always loaded using
'ImageLoader'.
"""

from ImageLoader import *

import os
from PyQt4 import QtGui, QtCore

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

class InternalState:
    def __init__(self):
        self.imagesList = []
        self.transformations = {}
        self.pos = -1
        self.movingForward = True
        self.recentlyRescaled = False

        self.previousPic = QtGui.QPixmap()
        self.previousPicScaled = QtGui.QPixmap()
        self.currentPic = QtGui.QPixmap()
        self.currentPicScaled = QtGui.QPixmap()
        self.nextPic = QtGui.QPixmap()
        self.nextPicScaled = QtGui.QPixmap()
    
    def isAtLastPosition(self):
        return self.pos == len(self.imagesList) - 1

    def isAtFirstPosition(self):
        return self.pos == 0

    def getCurrentImageNumber(self):
        return self.pos + 1

    def getTotalNumberImages(self):
        return len(self.imagesList)

    def startNextLoader(self, path, viewportSize):
        if path in self.transformations:
            self.loader = ImageLoader(path, viewportSize,
                                      self.transformations[path])
        else:
            self.loader = ImageLoader(path, viewportSize)
        self.loader.start()

    def nextImage(self, viewportSize):
        self.pos += 1
        if (self.pos >= len(self.imagesList)):
            self.pos = len(self.imagesList) - 1
            return
        self.previousPic = self.currentPic
        self.previousPicScaled = self.currentPicScaled
        if self.movingForward:
            self.loader.join()
            self.currentPic = QtGui.QPixmap.fromImage(self.loader.image)
            self.currentPicScaled = QtGui.QPixmap.fromImage(self.loader.
                                                            imageScaled)
            if self.recentlyRescaled:
                self.recentlyRescaled = False
                self.currentPicScaled = self.currentPic.scaled(
                    viewportSize, QtCore.Qt.KeepAspectRatio)
        else:
            self.currentPic = self.nextPic
            self.currentPicScaled = self.nextPicScaled
        if (self.pos < len(self.imagesList) - 1):
            path = self.currentImageCompletePathPos(self.pos + 1)
            self.startNextLoader(path, viewportSize)
        self.movingForward = True

    def previousImage(self, viewportSize):
        self.pos -= 1
        if (self.pos < 0):
            self.pos = 0
            return
        self.nextPic = self.currentPic
        self.nextPicScaled = self.currentPicScaled
        if not self.movingForward:
            self.loader.join()
            self.currentPic = QtGui.QPixmap.fromImage(self.loader.image)
            self.currentPicScaled = QtGui.QPixmap.fromImage(self.loader.
                                                            imageScaled)
            if self.recentlyRescaled:
                self.recentlyRescaled = False
                self.currentPicScaled = self.currentPic.scaled(
                    viewportSize, QtCore.Qt.KeepAspectRatio)
        else:
            self.currentPic = self.previousPic
            self.currentPicScaled = self.previousPicScaled
        if (self.pos > 0):
            path = self.currentImageCompletePathPos(self.pos - 1)
            self.startNextLoader(path, viewportSize)
        self.movingForward = False

    def imageAvailable(self):
        return not len(self.imagesList) == 0

    def currentImage(self):
        if not self.imageAvailable():
            raise InternalException('There is no image available to be loaded.')
        return self.currentPic

    def currentImageScaled(self):
        if not self.imageAvailable():
            raise InternalException('There is no image available to be loaded.')
        return self.currentPicScaled

    def setScaledImage(self, newImage):
        self.currentPicScaled = newImage

    def rescaleImages(self, viewportSize):
        self.recentlyRescaled = True
        if not self.currentPic.isNull():
            self.currentPicScaled = self.currentPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)
        if not self.previousPic.isNull():
            self.previousPicScaled = self.previousPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)
        if not self.nextPic.isNull():
            self.nextPicScaled = self.nextPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)

    def currentImageCompletePath(self):
         return self.currentImageCompletePathPos(self.pos)

    def currentImageCompletePathPos(self, pos):
        if not self.imageAvailable():
            raise InternalException('There is no image available to be loaded.')
        (dir,f) = self.imagesList[pos]
        return dir + '/' + f

    def currentDirectory(self):
        (d,_) = self.imagesList[self.pos]
        return d

    def currentImageName(self):
        (_,n) = self.imagesList[self.pos]
        return n

    # I got this list from the Qt documentation.
    imgExtensions = ['.jpg','.jpeg','.bmp','.gif','.png',
                     '.ppm','.pmb','.pgm','.xbm','.xpm']
    def getImagesList(self, dir):
        allList = os.listdir(dir)
        selected = filter(lambda x:
                          any(map(lambda y:
                                  x.lower().endswith(y), self.imgExtensions)),
                          allList)
        return map(lambda x: (dir,x), selected)

    def start(self, dirList, viewportSize):
        self.imagesList = []
        for f in dirList:
            if os.path.isdir(f):
                self.imagesList.extend(self.getImagesList(f))
        self.pos = -1
        if len(self.imagesList) == 0:
            return
        self.startNextLoader(self.currentImageCompletePathPos(0), viewportSize)
        self.movingForward = True

    def removeCurrentImage(self, viewportSize):
        lastPosDel = self.pos == len(self.imagesList) - 1
        self.imagesList.pop(self.pos)
        if self.pos == len(self.imagesList):
            if len(self.imagesList) == 0:
                self.__init__()
                return
            self.pos = len(self.imagesList) - 1
        if lastPosDel:
            self.currentPic = self.previousPic
            self.currentPicScaled = self.previousPicScaled
            fileName = self.currentImageCompletePathPos(self.pos - 1)
            self.previousPic = QtGui.QPixmap(fileName)
            self.previousPicScaled = self.previousPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)
            self.nextPic = QtGui.QPixmap()
        else:
            self.currentPic = self.previousPic
            self.currentPicScaled = self.previousPicScaled
            self.pos -= 1
            self.nextImage(viewportSize)
