import shutil

__author__ = "Fernando Sanchez Villaamil"
__copyright__ = "Copyright 2010, Fernando Sanchez Villaamil"
__credits__ = ["Fernando Sanchez Villaamil"]
__license__ = "GPL"
__version__ = "1.0beta"
__maintainer__ = "Fernando Sanchez Villaamil"
__email__ = "nano@moomug.com"
__status__ = "Just for fun!"

class DeletionAction():
    def __init__(self, internal_state, path, filename, pos):
        self.internal_state = internal_state
        self.path = path
        self.filename = filename
        self.pos = pos

    def undo(self, viewport_size):
        shutil.move(self.path + '/discarded/' + self.filename,
                    self.path + '/' + self.filename)
        self.internal_state.add_image(self.path, self.filename,
                                     self.pos, viewport_size)
        self.internal_state.jump_to_image(self.pos, viewport_size)

    def redo(self, viewport_size):
        assert self.internal_state.pos == self.pos
        self.internal_state.discard_current_image(viewport_size)
        shutil.move(self.path + '/discarded/' + self.filename,
                    self.path + '/' + self.filename)

class RotationAction():
    def __init__(self, internal_state, degrees, pos):
        self.internal_state = internal_state
        self.degrees = degrees
        self.pos = pos
        self.old_pos = None

    def undo(self, viewport_size):
        self.old_pos = self.internal_state.pos
        self.internal_state.jump_to_image(self.pos, viewport_size)
        self.internal_state.rotate_current_image(-self.degrees, viewport_size)

    def redo(self, viewport_size):
        assert self.internal_state.pos == self.pos
        self.internal_state.rotate_current_image(self.degrees, viewport_size)

        if self.old_pos != self.internal_state.pos:
            jump_action = JumpAction(self.internal_state, self.pos)
            jump_action.old_pos = self.old_pos
            self.internal_state.add_to_forward_history(jump_action)

class JumpAction():
    def __init__(self, internal_state, pos):
        self.internal_state = internal_state
        self.pos = pos
        self.old_pos = None

    def undo(self, viewport_size):
        self.old_pos = self.internal_state.pos
        self.internal_state.jump_to_image(self.pos, viewport_size)

    def redo(self, viewport_size):
        assert self.internal_state.pos == self.pos
        self.internal_state.jump_to_image(self.old_pos, viewport_size)
