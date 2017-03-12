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
