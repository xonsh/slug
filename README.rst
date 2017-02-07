slug
====

The underlying process management library for `xonsh`_.

Example
-------

.. code:: python

    with ProcessGroup() as pg:
      pipe = mkpipe()
      spam = pg.process(['spam'], stdin=StdIn(), stdout=pipe.side_in, stderr=StdErr(), environ=...)
      eggs = pg.process(['eggs'], stdin=pipe.side_out, stdout=StdOut(), stderr=StdErr(), environ=...)
    pg.start()
    pg.join()

.. _xonsh: http://xon.sh/