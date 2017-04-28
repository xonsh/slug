"""
Versions of the base functionality optimized for the NT kernel.

The 9x kernel is just unsupported.
"""
import ctypes
import _winapi
import signal
from . import base

__all__ = ('Process', 'ProcessGroup')


# {{{ win32 API calls

def _falsey_errcheck(result, func, arguments):
    if not result:
        raise ctypes.WinError()
    return arguments


def _truthy_errcheck_nt(result, func, arguments):
    if result:
        raise OSError(None, "NT Error", None, result)
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

CloseHandle = _winapi.CloseHandle

OpenProcess = _winapi.OpenProcess

PROCESS_SUSPEND_RESUME = ctypes.DWORD(0x0800)

NtSuspendProcess = ctypes.windll.ntdll.NtSuspendProcess
NtSuspendProcess.argtypes = (ctypes.wintypes.HANDLE,)
NtSuspendProcess.restype = ctypes.c_long
NtSuspendProcess.errcheck = _truthy_errcheck_nt

NtResumeProcess = ctypes.windll.ntdll.NtResumeProcess
NtResumeProcess.argtypes = (ctypes.wintypes.HANDLE,)
NtResumeProcess.restype = ctypes.c_long
NtResumeProcess.errcheck = _truthy_errcheck_nt

# }}}


class Process(base.Process):
    # https://groups.google.com/d/topic/microsoft.public.win32.programmer.kernel/IA-y-isvL9I/discussion

    # Note: Because Cygwin has complete control of all the processes, it does other things.
    # We don't have control of our children, so we can't do those things.
    def pause(self):
        """
        Pause the process, able to be continued later
        """
        if self.pid is not None:
            hproc = OpenProcess(PROCESS_SUSPEND_RESUME, False, self.pid)
            try:
                NtSuspendProcess(hproc)
            finally:
                CloseHandle(hproc)

    def unpause(self):
        """
        Continue the process after it's been paused
        """
        if self.pid is not None:
            hproc = OpenProcess(PROCESS_SUSPEND_RESUME, False, self.pid)
            try:
                NtResumeProcess(hproc)
            finally:
                CloseHandle(hproc)


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
        if proc.started and not isinstance(proc, base.VirtualProcess):
            # _handle is subprocess.Popen internal. Beats looking up the process ourselves.
            AssignProcessToJobObject(self.job, proc._proc._handle)

    def start(self):
        super().start()
        for proc in self:
            if isinstance(proc, base.VirtualProcess):
                continue
            # _handle is subprocess.Popen internal. Beats looking up the process ourselves.
            # FIXME: Handle if the process was already joined to us
            AssignProcessToJobObject(self.job, proc._proc._handle)

    def signal(self, sig):
        """
        Signal the process of an event.
        """
        if sig == signal.SIGKILL:
            self.kill()
        elif sig == signal.SIGTERM:
            self.terminate()
        else:
            super().signal(sig)

    def kill(self):
        TerminateJobObject(self.job, -9)
        for proc in self:
            if isinstance(proc, base.VirtualProcess):
                proc.kill()

    def terminate(self):
        TerminateJobObject(self.job, -9)
        for proc in self:
            if isinstance(proc, base.VirtualProcess):
                proc.terminate()
