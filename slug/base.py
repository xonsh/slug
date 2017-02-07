"""
Base, non-system specific abstract implementations.
"""
import os
__all__ = ('Process', 'Pipe', 'ProcessGroup')


class Process:
    def __init__(self, cmd, *, stdin=None, stdout=None, stderr=None, environ=None, priority=None):
        NotImplemented

    def signal(self, signal):
        """
        Send a request to the process
        """
        NotImplemented

    def terminate(self):
        """
        Forcibly quit the process
        """

    @property
    def priority(self):
        """
        The priority of the process. The priority ranges from 19 to -20, where
        lower is more priority.

        Not all priorities are available at all permissions.
        """
        return vars(self)['priority']

    @priority.setter
    def priority(self, value):
        vars(self)['priority'] = value
        if self.started:
            self._set_priority(value)

    def _set_priority(self, value):
        """
        Actually call out to the OS to change the priority.
        """
        NotImplemented

    @property
    def started(self):
        """
        Has the process started?
        """
        NotImplemented

    @property
    def status(self):
        """
        The status of the process, one of:

        * ...: The process has not yet started
        * ...: The process is currently running
        * ...: The process is paused
        * ...: The process has exited
        """
        NotImplemented

    @property
    def pid(self):
        """
        The process identifier. None if the process hasn't started.
        """
        NotImplemented

    def start(self):
        """
        Start the process.
        """
        NotImplemented

    def _virtual_start(self, pid):
        """
        Mark the process as started when something else somewhere does the starting.
        """
        NotImplemented


class ProcessGroup:
    def __enter__(self):
        return self

    def __exit__(self, t, exc, b):
        if exc is None:
            # XXX: Do we want to automatically start the group at the end of the context manager?
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
        r, w = os.pipe2(0)  # TODO: Flags
        self.side_in = os.fdopen(w, 'wb', buffering=0)
        self.side_out = os.fdopen(r, 'rb', buffering=0)


class PseudoTerminal:
    """
    A two-way byte stream, with extras.
    """
    def __init__(self):
        self.side_master, self.side_slave = NotImplemented, NotImplemented
