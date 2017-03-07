"""
Private utilities.
"""
import threading
import ctypes


def thread_async_raise(thread: threading.Thread, exception: type):
    """
    "Asynchronously raise an exception in a thread. The id argument is the
    thread id of the target thread; exc is the exception object to be raised.
    This function does not steal any references to exc. To prevent naive misuse,
    you must write your own C extension to call this. Must be called with the
    GIL held. Returns the number of thread states modified; this is normally
    one, but will be zero if the thread id isn’t found. If exc is NULL, the
    pending exception (if any) for the thread is cleared. This raises no
    exceptions."
    """
    if not issubclass(exception, BaseException):
        raise TypeError("Only Exception types can be raised (not instances)")
    if thread.ident is None:
        raise ValueError("Thread not started")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident),
        ctypes.py_object(exception),
    )
    if res == 0:
        raise ValueError("Invalid thread")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, 0)
        raise RuntimeError("PyThreadState_SetAsyncExc affected {} threads".format(res))
