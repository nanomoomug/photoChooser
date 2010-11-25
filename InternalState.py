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
import os

from PyQt4 import QtGui, QtCore

from ImageLoader import ImageLoader

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
    
    def is_at_last_position(self):
        return self.pos == len(self.imagesList) - 1

    def is_at_first_position(self):
        return self.pos == 0

    def get_current_image_number(self):
        return self.pos + 1

    def get_total_number_images(self):
        return len(self.imagesList)

    def start_next_loader(self, path, viewportSize):
        if path in self.transformations:
            self.loader = ImageLoader(path, viewportSize,
                                      self.transformations[path])
        else:
            self.loader = ImageLoader(path, viewportSize)
        self.loader.start()

    def next_image(self, viewportSize):
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
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.start_next_loader(path, viewportSize)
        self.movingForward = True

    def previous_image(self, viewportSize):
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
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.start_next_loader(path, viewportSize)
        self.movingForward = False

    def image_available(self):
        return not len(self.imagesList) == 0

    def current_image(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')
        return self.currentPic

    def current_image_scaled(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')
        return self.currentPicScaled

    def set_scaled_image(self, newImage):
        self.currentPicScaled = newImage

    def rescale_images(self, viewportSize):
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

    def current_image_complete_path(self):
         return self.current_image_complete_path_pos(self.pos)

    def current_image_complete_path_pos(self, pos):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')
        (dir,f) = self.imagesList[pos]
        return dir + '/' + f

    def current_directory(self):
        (d,_) = self.imagesList[self.pos]
        return d

    def current_image_name(self):
        (_,n) = self.imagesList[self.pos]
        return n

    
    def get_images_list(self, dir):
        # I got this list from the Qt documentation.
        imgExtensions = ['.jpg','.jpeg','.bmp','.gif','.png',
                         '.ppm','.pmb','.pgm','.xbm','.xpm']
        allList = os.listdir(dir)
        selected = filter(lambda x:
                          any(map(lambda y:
                                  x.lower().endswith(y), imgExtensions)),
                          allList)
        return map(lambda x: (dir,x), selected)

    def start(self, dirList, viewportSize):
        self.imagesList = []
        for f in dirList:
            if os.path.isdir(f):
                self.imagesList.extend(self.get_images_list(f))
        self.pos = -1
        if len(self.imagesList) == 0:
            return
        self.start_next_loader(self.current_image_complete_path_pos(0),
                                viewportSize)
        self.movingForward = True

    def remove_current_image(self, viewportSize):
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
            fileName = self.current_image_complete_path_pos(self.pos - 1)
            self.previousPic = QtGui.QPixmap(fileName)
            self.previousPicScaled = self.previousPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)
            self.nextPic = QtGui.QPixmap()
        else:
            self.currentPic = self.previousPic
            self.currentPicScaled = self.previousPicScaled
            self.pos -= 1
            self.next_image(viewportSize)
