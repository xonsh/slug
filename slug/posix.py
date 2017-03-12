"""
Versions of the base functionality optimized for by-the-spec POSIX.

Linux/Mac/BSD-specific code should live elsewhere.
"""
import signal
import selectors
from . import base

__all__ = ('Process', 'Valve')


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
