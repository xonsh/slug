from .base import *  # noqa

import os
import sys

if os.name == 'nt':  # Windows
    from .win import *  # noqa
elif os.name == 'posix':  # Posix
    from .posix import *  # noqa
    if sys.platform == 'linux':
        pass
    elif sys.platform == 'darwin':
        pass
    elif sys.platform == 'cygwin':
        pass

from .plumbing import *  # noqa
