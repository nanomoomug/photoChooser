#!/usr/bin/env python
"""
A threaded ImageLoader.

A threaded image loader. It will do two things:
1. Load a 'QImage' into 'self.image' that is the exact image that was read from
   the filname given in the constructor.
2. It will make a copy of the read 'self.image', attempt to read the Exif
   metadata of the image file, get the orientation from the metadata, rotate the
   image accordingly and finaly scale it the size of the viewport. The size of
   the viewport must also be passed as an argument to the constructor. The
   transformed image will be put in 'self.scaledImage'. A transformation matrix
   can be passed and it will be used too.

The reason why QImage is used and not QPixmap ---even though it may have to be
converted later to QPixmap to be shown--- is that QPixmap can not be used
outside of the main thread.

Some of the functions that ImageLoader uses are useful in other places aswell.
Thus these functions are not part of the ImageLoader, but are global functions.
"""

from threading import Thread

from PyQt4 import QtGui, QtCore
import pyexiv2

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

def scale_and_rotate_image(to_scale, filename, maximum_viewport_size,
                           matrix=QtGui.QMatrix()):
    """Returns a scaled and rotated version of an image.

    Keyword Arguments:
    to_scale -- The image to be scaled.
    filename -- The file path to the image.
    maximum_viewport_size -- The size to which the image has to be scaled.
    matrix -- A transformation matrix (default is identity)
    """
    to_scale = rotate_image(to_scale, filename, matrix)
    
    return to_scale.scaled(maximum_viewport_size, QtCore.Qt.KeepAspectRatio)

def rotate_image(to_rotate, filename, matrix=QtGui.QMatrix()):
    """Return a rotated version of an image.

    The transformation matrix is given as an argument.

    Keyword Arguments:
    to_rotate -- The image to be rotated.
    filename -- The file path to the image.
    matrix -- A transformation matrix (default is identity)
    """
    metadata = pyexiv2.metadata.ImageMetadata(str(filename))
    metadata.read()
    
    if 'Exif.Image.Orientation' in metadata.exif_keys:
        orientation = metadata['Exif.Image.Orientation'].raw_value
        orientation = int(orientation)
        pre_matrix = QtGui.QMatrix()
            
        if 1 <= orientation <= 2:
            if orientation == 2:
                pre_matrix.scale(-1, 1)
        elif 7 <= orientation <= 8:
            pre_matrix.rotate(-90)
            if orientation == 7:
                pre_matrix.scale(-1, 1)
        elif 3 <= orientation <= 4:
            pre_matrix.rotate(180)
            if orientation == 4:
                pre_matrix.scale(-1, 1)
        elif 5 <= orientation <= 6:
            pre_matrix.rotate(90)
            if orientation == 5:
                pre_matrix.scale(-1, 1)

        if (orientation > 8):
            print Exception('The value for \'Exif.Image.Orientation\' '
                            + 'is greater than 8, which should never be '
                            + 'the case. The Orientation shown may be '
                            + 'wrong.')
                
        if not pre_matrix.isIdentity():
            to_rotate = to_rotate.transformed(pre_matrix)
                
    if not matrix.isIdentity():
        to_rotate = to_rotate.transformed(matrix)

    return to_rotate

class ImageLoader(Thread):
    """An object used to load an image in a differente thread."""
    def __init__(self, filename, viewport_size, matrix=QtGui.QMatrix()):
        Thread.__init__(self)
        self.filename = filename
        self.matrix = matrix
        self.maximum_viewport_size = viewport_size
        # These variables are set by run().
        # If you try to acces the result of a thread before running it,
        # it's your own fault, but for debugging you can read if the thread
        # ran in variable self.ran.
        self.image = None
        self.image_scaled = None
        self.ran = False
    
    def run(self):
        self.image = QtGui.QImage(self.filename)
        self.image_scaled = scale_and_rotate_image(self.image,
                                                   self.filename,
                                                   self.maximum_viewport_size,
                                                   self.matrix)
        self.ran = True
