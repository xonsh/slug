slug
====

.. image:: https://badges.gitter.im/xonsh/xonsh.svg
   :alt: Join the chat at https://gitter.im/xonsh/xonsh
   :target: https://gitter.im/xonsh/xonsh?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://travis-ci.org/xonsh/slug.svg?branch=master
    :target: https://travis-ci.org/xonsh/slug

.. image:: https://ci.appveyor.com/api/projects/status/github/xonsh/slug?svg=true
    :target: https://ci.appveyor.com/project/xonsh/slug

.. image:: https://landscape.io/github/xonsh/slug/master/landscape.svg?style=flat
    :target: https://landscape.io/github/xonsh/slug/master
    :alt: Code Health

.. image:: https://codecov.io/gh/xonsh/slug/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/xonsh/slug

The underlying process management library for `xonsh`_.

Example
-------

.. code:: python

    with ProcessGroup() as pg:
      pipe = Pipe()
      spam = pg.add(Process(['spam'], stdout=pipe.side_in))
      eggs = pg.add(Process(['eggs'], stdin=pipe.side_out))
    pg.start()
    pg.join()

.. _xonsh: http://xon.sh/
