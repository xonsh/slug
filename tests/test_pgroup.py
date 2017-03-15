from slug import ProcessGroup, Process, Pipe
from conftest import runpy


def test_group():
    with ProcessGroup() as pg:
        p1 = Pipe()
        pg.add(Process(runpy("print('spam')"), stdout=p1.side_in))
        p2 = Pipe()
        pg.add(Process(runpy("print('eggs')"), stdout=p2.side_in))
        p3 = Pipe()
        pg.add(Process(runpy("print('vikings')"), stdout=p3.side_in))

    pg.start()
    p1.side_in.close()
    p2.side_in.close()
    p3.side_in.close()
    pg.join()

    assert p1.side_out.read().rstrip() == b'spam'
    assert p2.side_out.read().rstrip() == b'eggs'
    assert p3.side_out.read().rstrip() == b'vikings'
