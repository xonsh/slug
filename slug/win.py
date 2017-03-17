"""
Versions of the base functionality optimized for the NT kernel.

The 9x kernel is just unsupported.
"""
import ctypes
import _winapi
from . import base

__all__ = ('Process', 'ProcessGroup')


# {{{ win32 API calls

def _falsey_errcheck(result, func, arguments):
    if not result:
        raise ctypes.WinError()
    return arguments


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Length", ctypes.wintypes.DWORD),
                ("SecDescriptor", ctypes.wintypes.LPVOID),
                ("InheritHandle", ctypes.wintypes.BOOL)]


CreateJobObject = ctypes.windll.kernel32.CreateJobObjectW
CreateJobObject.argtypes = (ctypes.POINTER(SECURITY_ATTRIBUTES), ctypes.wintypes.LPCWSTR)
CreateJobObject.restype = ctypes.wintypes.HANDLE
CreateJobObject.errcheck = _falsey_errcheck

AssignProcessToJobObject = ctypes.windll.kernel32.AssignProcessToJobObject
AssignProcessToJobObject.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.UINT)
AssignProcessToJobObject.restype = ctypes.wintypes.BOOL
AssignProcessToJobObject.errcheck = _falsey_errcheck

TerminateJobObject = ctypes.windll.kernel32.TerminateJobObject
TerminateJobObject.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.HANDLE)
TerminateJobObject.restype = ctypes.wintypes.BOOL
TerminateJobObject.errcheck = _falsey_errcheck

DebugActiveProcess = ctypes.windll.kernel32.DebugActiveProcess
DebugActiveProcess.argtypes = (ctypes.wintypes.DWORD,)
DebugActiveProcess.restype = ctypes.wintypes.BOOL
DebugActiveProcess.errcheck = _falsey_errcheck

DebugSetProcessKillOnExit = ctypes.windll.kernel32.DebugSetProcessKillOnExit
DebugSetProcessKillOnExit.argtypes = (ctypes.wintypes.BOOL,)
DebugSetProcessKillOnExit.restype = ctypes.wintypes.BOOL
DebugSetProcessKillOnExit.errcheck = _falsey_errcheck

DebugActiveProcessStop = ctypes.windll.kernel32.DebugActiveProcessStop
DebugActiveProcessStop.argtypes = (ctypes.wintypes.DWORD,)
DebugActiveProcessStop.restype = ctypes.wintypes.BOOL
DebugActiveProcessStop.errcheck = _falsey_errcheck

CloseHandle = _winapi.CloseHandle

# }}}


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
            DebugActiveProcess(self.pid)
            # When we exit, the process will resume. The alternative is for it to die.
            DebugSetProcessKillOnExit(False)

    def unpause(self):
        """
        Continue the process after it's been paused
        """
        if self.pid is not None:
            DebugActiveProcessStop(self.pid)


class ProcessGroup(base.ProcessGroup):
    def __init__(self):
        super().__init__()
        self.job = CreateJobObject(None, None)

    def __del__(self):
        CloseHandle(self.job)
        self.job = None

    # __contains__ with IsProcessInJob? No matching __iter__.

    def add(self, proc):
        super().add(proc)
        if proc.started:
            # _handle is subprocess.Popen internal. Beats looking up the process ourselves.
            AssignProcessToJobObject(self.job, proc._proc._handle)

    def start(self):
        super().start()
        for proc in self:
            # _handle is subprocess.Popen internal. Beats looking up the process ourselves.
            # FIXME: Handle if the process was already joined to us
            AssignProcessToJobObject(self.job, proc._proc._handle)

    def kill(self):
        TerminateJobObject(self.job, -9)

    terminate = kill
