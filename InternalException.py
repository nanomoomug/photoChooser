class InternalException(Exception):
    def __init__(self, msg):
        super(InternalException, self).__init__(msg)

