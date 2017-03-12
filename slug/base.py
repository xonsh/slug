"""
Base, non-system specific abstract implementations.
"""
import os
import subprocess
import threading
__all__ = (
    # Base primitives
    'Process', 'ProcessGroup', 'Pipe', 'PseudoTerminal',
    # Plumbing
    'Tee', 'Valve', 'QuickConnect',
)


class Process:
    def __init__(self, cmd, *, stdin=None, stdout=None, stderr=None,
                 cwd=None, environ=None):
        self.cmd = cmd
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.cwd = cwd
        self.environ = environ
        self._proc = None

    def signal(self, signal):
        """
        Send a request to the process, by POSIX signal number
        """
        if self._proc:
            self._proc.send_signal(signal)

    def kill(self):
        """
        Forcibly quit the process
        """
        if self._proc:
            self._proc.kill()

    def terminate(self):
        """
        Ask the process to exit quickly
        """
        if self._proc:
            self._proc.terminate()

    def pause(self):
        """
        Pause the process, able to be continued later
        """
        # No cross-platform way to do this
        raise NotImplementedError

    def unpause(self):
        # continue is a reserved word
        """
        Continue the process after it's been paused
        """
        # No cross-platform way to do this
        raise NotImplementedError

    @property
    def started(self):
        """
        Has the process started?
        """
        return self._proc is not None

    INIT = "init"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"

    @property
    def status(self):
        """
        The status of the process, one of:

        * INIT: The process has not yet started
        * RUNNING: The process is currently running
        * PAUSED: The process is paused
        * FINISHED: The process has exited
        """
        if self._proc is None:
            return self.INIT
        elif self._proc.returncode is not None:
            return self.FINISHED
        else:
            # TODO: How to tell if a process is currently stopped?
            return self.RUNNING

    @property
    def pid(self):
        """
        The process identifier. None if the process hasn't started.
        """
        if self._proc is not None:
            return self._proc.pid

    @property
    def return_code(self):
        """
        The return code of the process. None if it hasn't returned yet.
        """
        # TODO: what's the result if it exits from signal/error? Thinking not an int
        if self._proc is not None:
            return self._proc.returncode

    def start(self):
        """
        Start the process.
        """
        self._proc = subprocess.Popen(
            self.cmd, stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
            cwd=self.cwd, env=self.environ
        )

    def join(self):
        if self._proc is not None:
            self._proc.wait()


class ProcessGroup:
    def __enter__(self):
        return self

    def __exit__(self, t, exc, b):
        if exc is None:
            # XXX: Do we want to automatically start the group?
            NotImplemented

    def Process(self, *pargs, **kwargs):
        NotImplemented
        if self.started:
            # Group already started, bring process back up to speed
            NotImplemented

    def start(self):
        NotImplemented

    @property
    def started(self):
        """
        Has the process groups started?
        """
        NotImplemented

    @property
    def status(self):
        """
        The status of the process group, one of:

        * ...: The process group has not yet started
        * ...: The process group is currently running
        * ...: All the processes have exited
        """
        NotImplemented

    def signal(self, signal):
        """
        Send a request to the process group
        """
        NotImplemented

    def terminate(self):
        """
        Forcibly quit the process group
        """
        NotImplemented


class Pipe:
    """
    A one-way byte stream.
    """
    def __init__(self):
        r, w = self._mkpipe()
        self.side_in = os.fdopen(w, 'wb', buffering=0)
        self.side_out = os.fdopen(r, 'rb', buffering=0)

    @staticmethod
    def _mkpipe():
        return os.pipe()


class PseudoTerminal:
    """
    A two-way byte stream, with extras.
    """
    def __init__(self):
        self.side_master, self.side_slave = NotImplemented, NotImplemented


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
    CHUNKSIZE = 4096

    def __init__(self, side_in, side_out, callback, eof=None, *, keepopen=False):
        self.side_in = side_in
        self.side_out = side_out
        self.callback = callback
        self.eof = eof
        self.keepopen = keepopen
        self.thread = threading.Thread(target=self._thread, daemon=True)
        self.thread.start()

    def _thread(self):
        try:
            while True:
                chunk = self.side_in.read(self.CHUNKSIZE)
                if chunk == b'':
                    break
                else:
                    self.callback(chunk)
                    self.side_out.write(chunk)
        finally:
            if self.eof is not None:
                self.eof()
            if not self.keepopen:
                self.side_out.close()


class Valve:
    """
    Forwards from one file-like to another, but this flow may be paused and
    resumed.
    """
    # This implementation is broken. It will read an extra block.
    CHUNKSIZE = 4096

    def __init__(self, side_in, side_out, *, keepopen=False):
        self.side_in = side_in
        self.side_out = side_out
        self.gate = threading.Event()
        self.keepopen = keepopen
        self.thread = threading.Thread(target=self._thread, daemon=True)
        self.thread.start()

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


class QuickConnect:
    """
    Forwards one file-like to another, but allows the files involved to be
    swapped arbitrarily at any time.

    NOTE: Unlike other plumbing types, this defaults to NOT closing the
    receiving file. This means that a ``Tee`` should be used before a
    ``QuickConnect`` in order to detect EOF and close any files involved.

    Attributes:

    * ``side_in``: The file the QuickConnect reads from
    * ``side_out``: The file the QuickConnect writes to

    The attributes may be written to at any time and the QuickConnect will
    reconfigure anything internal as quickly as possible.
    """

    # This implementation is broken. It will read an extra block.
    CHUNKSIZE = 4096

    def __init__(self, side_in, side_out, *, keepopen=True):
        self.side_in = side_in
        self.side_out = side_out
        self.keepopen = keepopen
        self.thread = threading.Thread(target=self._thread, daemon=True)
        self.thread.start()

    def _thread(self):
        while True:
            chunk = self.side_in.read(self.CHUNKSIZE)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()
