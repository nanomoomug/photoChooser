#!/usr/bin/env python
"""
A threaded ImageLoader.

A threaded image loader. It will do two things:
1. Load a 'QImage' into 'self.image' that is the exact image that was read from
   the filname given in the constructor.
2. It will make a copy of the read image, attempt to read the Exif metadata of
   the image file, get the orientation from the metadata, rotate the image
   accordingly and finaly scale it the size of the viewport. The size of the
   viewport must also be passed as an argument to the constructor. The
   transformed image will be put in 'self.scaledImage'

The reason why QImage is used and not QPixmap ---even though it may have to be
converted later to QPixmap to be shown--- is that QPixmap can not be used
outside of the main thread.
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

class ImageLoader(Thread):
    def __init__(self, filename, viewportSize, matrix=QtGui.QMatrix()):
        Thread.__init__(self)
        self.filename = filename
        self.matrix = matrix
        self.maximumViewportSize = viewportSize
    
    def run(self):
        self.image = QtGui.QImage(self.filename)
        toScale = self.image
        metadata = pyexiv2.metadata.ImageMetadata(str(self.filename))
        metadata.read()
        if 'Exif.Image.Orientation' in metadata.exif_keys:
            orientation = metadata['Exif.Image.Orientation'].raw_value
            orientation = int(orientation)
            preMatrix = QtGui.QMatrix()
            
            if 1 <= orientation <= 2:
                if orientation == 2:
                    preMatrix.scale(-1, 1)
            elif 7 <= orientation <= 8:
                preMatrix.rotate(-90)
                if orientation == 7:
                    preMatrix.scale(-1, 1)
            elif 3 <= orientation <= 4:
                preMatrix.rotate(180)
                if orientation == 4:
                    preMatrix.scale(-1, 1)
            elif 5 <= orientation <= 6:
                preMatrix.rotate(90)
                if orientation == 5:
                    preMatrix.scale(-1, 1)

            if (orientation > 8):
                print Exception('The value for \'Exif.Image.Orientation\' '
                                + 'is greater than 8, which should never be '
                                + 'the case. The Orientation shown may be '
                                + 'wrong.')
                
            if not preMatrix.isIdentity():
                toScale = toScale.transformed(preMatrix)
                
        if not self.matrix.isIdentity():
            toScale = toScale.transformed(self.matrix)
            
        self.imageScaled = toScale.scaled(self.maximumViewportSize,
                                          QtCore.Qt.KeepAspectRatio)
