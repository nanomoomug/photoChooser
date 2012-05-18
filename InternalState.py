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
__license__ = "MIT"
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

        # These variables are needed later to handle rescaling.
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
            self.image_scaled = QtGui.QPixmap.fromImage(self.loader.image_scaled)
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
        (image, _) = self.get_images()
        return rotate_image(image, path, matrix)

    def rescale(self, path, viewport_size, matrix=QtGui.QMatrix()):
        self.to_rescale = True
        self.rescale_info.rescale_path = path
        self.rescale_info.rescale_viewport_size = viewport_size
        self.rescale_info.rescale_matrix = matrix

    def set_image(self, new_image):
        if not self.from_loader:
            self.image = new_image

    def set_scaled_image(self, new_image):
        if not self.from_loader:
            self.image_scaled = new_image

ALREADY_INSTANTIATED = False #global variable to force singleton.
class InternalState:
    def __init__(self):
        # All these variables should be instantiated by calling self.reset()
        self.images_list = None
        self.images_list = None
        self.transformations = None
        self.pos = None
        self.recently_rescaled = None
        self.history = None
        self.forward_history = None
        self.previous_pic = None
        self.current_pic = None
        self.next_pic = None
        
        global ALREADY_INSTANTIATED
        if ALREADY_INSTANTIATED:
            raise InternalException('InternalState instantiated more than one '
                                    + 'time. '
                                    + 'It should be treated as a singleton.')
        else:
            ALREADY_INSTANTIATED = True
            self.reset()

    def reset(self):
        self.images_list = []
        self.transformations = {}
        self.pos = -1
        self.recently_rescaled = False

        self.history = []
        self.forward_history = []

        # These should later become pre-fetchers
        self.previous_pic = None
        self.current_pic = None
        self.next_pic = None

    def reset_transformation(self, path):
        del self.transformations[path]

    def is_at_last_position(self):
        return self.pos == len(self.images_list) - 1

    def is_at_first_position(self):
        return self.pos == 0

    def get_current_image_number(self):
        return self.pos + 1

    def get_total_number_images(self):
        return len(self.images_list)

    def make_path_fetcher(self, path, viewport_size):
        if path in self.transformations:
            return PreFetcher(path, viewport_size, self.transformations[path])
        else:
            return PreFetcher(path, viewport_size)

    def next_image(self, viewport_size):
        self.pos += 1

        if (self.pos >= len(self.images_list)):
            self.pos = len(self.images_list) - 1
            return

        self.previous_pic = self.current_pic

        self.current_pic = self.next_pic
        if self.recently_rescaled:
            self.recently_rescaled = False
            path = self.current_image_complete_path()
            self.current_pic.rescale(path, viewport_size)

        if self.pos < len(self.images_list) - 1:
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.next_pic = self.make_path_fetcher(path, viewport_size)

    def previous_image(self, viewport_size):
        self.pos -= 1

        if (self.pos < 0):
            self.pos = 0
            return

        self.next_pic = self.current_pic

        self.current_pic = self.previous_pic
        if self.recently_rescaled:
            self.recently_rescaled = False
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.current_pic.rescale(path, viewport_size)

        if self.pos > 0:
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.previous_pic = self.make_path_fetcher(path, viewport_size)

    def add_image(self, path, filename, pos, viewport_size):
        self.images_list.insert(pos, (path, filename))
        self.jump_to_image(pos, viewport_size)

    def jump_to_image(self, new_pos, viewport_size):
        if new_pos < 0 or new_pos >= len(self.images_list):
            return

        self.pos = new_pos

        if self.pos - 1 >= 0:
            path = self.current_image_complete_path_pos(self.pos - 1)
            self.previous_pic = self.make_path_fetcher(path, viewport_size)

        path = self.current_image_complete_path_pos(self.pos)
        self.current_pic = self.make_path_fetcher(path, viewport_size)

        if self.pos + 1 < len(self.images_list):
            path = self.current_image_complete_path_pos(self.pos + 1)
            self.next_pic = self.make_path_fetcher(path, viewport_size)

    def image_available(self):
        return not len(self.images_list) == 0

    def current_image(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        (res, _) = self.current_pic.get_images()
        return res

    def current_image_scaled_and_rotated(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        (_, res) = self.current_pic.get_images()
        return res

    def current_image_rotated(self):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')

        path = self.current_image_complete_path()
        if path in self.transformations:
            return self.current_pic.get_rotated_image(
                path,
                self.transformations[path])
        else:
            return self.current_pic.get_rotated_image(path)

    def set_image(self, new_image):
        self.current_pic.set_image(new_image)

    def set_scaled_image(self, new_image):
        self.current_pic.set_scaled_image(new_image)

    def rescale_images(self, viewport_size):
        if not self.image_available():
            return

        self.recently_rescaled = True

        def rescale(fetcher, pos):
            path = self.current_image_complete_path_pos(pos)
            if path in self.transformations:
                fetcher.rescale(path, viewport_size, self.transformations[path])
            else:
                fetcher.rescale(path, viewport_size)

        if self.previous_pic is not None and self.pos > 0:
            rescale(self.previous_pic, self.pos - 1)

        if self.current_pic is not None:
            rescale(self.current_pic, self.pos)

        if self.next_pic is not None  and self.pos < len(self.images_list) - 1:
            rescale(self.next_pic, self.pos + 1)

    def current_image_complete_path(self):
        return self.current_image_complete_path_pos(self.pos)

    def current_image_complete_path_pos(self, pos):
        if not self.image_available():
            raise InternalException('There is no image available to be loaded.')
        (d, f) = self.images_list[pos]
        return d + '/' + f

    def current_directory(self):
        (d, _) = self.images_list[self.pos]
        return d

    def current_image_name(self):
        (_, n) = self.images_list[self.pos]
        return n

    def get_images_list(self, directory):
        # I got this list from the Qt documentation of QImage:
        #http://doc.qt.nokia.com/4.7/qimage.html#reading-and-writing-image-files
        img_extensions = ['.jpg', '.jpeg', '.bmp', '.gif', '.png',
                          '.ppm', '.pmb', '.pgm', '.xbm', '.xpm']

        directory = str(directory)

        dir_list = os.listdir(directory)
        dir_list = [directory + '/' + x for x in dir_list]
        directories = filter(os.path.isdir, dir_list)
        directories = [x for x in directories if not x.endswith('discarded')]
        files = filter(os.path.isfile, dir_list)

        selected = [x for x in files
                    if any([x.lower().endswith(y) for y in img_extensions])]
        new_images = map(os.path.split, selected)
        self.images_list.extend(new_images)

        for f in directories:
            self.get_images_list(f)

    def start(self, dir_list, viewport_size):
        self.images_list = []

        for f in dir_list:
            self.get_images_list(f)

        self.pos = -1

        if len(self.images_list) == 0:
            return

        # currentPic being invalid can only cause problems...
        self.previous_pic = PreFetcher(QtGui.QPixmap(), QtGui.QPixmap())
        self.current_pic = PreFetcher(QtGui.QPixmap(), QtGui.QPixmap())

        path = self.current_image_complete_path_pos(0)
        self.next_pic = self.make_path_fetcher(path, viewport_size)

    def discard_current_image(self, viewport_size):
        del self.images_list[self.pos]

        if len(self.images_list) == 0:
            self.reset()
            return

        if self.pos >= len(self.images_list):
            self.previous_image(viewport_size)
        else:
            self.current_pic = self.next_pic
            if self.pos < len(self.images_list) - 1:
                path = self.current_image_complete_path_pos(self.pos + 1)
                self.next_pic = self.make_path_fetcher(path, viewport_size)

    def rotate_current_image(self, degrees, viewport_size):
        name = self.current_image_complete_path()
        if name in self.transformations:
            matrix = self.transformations[name]
        else:
            matrix = QtGui.QMatrix()
        matrix.rotate(degrees)
        pix = self.current_image()
        transformed = pix.transformed(matrix).scaled(viewport_size,
                                                     QtCore.Qt.KeepAspectRatio)

        self.set_scaled_image(transformed)
        self.transformations[name] = matrix

    def add_to_history(self, action):
        self.history.insert(0, action)

    def add_to_forward_history(self, action):
        self.forward_history.insert(0, action)

    def clear_forward_history(self):
        self.forward_history = []

    def undo(self, viewport_size):
        if len(self.history) == 0:
            return

        action = self.history[0]
        del self.history[0]
        action.undo(viewport_size)
        self.add_to_forward_history(action)

    def redo(self, viewport_size):
        if len(self.forward_history) == 0:
            return

        action = self.forward_history[0]
        del self.forward_history[0]
        action.redo(viewport_size)
        self.add_to_history(action)
