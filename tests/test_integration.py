import io
import slug
import threading


def test_xonshy_capture_output():
    procout = slug.Pipe()
    stdout = io.BytesIO()
    outbuffer = io.BytesIO()
    finished = threading.Event()

    buf = slug.Pipe()
    slug.Tee(procout.side_out, stdout, buf.side_in.write, buf.side_in.close, keepopen=True)

    slug.Tee(
        buf.side_out,
        outbuffer,
        lambda data: None,
        finished.set,
        keepopen=True,
    )

    procout.side_in.write(b'Xonshy Output')
    procout.side_in.close()
    finished.wait()

    assert stdout.getvalue() == b'Xonshy Output'
    assert outbuffer.getvalue() == b'Xonshy Output'


def test_xonshy_capture_no_output():
    procout = slug.Pipe()
    stdout = io.BytesIO()
    outbuffer = io.BytesIO()
    finished = threading.Event()

    # We need it not printed and stored
    buf = procout

    slug.Tee(
        buf.side_out,
        outbuffer,
        lambda data: None,
        finished.set,
        keepopen=True,
    )

    procout.side_in.write(b'Xonshy Capture')
    procout.side_in.close()
    finished.wait()

    assert stdout.getvalue() == b''
    assert outbuffer.getvalue() == b'Xonshy Capture'