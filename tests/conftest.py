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
