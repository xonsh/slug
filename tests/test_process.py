import sys
from slug import Process, Pipe


def runpy(code):
    return [sys.executable, '-c', code]


def test_successful_command():
    proc = Process(runpy('import sys; sys.exit(0)'))
    proc.start()
    proc.join()
    assert proc.return_code == 0


def test_failed_command():
    proc = Process(runpy('import sys; sys.exit(42)'))
    proc.start()
    proc.join()
    assert proc.return_code == 42


def test_kill_process():
    proc = Process(runpy('input()'))
    proc.start()
    proc.kill()
    assert proc.return_code != 0


def test_terminate_process():
    proc = Process(runpy('input()'))
    proc.start()
    proc.terminate()
    proc.join()
    assert proc.return_code != 0


def test_pipe_output():
    pi = Pipe()
    proc = Process(runpy(r'print("hello")'), stdout=pi.side_in)
    proc.start()
    data = pi.side_out.readline()
    # Pipe is closed but process might still be live
    proc.join()  # Commenting this out causes data to be None?
    assert proc.return_code == 0
    assert data in (b'hello\n', b'hello\r\n')


def test_pipe_input():
    pi = Pipe()
    proc = Process(runpy(r'import sys; sys.exit(input() == "spam")'), stdin=pi.side_out)
    proc.start()
    pi.side_in.write(b"spam\n")
    pi.side_in.close()
    # Pipe is closed but process might still be live
    proc.join()
    assert proc.return_code == 1


def test_inner_pipe():
    pi = Pipe()
    prod = Process(runpy(r'print("eggs")'), stdout=pi.side_in)
    cons = Process(runpy(r'import sys; sys.exit(input() == "eggs")'), stdin=pi.side_out)
    prod.start()
    cons.start()
    prod.join()
    cons.join()
    assert prod.return_code == 0
    assert cons.return_code == 1


def test_inner_pipe_reversed_order():
    pi = Pipe()
    prod = Process(runpy(r'print("eggs")'), stdout=pi.side_in)
    cons = Process(runpy(r'import sys; sys.exit(input() == "eggs")'), stdin=pi.side_out)
    cons.start()
    prod.start()
    cons.join()
    prod.join()
    assert prod.return_code == 0
    assert cons.return_code == 1


def test_partial_output():
    pi = Pipe()
    proc = Process(
        runpy(r'print("foo", flush=True); input(); print("bar", flush=True)'),
        stdout=pi.side_in,
    )
    proc.start()
    data = pi.side_out.readline()
    proc.terminate()
    proc.join()
    assert data in (b'foo\n', b'foo\r\n')


def test_terminated_output():
    # NOTE: POSIX clears the pipe when a process has non-zero return
    pi = Pipe()
    proc = Process(
        runpy(r'print("foo", flush=True); input(); print("bar", flush=True)'),
        stdout=pi.side_in,
    )
    proc.start()
    pi.side_in.close()  # Remove our reference on this end of the pipe, now that the child has one
    proc.terminate()
    proc.join()
    data = pi.side_out.read()
    assert data == b''


def test_error_output():
    # NOTE: POSIX clears the pipe when a process has non-zero return
    pi = Pipe()
    proc = Process(
        runpy(r'import sys; print("bar", flush=True); sys.exit(42)'),
        stdout=pi.side_in,
    )
    proc.start()
    pi.side_in.close()  # Remove our reference on this end of the pipe, now that the child has one
    proc.join()
    data = pi.side_out.read()
    assert data in (b'bar\n', b'bar\r\n')
