"""
Versions of the base functionality optimized for by-the-spec POSIX.

Linux/Mac/BSD-specific code should live elsewhere.
"""
import signal
import selectors
import threading
from . import base

__all__ = ('Process', 'Valve', 'QuickConnect')


class Process(base.Process):
    def pause(self):
        """
        Pause the process, able to be continued later
        """
        self.signal(signal.SIGSTOP)

    def unpause(self):
        # continue is a reserved word
        """
        Continue the process after it's been paused
        """
        self.signal(signal.SIGCONT)


class Valve(base.Valve):
    """
    Forwards from one file-like to another, but this flow may be paused and
    resumed.

    This implementation doesn't support changing the target descriptors after
    initialization.
    """
    def _thread(self):
        sel = selectors.DefaultSelector()
        sel.register(self.side_in, selectors.EVENT_READ)
        while True:
            sel.select()
            # Don't care about the event, there's only one thing it can be.

            # This feels like there's a race condition in here, but I think the
            # window is small enough we can call it "slight asyncronousity".
            if not self.gate.is_set():
                self.gate.wait()
                continue

            chunk = self.side_in.read(self.CHUNKSIZE)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()


class QuickConnect(base.QuickConnect):
    def __init__(self, side_in, side_out, *, keepopen=True):
        vars(self)['side_in'] = None  # Initialize so we don't get key errors
        self.sel = selectors.DefaultSelector()
        self.changed = threading.Event()
        super().__init__(side_in, side_out, keepopen=keepopen)

    @property
    def side_in(self):
        return vars(self)['side_in']

    @side_in.setter
    def side_in(self, value):
        # There's a race condition in here...
        old = vars(self)['side_in']
        vars(self)['side_in'] = value
        if old is not None:
            self.sel.unregister(old)
            self.changed.set()
        self.sel.register(value, selectors.EVENT_READ)

    def _thread(self):
        while True:
            self.sel.select()
            # Don't care about the event, there's only one thing it can be.

            if self.changed.is_set():
                self.changed.clear()
                continue

            chunk = self.side_in.read(self.CHUNKSIZE)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()
