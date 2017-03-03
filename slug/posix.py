"""
Versions of the base functionality optimized for by-the-spec POSIX.

Linux/Mac/BSD-specific code should live elsewhere.
"""
import signal
from . import base

__all__ = ('Process',)


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
