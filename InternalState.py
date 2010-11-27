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

from ImageLoader import ImageLoader, scale_image
from InternalException import InternalException

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

alreadyInstantiated = False

class PreFetcher():
    def __init__(self, filename_image, viewportSize_imageScaled,
                 matrix=QtGui.QMatrix()):

        if isinstance(filename_image, QtGui.QPixmap) \
                 and isinstance(viewportSize_imageScaled, QtGui.QPixmap):
            self.image = filename_image
            self.imageScaled = viewportSize_imageScaled
            self.fromLoader = False
            self.rescale = False
        elif isinstance(filename_image, QtCore.QString) \
               and isinstance(viewportSize_imageScaled, QtCore.QSize):
            self.loader = ImageLoader(filename_image, viewportSize_imageScaled,
                                      matrix)
            self.loader.start()
            self.fromLoader = True
            self.rescale = False
        else:
            raise InternalException('Incorrect PreFetcher contructor.')

    def getImages(self):
        if self.fromLoader:
            self.loader.join()
            self.image = QtGui.QPixmap.fromImage(self.loader.image)
            self.imageScaled = QtGui.QPixmap.fromImage(self.loader.imageScaled)
            self.fromLoader = False

        if self.rescale:
            self.imageScaled = scale_image(self.image, self.rescalePath,
                                           self.rescaleViewportSize,
                                           self.rescaleMatrix)
        
        return (self.image, self.imageScaled)

    def rescale(self, path, viewportSize, matrix=QtGui.QMatrix()):
        self.rescale = True
        self.rescalePath = path
        self.rescaleViewportSize = viewportSize
        self.rescaleMatrix = matrix

    def set_scaled_image(self, newImage):
        if not self.fromLoader:
            self.imageScaled = newImage
            

class InternalState:
    def __init__(self):
        global alreadyInstantiated
        if alreadyInstantiated:
            raise InternalException('InternalState instantiated more than one '
                                    + 'time. '
                                    + 'It should be treated as a singleton.')
        else:            
            alreadyInstantiated = True
            self.reset()

    def reset(self):
        self.imagesList = []
        self.transformations = {}
        self.pos = -1
        self.movingForward = True
        self.recentlyRescaled = False

        # These should later become pre-fetchers
        self.previousPic = None
        self.currentPic = None
        self.nextPic = None

    
    def is_at_last_position(self):
        return self.pos == len(self.imagesList) - 1

    def is_at_first_position(self):
        return self.pos == 0

    def get_current_image_number(self):
        return self.pos + 1

    def get_total_number_images(self):
        return len(self.imagesList)

    def make_path_fetcher(self, path, viewportSize):
        if path in self.transformations:
            return PreFetcher(path, viewportSize, self.transformations[path])
        else:
            return PreFetcher(path, viewportSize)

    def next_image(self, viewportSize):
        self.pos += 1
        
        if (self.pos >= len(self.imagesList)):
            self.pos = len(self.imagesList) - 1
            return

        self.previousPic = self.currentPic

        self.currentPic = self.nextPic
        if self.recentlyRescaled:
            self.recentlyRescaled = False
            self.currentPicScaled = self.currentPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)

        if self.pos < len(self.imagesList) - 1:
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.nextPic = self.make_path_fetcher(path, viewportSize)
        
    def previous_image(self, viewportSize):
        self.pos -= 1
        
        if (self.pos < 0):
            self.pos = 0
            return

        self.nextPic = self.currentPic

        self.currentPic = self.previousPic
        if self.recentlyRescaled:
            self.recentlyRescaled = False
            self.currentPicScaled = self.currentPic.scaled(
                viewportSize, QtCore.Qt.KeepAspectRatio)

        if self.pos > 0:
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.previousPic = self.make_path_fetcher(path, viewportSize)
        
    def image_available(self):
        return not len(self.imagesList) == 0

    def current_image(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')
        
        (res,_) = self.currentPic.getImages()
        return res

    def current_image_scaled(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        (_,res) = self.currentPic.getImages()
        return res

    def set_scaled_image(self, newImage):
        self.currentPic.set_scaled_image(newImage)

    def rescale_images(self, viewportSize):
        if not self.image_available():
            return
        
        self.recentlyRescaled = True

        def rescale(fetcher, pos):
            path = self.current_image_complete_path_pos(pos)
            if path in self.transformations:
                fetcher.rescale(path, viewportSize, self.transformations[path])
            else:
                fetcher.rescale(path, viewportSize)

        if self.previousPic is not None and self.pos > 0:
            rescale(self.previousPic, pos - 1)
            
        if self.currentPic is not None:
            rescale(self.currentPic, self.pos)
            
        if self.nextPic is not None  and self.pos < len(self.imagesList) - 1:
            rescale(self.nextPic, self.pos + 1)
        
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

        # currentPic being invalid can only cause problems...
        self.currentPic = PreFetcher(QtGui.QPixmap(), QtGui.QPixmap())

        path = self.current_image_complete_path_pos(0)
        self.nextPic = self.make_path_fetcher(path, viewportSize)

    def discard_current_image(self, viewportSize):
        del self.imagesList[self.pos]
        
        if len(self.imagesList) == 0:
            self.reset()
            return

        if self.pos >= len(self.imagesList):
            self.previous_image(viewportSize)
        else:
            self.pos -= 1
            if self.movingForward:
                previousPic = QtGui.QPixmap(self.previousPic)
                previousPicScaled = QtGui.QPixmap(self.previousPicScaled)
            else:
                self.loader.join()
                previousPic = QtGui.QPixmap.fromImage(self.loader.image)
                previousPicScaled = QtGui.QPixmap.fromImage(self.loader.
                                                            imageScaled)
            self.next_image(viewportSize)
            self.previousPic = previousPic
            self.previousPicScaled = previousPicScaled

