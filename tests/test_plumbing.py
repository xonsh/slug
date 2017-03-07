import io
from slug import Tee, Valve, Pipe


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


def test_valve_through():
    pin = Pipe()
    pout = Pipe()
    v = Valve(  # noqa
        side_in=pin.side_out,
        side_out=pout.side_in,
    )
    v.turn_on()

    pin.side_in.write(b'spameggs')
    pin.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'spameggs'
