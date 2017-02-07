from slug import Pipe

def test_goesthrough():
    p = Pipe()
    p.side_in.write(b"Hello")
    p.side_in.close()

    data = p.side_out.read()
    assert data == b'Hello'
