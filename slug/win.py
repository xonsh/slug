"""
Versions of the base functionality optimized for the NT kernel.

The 9x kernel is just unsupported.
"""
import ctypes
import time
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


def _peek_named_pipe_return(value):
    print("PeekNamedPipe return", repr(value))
    if value == 0:
        raise ctypes.WinError()
    return value

PeekNamedPipe = ctypes.windll.kernel32.PeekNamedPipe
PeekNamedPipe.restype = _peek_named_pipe_return


def _peek_pipe(pipe):
    lpTotalBytesAvail = ctypes.wintypes.DWORD(0)
    PeekNamedPipe(
        ctypes.wintypes.HANDLE(pipe.fileno()),
        None,
        ctypes.wintypes.DWORD(0),
        None,
        ctypes.byref(lpTotalBytesAvail),
        None,
    )
    return lpTotalBytesAvail.value


class Valve(base.Valve):
    """
    Forwards from one file-like to another, but this flow may be paused and
    resumed.
    """
    def _thread(self):
        while True:
            try:
                avail = _peek_pipe(self.side_in)
            except OSError as exc:
                if exc.winerror == 6:  # ERROR_INVALID_HANDLE
                    # Assume EOF?
                    pass  # Have it read out remaining data
                else:
                    raise

            # This feels like there's a race condition in here, but I think the
            # window is small enough we can call it "slight asyncronousity".
            if not self.gate.is_set():
                self.gate.wait()
                continue

            if avail == 0:
                # Do we want to sleep?
                time.sleep(0.1)
                continue

            chunk = self.side_in.read(avail)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()
