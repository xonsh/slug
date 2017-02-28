import pytest
from slug import Pipe


def test_goesthrough():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    data = p.side_out.read()
    assert data == b'Hello'


def test_eof():
    p = Pipe()
    p.side_in.write(b"spam")

    data = p.side_out.read()
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
