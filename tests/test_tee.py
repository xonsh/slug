import io
from slug import Tee, Pipe


def test_tee_basics():
    pin = Pipe()
    pout = Pipe()
    buf = io.BytesIO()
    t = Tee(  # noqa
        side_in=pin.side_out,
        side_out=pout.side_in,
        callback=buf.write,
        # Closing a BytesIO disables getting the value
        # eof=buf.close,
    )
    pin.side_in.write(b'foobar')
    pin.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'foobar'
    # This is only guarenteed _after_ it appears on the pipe
    assert buf.getvalue() == b'foobar'
