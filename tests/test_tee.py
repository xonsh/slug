import io
from slug import Tee, Pipe


def test_tee_basics():
    pin = Pipe()
    pout = Pipe()
    buf = io.BytesIO()

    closed = False

    def _closeit():
        nonlocal closed
        closed = True

    t = Tee(  # noqa
        side_in=pin.side_out,
        side_out=pout.side_in,
        callback=buf.write,
        eof=_closeit,
    )
    pin.side_in.write(b'foobar')
    pin.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'foobar'
    # This is only guarenteed _after_ it appears on the pipe
    assert buf.getvalue() == b'foobar'
    assert closed
