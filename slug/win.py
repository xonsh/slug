"""
Versions of the base functionality optimized for the NT kernel.

The 9x kernel is just unsupported.
"""
import ctypes
from . import base

__all__ = ('Process', 'Valve')


class Process(base.Process):
    # https://stackoverflow.com/questions/11010165/how-to-suspend-resume-a-process-in-windows
    # NtSuspendProcess would be better, but
    #  1. maintaining a minority port
    #  2. undocumented functions
    #  3. No references to the resuming function

    # Note: Because Cygwin has complete control of all the processes, it does other things.
    # We don't have control of our children, so we can't do those things.
    def pause(self):
        """
        Pause the process, able to be continued later
        """
        if self.pid is not None:
            ctypes.windll.kernel32.DebugActiveProcess(self.pid)
            # When we exit, the process will resume. The alternative is for it to die.
            ctypes.windll.kernel32.DebugSetProcessKillOnExit(False)

    def unpause(self):
        """
        Continue the process after it's been paused
        """
        if self.pid is not None:
            ctypes.windll.kernel32.DebugActiveProcessStop(self.pid)


class Valve:
    def _thread(self):
        while True:
            chunk = self.side_in.read(self.CHUNKSIZE)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
                self.gate.wait()
        if not self.keepopen:
            self.side_out.close()

    def turn_off(self):
        """
        Disable flow
        """
        self.gate.clear()
        ctypes.windll.kernel32.CancelSynchronousIo(ctypes.wintypes.HANDLE(self.thread.ident))
