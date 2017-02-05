from .utils import *

if False:  # Windows
    from .win import *
elif False:  # Posix
    from .posix import *
else:
    # Maybe a subprocess-based executer?
    raise RuntimeError("Your platform is not supported.")
