
import InternalState

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

class DeletionAction():

    def __init__(self, internalState, deleted, pos):
        self.internalState = internalState
        self.deleted = deleted
        self.pos = pos

    def undo(self, viewportSize):
        self.internalState.add_image(deleted, pos, viewportSize)

    def redo(self, viewportSize):
        assert self.internalState.pos == self.pos
        self.internalState.discard_current_image(viewportSize)

class RotationAction():
    
    def __init__(self, internalState, degrees, pos):
        self.internalState = internalState
        self.degrees = degrees
        self.pos = pos

    def undo(self, viewportSize):
        self.oldPos = self.internalState.pos
        self.internalState.jump_to_image(self.pos, viewportSize)
        self.internalState.rotate_current_image(-self.degrees, viewportSize)

    def redo(self, viewportSize):
        assert self.internalState.pos == self.pos
        self.internalState.rotate_current_image(self.degrees, viewportSize)
        jumpAction = JumpAction(self.internalState, self.pos)
        jumpAction.oldPos = self.oldPos
        self.internalState.add_to_forward_history(jumpAction)

class JumpAction():

    def __init__(self, internalState, pos):
        self.internalState = internalState
        self.pos = pos

    def undo(self, viewportSize):
        self.oldPos = self.internalState.pos
        self.internalState.jump_to_image(self.pos, viewportSize)

    def redo(self, viewportSize):
        assert self.internalState.pos == self.pos
        self.internalState.jump_to_image(self.oldPos, viewportSize)
