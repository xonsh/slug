"""
Base, non-system specific abstract implementations.
"""
import os
import subprocess
import threading
import weakref
import collections.abc
__all__ = (
    # Base primitives
    'Process', 'ProcessGroup', 'Pipe', 'PseudoTerminal',
    # Constants
    'INIT', 'RUNNING', 'PAUSED', 'FINISHED',
    # Plumbing
    'Tee', 'Valve', 'QuickConnect',
)

INIT = "init"
RUNNING = "running"
PAUSED = "paused"
FINISHED = "finished"


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
        Ask the process to exit quickly, if "asking nicely" is something this
        platform understands
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
            return INIT
        elif self._proc.returncode is not None:
            return FINISHED
        else:
            # TODO: How to tell if a process is currently stopped?
            return RUNNING

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


# Py36: collections.abc.Collection
class ProcessGroup(collections.abc.Sized, collections.abc.Iterable, collections.abc.Container):
    """
    A collection of processes that can be controlled as a group.

    The process group is inherited. The descendent processes are also part of
    the group.

    A process may only be part of one group. If a process is added to a new
    group, it is removed from the old group. Its children may or may not go with
    it.
    """
    def __init__(self):
        self._procs = list()

    def __enter__(self):
        return self

    def __exit__(self, t, exc, b):
        # Doesn't actually do anything, just lets users set process group construction into a block
        pass

    def __iter__(self):
        yield from self._procs

    def __len__(self):
        return len(self._procs)

    def __contains__(self, item):
        return item in self._procs

    def add(self, proc):
        """
        Add a process to the process group.
        """
        if hasattr(proc, '_process_group'):
            raise ValueError("Cannot move processes between groups")
        proc._process_group = weakref.ref(self)
        self._procs.append(proc)

    def start(self):
        for proc in self:
            proc.start()

    @property
    def status(self):
        """
        The status of the process group, one of:

        * INIT: The process group has not yet started
        * RUNNING: The process group is currently running
        * FINISHED: All the processes have exited
        """
        if all(p.status == FINISHED for p in self):
            return FINISHED
        elif all(p.status == INIT for p in self):
            return INIT
        else:
            return RUNNING

    @property
    def started(self):
        return self.pgid is not None

    def signal(self, signal):
        """
        Send a request to all the processes, by POSIX signal number
        """
        for proc in self:
            proc.send_signal(signal)

    def kill(self):
        """
        Forcibly quit all the processes
        """
        for proc in self:
            proc.kill()

    def terminate(self):
        """
        Ask the all the processes to exit quickly, if asking nicely is
        something this platform understands.
        """
        for proc in self:
            proc.terminate()

    def pause(self):
        """
        Pause all the processes, able to be continued later
        """
        for proc in self:
            proc.pause()

    def unpause(self):
        # continue is a reserved word
        """
        Continue the all processes that have been paused
        """
        for proc in self:
            proc.unpause()

    def join(self):
        """
        Wait for all the processes to finish.
        """
        for proc in self:
            proc.join()


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
                if chunk in (b'', ''):
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
            if chunk in (b'', ''):
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
            if chunk in (b'', ''):
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()
