import pytest
import time
from slug import QuickConnect, Pipe


def test_through():
    pin = Pipe()
    pout = Pipe()
    qc = QuickConnect(  # noqa
        side_in=pin.side_out,
        side_out=pout.side_in,
        keepopen=False
    )

    pin.side_in.write(b'spameggs')
    pin.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'spameggs'


# Until we implement Posix and #7
@pytest.mark.xfail
def test_change_input():
    p1 = Pipe()
    p2 = Pipe()
    pout = Pipe()
    qc = QuickConnect(
        side_in=p1.side_out,
        side_out=pout.side_in,
        keepopen=False
    )

    p1.side_in.write(b'spam')
    p2.side_in.write(b'foo')

    time.sleep(1.0)
    qc.side_in = p2.side_out

    p1.side_in.write(b'eggs')
    p2.side_in.write(b'bar')

    p1.side_in.close()
    p2.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'spamfoobar'


def test_change_output():
    pin = Pipe()
    p1 = Pipe()
    p2 = Pipe()
    qc = QuickConnect(
        side_in=pin.side_out,
        side_out=p1.side_in,
    )

    pin.side_in.write(b'spam')

    time.sleep(1.0)
    qc.side_out = p2.side_in

    pin.side_in.write(b'eggs')

    out1 = p1.side_out.read(4000)
    out2 = p2.side_out.read(4000)
    assert out1 == b'spam'
    assert out2 == b'eggs'
