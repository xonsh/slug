import pytest
from slug import Pipe


def test_goesthrough():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    data = p.side_out.read()
    assert data == b'Hello'
    data = p.side_out.read()
    assert data == b''


def test_eof():
    p = Pipe()
    p.side_in.write(b"spam")

    data = p.side_out.read(4)  # read() or read(-1) read until EOF
    assert data == b'spam'

    p.side_in.close()
    data = p.side_out.read()
    assert data == b''


def test_iter():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    riter = iter(p.side_out)

    data = next(riter)
    assert data == b'Hello'

    with pytest.raises(StopIteration):
        next(riter)


def test_iter_eof():
    p = Pipe()
    riter = iter(p.side_out)

    p.side_in.write(b"Hello\n")

    data = next(riter)
    assert data == b'Hello\n'

    p.side_in.close()

    with pytest.raises(StopIteration):
        next(riter)


def test_chunk():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    data = p.side_out.read(3)
    assert data == b'Hel'
    data = p.side_out.read(2)
    assert data == b'lo'
    data = p.side_out.read(5)
    assert data == b''


def test_chunk_eof():
    p = Pipe()
    p.side_in.write(b"Hello")

    data = p.side_out.read(3)
    assert data == b'Hel'
    data = p.side_out.read(2)
    assert data == b'lo'
    p.side_in.close()
    data = p.side_out.read(5)
    assert data == b''


def test_large_chunk():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    data = p.side_out.read(4000)
    assert data == b'Hello'
    data = p.side_out.read(4000)
    assert data == b''


def test_large_chunk_interactivish():
    p = Pipe()
    p.side_in.write(b"Hello")

    data = p.side_out.read(4000)
    assert data == b'Hello'
    p.side_in.close()
    data = p.side_out.read(4000)
    assert data == b''
