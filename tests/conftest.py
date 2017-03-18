import os
import sys
import pytest


# Blatently stolen from
# http://doc.pytest.org/en/latest/example/markers.html#marking-platform-specific-tests-with-pytest
ALL = set("darwin linux win32".split())


def pytest_runtest_setup(item):
    if isinstance(item, item.Function):
        plat = sys.platform
        if not item.get_marker(plat):
            if ALL.intersection(item.keywords):
                pytest.skip("cannot run on platform %s" % (plat))

# End blatent stealing


def runpy(code):
    return [sys.executable, '-c', code]


def not_in_path(*progs):
    bindirs = os.environ['PATH'].split(os.pathsep)
    for prog in progs:
        if not any(os.path.exists(os.path.join(bd, prog)) for bd in bindirs):
            return True
    else:
        return False
