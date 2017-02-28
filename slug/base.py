"""
Base, non-system specific abstract implementations.
"""
import os
import subprocess
__all__ = ('Process', 'Pipe', 'ProcessGroup')


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
