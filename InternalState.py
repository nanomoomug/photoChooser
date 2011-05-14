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

from ImageLoader import ImageLoader, scale_and_rotate_image, rotate_image
from InternalException import InternalException

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

class PreFetcher():
    class RescaleInfo:
        def __init__(self):
            self.rescale_path = None
            self.rescale_viewport_size = None
            self.rescale_matrix = None    
    
    def __init__(self, filename_image, viewportSize_imageScaled,
                 matrix=QtGui.QMatrix()):

        # This variables are needed later to handle rescaling.
        self.rescale_info = PreFetcher.RescaleInfo()

        if isinstance(filename_image, QtGui.QPixmap) \
               and isinstance(viewportSize_imageScaled, QtGui.QPixmap):
            self.image = filename_image
            self.image_scaled = viewportSize_imageScaled
            self.from_loader = False
            self.to_rescale = False
        elif (isinstance(filename_image, QtCore.QString) or \
                 isinstance(filename_image, str)) \
               and isinstance(viewportSize_imageScaled, QtCore.QSize):
            self.loader = ImageLoader(filename_image, viewportSize_imageScaled,
                                      matrix)
            self.loader.start()
            self.from_loader = True
            self.to_rescale = False
        else:
            msg = 'Incorrect PreFetcher contructor: ' + \
                  str(type(filename_image)) + ', ' + \
                  str(type(viewportSize_imageScaled))
            raise InternalException(msg)

    def get_images(self):
        if self.from_loader:
            self.loader.join()
            self.image = QtGui.QPixmap.fromImage(self.loader.image)
            self.image_scaled = QtGui.QPixmap.fromImage(self.loader.imageScaled)
            self.from_loader = False

        if self.to_rescale:
            self.image_scaled = scale_and_rotate_image(
                self.image,
                self.rescale_info.rescale_path,
                self.rescale_info.rescale_viewport_size,
                self.rescale_info.rescale_matrix)
            self.to_rescale = False

        return (self.image, self.image_scaled)

    def get_rotated_image(self, path, matrix=QtGui.QMatrix()):
        (image,_) = self.get_images()
        return rotate_image(image, path, matrix)

    def rescale(self, path, viewport_size, matrix=QtGui.QMatrix()):
        self.to_rescale = True
        self.rescale_info.rescale_path = path
        self.rescale_info.rescale_viewport_size = viewport_size
        self.rescale_info.rescale_matrix = matrix

    def set_scaled_image(self, new_image):
        if not self.from_loader:
            self.image_scaled = new_image

ALREADY_INSTANTIATED = False #global variable to force singleton.
class InternalState:
    def __init__(self):
        global ALREADY_INSTANTIATED
        if ALREADY_INSTANTIATED:
            raise InternalException('InternalState instantiated more than one '
                                    + 'time. '
                                    + 'It should be treated as a singleton.')
        else:
            ALREADY_INSTANTIATED = True
            self.reset()

    def reset(self):
        self.imagesList = []
        self.transformations = {}
        self.pos = -1
        self.movingForward = True
        self.recentlyRescaled = False

        self.history = []
        self.forwardHistory = []

        # These should later become pre-fetchers
        self.previousPic = None
        self.currentPic = None
        self.nextPic = None

    def reset_transformation(self, path):
        del self.transformations[path]

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
            path = self.current_image_complete_path()
            self.currentPic.rescale(path, viewportSize)

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
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.currentPic.rescale(path, viewportSize)

        if self.pos > 0:
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.previousPic = self.make_path_fetcher(path, viewportSize)

    def add_image(self, path, filename, pos, viewportSize):
        self.imagesList.insert(pos, (path,filename))
        self.jump_to_image(pos, viewportSize)

    def jump_to_image(self, newPos, viewportSize):
        if newPos < 0 or newPos >= len(self.imagesList):
            return

        self.pos = newPos

        if self.pos - 1 >= 0:
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.previousPic = self.make_path_fetcher(path, viewportSize)

        path = self.current_image_complete_path_pos(self.pos)
        self.currentPic = self.make_path_fetcher(path, viewportSize)

        if self.pos + 1 < len(self.imagesList):
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.nextPic = self.make_path_fetcher(path, viewportSize)

    def image_available(self):
        return not len(self.imagesList) == 0

    def current_image(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        (res,_) = self.currentPic.get_images()
        return res

    def current_image_scaled_and_rotated(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        (_,res) = self.currentPic.get_images()
        return res

    def current_image_rotated(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        path = self.current_image_complete_path()
        if path in self.transformations:
            return self.currentPic.get_rotated_image(path,
                                                   self.transformations[path])
        else:
            return self.currentPic.get_rotated_image(path)

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
            rescale(self.previousPic, self.pos - 1)

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
        # I got this list from the Qt documentation of QImage:
        #http://doc.qt.nokia.com/4.7/qimage.html#reading-and-writing-image-files
        imgExtensions = ['.jpg','.jpeg','.bmp','.gif','.png',
                         '.ppm','.pmb','.pgm','.xbm','.xpm']

        dir = str(dir)

        list = os.listdir(dir)
        list = map(lambda x: dir + '/' + x, list)
        directories = filter(os.path.isdir, list)
        directories = filter(lambda x: not x.endswith('discarded'),
                             directories)
        files = filter(os.path.isfile, list)
        
        selected = filter(lambda x:
                          any(map(lambda y: x.lower().endswith(y),
                                  imgExtensions)), files)
        newImages = map(os.path.split, selected)
        self.imagesList.extend(newImages)

        for f in directories:
            self.get_images_list(f)

    def start(self, dirList, viewportSize):
        self.imagesList = []

        for f in dirList:
            self.get_images_list(f)

        self.pos = -1

        if len(self.imagesList) == 0:
            return

        # currentPic being invalid can only cause problems...
        self.previousPic = PreFetcher(QtGui.QPixmap(), QtGui.QPixmap())
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
            self.currentPic = self.nextPic
            if self.pos < len(self.imagesList) - 1:
                path = self.current_image_complete_path_pos(self.pos + 1)
                self.nextPic = self.make_path_fetcher(path, viewportSize)

    def rotate_current_image(self, degrees, viewportSize):
        name = self.current_image_complete_path()
        if name in self.transformations:
            matrix = self.transformations[name]
        else:
            matrix = QtGui.QMatrix()
        matrix.rotate(degrees)
        pix = self.current_image()
        transformed = pix.transformed(matrix).scaled(viewportSize,
                                                     QtCore.Qt.KeepAspectRatio)

        self.set_scaled_image(transformed)
        self.transformations[name] = matrix

    def add_to_history(self, action):
        self.history.insert(0, action)

    def add_to_forward_history(self, action):
        self.forwardHistory.insert(0, action)

    def clear_forward_history(self):
        self.forwardHistory = []

    def undo(self, viewportSize):
        if len(self.history) == 0:
            return

        action = self.history[0]
        del self.history[0]
        action.undo(viewportSize)
        self.add_to_forward_history(action)

    def redo(self, viewportSize):
        if len(self.forwardHistory) == 0:
            return

        action = self.forwardHistory[0]
        del self.forwardHistory[0]
        action.redo(viewportSize)
        self.add_to_history(action)
