from slug.utils import thread_async_raise
import threading


def test_tar():
    exc = None
    started = threading.Event()

    def test():
        nonlocal exc
        started.set()
        try:
            while True:
                pass
        except Exception as e:
            exc = e

    t = threading.Thread(target=test, daemon=True)
    t.start()
    started.wait()
    thread_async_raise(t, ZeroDivisionError)
    t.join()
    assert isinstance(exc, ZeroDivisionError)


def test_tar_read():
    exc = None
    started = threading.Event()
    from slug import Pipe  # Used to create a non-returning read()

    p = Pipe()

    def test():
        nonlocal exc
        started.set()
        try:
            p.side_out.read(4000)
        except Exception as e:
            exc = e

    t = threading.Thread(target=test, daemon=True)
    t.start()
    started.wait()
    thread_async_raise(t, ZeroDivisionError)
    t.join()
    assert isinstance(exc, ZeroDivisionError)


def test_tar_read_ki():
    exc = None
    started = threading.Event()
    from slug import Pipe  # Used to create a non-returning read()

    p = Pipe()

    def test():
        nonlocal exc
        started.set()
        try:
            p.side_out.read(4000)
        except Exception as e:
            exc = e

    t = threading.Thread(target=test, daemon=True)
    t.start()
    started.wait()
    thread_async_raise(t, KeyboardInterrupt)
    t.join()
    assert isinstance(exc, KeyboardInterrupt)


def test_tar_read_se():
    exc = None
    started = threading.Event()
    from slug import Pipe  # Used to create a non-returning read()

    p = Pipe()

    def test():
        nonlocal exc
        started.set()
        try:
            p.side_out.read(4000)
        except Exception as e:
            exc = e

    t = threading.Thread(target=test, daemon=True)
    t.start()
    started.wait()
    thread_async_raise(t, SystemExit)
    t.join()
    assert isinstance(exc, SystemExit)
