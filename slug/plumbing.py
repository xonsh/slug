"""
Several implementations of "plumbing" to help connect various bits and basic 
data flows.
"""
import threading
__all__ = 'Tee', 'Valve'


def read_chunks(fo, *, chunksize=4096):
    """
    The magic of the plumbing. Generates chunks from the file object with timely
    reading while still maintaining performance.
    """
    # Initial testing shows that we should just do the naive thing
    while True:
        chunk = fo.read(chunksize)
        if chunk == b'':
            break
        else:
            yield chunk


class Tee:
    """
    Forwards from one file-like to another, but a callable is passed all data 
    that flows over the connection.

    The callable is called many times with chunks of the data, until EOF. Each
    chunk is a bytes. At EOF, the eof callback is called.

    NOTE: There are several properties about how the callback is called, and 
    care should be taken. In particular:
     * No guarentees about which thread, greenlet, coroutine, etc is current
     * If it blocks, the connection will block
     * If it throws an exception, the connection may die

    For these reasons, it is highly recommended that the data be immediately
    handed to a pipe, queue, buffer, etc.
    """
    def __init__(self, side_in, side_out, callback, eof=None):
        self.side_in = side_in
        self.side_out = side_out
        self.callback = callback
        self.eof = eof
        self.thread = threading.Thread(target=self._thread, daemon=True)
        self.thread.start()

    def _thread(self):
        try:
            for chunk in read_chunks(self.side_in):
                self.callback(chunk)
                self.side_out.write(chunk)
        finally:
            if self.eof is not None:
                self.eof()


class Valve:
    """
    Forwards from one file-like to another, but this flow may be paused and
    resumed.
    """
    def __init__(self, side_in, side_out):
        self.side_in = side_in
        self.side_out = side_out
        self.gate = threading.Event()
        self.thread = threading.Thread(target=self._thread, daemon=True)
        self.thread.start()

    def _thread(self):
        for chunk in read_chunks(self.side_in):
            self.side_out.write(chunk)
            self.gate.wait()

    def turn_on(self):
        """
        Enable flow
        """
        self.gate.set()


    def turn_off(self):
        """
        Disable flow
        """
        self.gate.clear()
