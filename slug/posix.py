"""
Versions of the base functionality optimized for by-the-spec POSIX.

Linux/Mac/BSD-specific code should live elsewhere.
"""
import signal
import selectors
import threading
import os
import subprocess
from . import base

__all__ = ('Process', 'ProcessGroup', 'Valve', 'QuickConnect')


class Process(base.Process):
    def start(self):
        """
        Start the process.
        """
        preexec = None
        if hasattr(self, '_process_group_leader'):
            # This probably needs some kind of syncronization...
            if self._process_group_leader is ...:
                preexec = os.setpgrp
            else:
                pgid = self._process_group_leader.pid

                def preexec():
                    os.setpgid(0, pgid)

        self._proc = subprocess.Popen(
            # What to execute
            self.cmd,
            preexec_fn=preexec,
            # What IO it has
            stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
            # Environment it executes in
            cwd=self.cwd, env=self.environ,
        )

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

    @property
    def pgid(self):
        """
        Process group ID, or None if it hasn't started yet.

        POSIX only.
        """
        if self.pid is not None:
            return os.getpgid(self.pid)

    @property
    def sid(self):
        """
        Session ID, or None if it hasn't started yet.

        POSIX only.
        """
        return os.getsid(self.pid)


class ProcessGroup(base.ProcessGroup):
    pgid = None

    def add(self, proc):
        super().add(proc)
        if self.started and proc.started:
            os.setpgid(proc.pid, self.pgid)

    def start(self):
        # This relies on consistent iteration order
        procs = iter(self)
        leader = next(procs)
        leader._process_group_leader = ...
        for p in procs:
            p._process_group_leader = leader
        super().start()
        # Don't use pgid here because sometimes programs exit in their first
        # slice (eg on Mac, see https://github.com/xonsh/slug/issues/10)
        self.pgid = leader.pid

    def kill(self):
        if self.pgid is not None:
            os.kill(-self.pgid, signal.SIGKILL)

    def terminate(self):
        if self.pgid is not None:
            os.kill(-self.pgid, signal.SIGTERM)


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


class QuickConnect(base.QuickConnect):
    def __init__(self, side_in, side_out, *, keepopen=True):
        vars(self)['side_in'] = None  # Initialize so we don't get key errors
        self.sel = selectors.DefaultSelector()
        self.changed = threading.Event()
        super().__init__(side_in, side_out, keepopen=keepopen)

    @property
    def side_in(self):
        return vars(self)['side_in']

    @side_in.setter
    def side_in(self, value):
        # There's a race condition in here...
        old = vars(self)['side_in']
        vars(self)['side_in'] = value
        if old is not None:
            self.sel.unregister(old)
            self.changed.set()
        self.sel.register(value, selectors.EVENT_READ)

    def _thread(self):
        while True:
            self.sel.select()
            # Don't care about the event, there's only one thing it can be.

            if self.changed.is_set():
                self.changed.clear()
                continue

            chunk = self.side_in.read(self.CHUNKSIZE)
            if chunk == b'':
                break
            else:
                self.side_out.write(chunk)
        if not self.keepopen:
            self.side_out.close()
