import sys
from slug import Process, Pipe


def test_successful_command():
    proc = Process([sys.executable, '-c', 'import sys; sys.exit(0)'])
    proc.start()
    proc.join()
    assert proc.return_code == 0


def test_failed_command():
    proc = Process([sys.executable, '-c', 'import sys; sys.exit(42)'])
    proc.start()
    proc.join()
    assert proc.return_code == 42


def test_pipe_output():
    pi = Pipe()
    proc = Process([sys.executable, '-c', 'print("hello")'], stdout=pi.side_in)
    proc.start()
    data = pi.side_out.readline()
    # Pipe is closed but process might still be live
    proc.join()  # Commenting this out causes data to be None?
    assert proc.return_code == 0
    assert data == b'hello\n'
