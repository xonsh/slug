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



def test_pipe_output():
    pi = Pipe()
    proc = Process([sys.executable, '-c', r'import sys; sys.exit(sys.stdin.readline() == "spam\n")'], stdin=pi.side_out)
    proc.start()
    pi.side_in.write(b"spam\n")
    pi.side_in.close()
    # Pipe is closed but process might still be live
    proc.join()  # Commenting this out causes data to be None?
    assert proc.return_code == 1


def test_inner_pipe():
    pi = Pipe()
    producer = Process([sys.executable, '-c', r'print("eggs")'], stdout=pi.side_in)
    consumer = Process([sys.executable, '-c', r'import sys; sys.exit(sys.stdin.readline() == "eggs\n")'], stdin=pi.side_out)
    producer.start()
    consumer.start()
    producer.join()
    consumer.join()
    assert producer.return_code == 0
    assert consumer.return_code == 1


def test_inner_pipe_reversed_order():
    pi = Pipe()
    producer = Process([sys.executable, '-c', r'print("eggs")'], stdout=pi.side_in)
    consumer = Process([sys.executable, '-c', r'import sys; sys.exit(sys.stdin.readline() == "eggs\n")'], stdin=pi.side_out)
    consumer.start()
    producer.start()
    consumer.join()
    producer.join()
    assert producer.return_code == 0
    assert consumer.return_code == 1
