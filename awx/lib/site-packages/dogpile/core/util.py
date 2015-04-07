import sys
py3k = sys.version_info >= (3, 0)

try:
    import threading
except ImportError:
    import dummy_threading as threading

