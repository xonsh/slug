"""
Several implementations of "plumbing" to help connect various bits and basic 
data flows.
"""

__all__ = 'Tee', 'Valve'

class Tee:
    """
    Forwards from one file-like to another, but a callable is passed all data 
    that flows over the connection.

    The callable is called many times with chunks of the data, until EOF. Each
    chunk is a bytes. At EOF, it is called with None.

    NOTE: There are several properties about how the callback is called, and 
    care should be taken. In particular:
     * No guarentees about which thread, greenlet, coroutine, etc is current
     * If it blocks, the connection will block
     * If it throws an exception, the connection may die
    """
    def __init__(self, side_in, side_out, callback):
        NotImplemented

class Valve:
    """
    Forwards from one file-like to another, but this flow may be paused and
    resumed.
    """
    def __init__(self, side_in, side_out):
        NotImplemented

    def turn_on(self):
        """
        Enable flow
        """
        NotImplemented


    def turn_off(self):
        """
        Disable flow
        """
        NotImplemented

