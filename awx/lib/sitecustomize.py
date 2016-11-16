# Python
import os
import sys

# Based on http://stackoverflow.com/a/6879344/131141 -- Initialize tower display
# callback as early as possible to wrap ansible.display.Display methods.


def argv_ready(argv):
    if argv and os.path.basename(argv[0]) in {'ansible', 'ansible-playbook'}:
        import tower_display_callback  # noqa


class argv_placeholder(object):

    def __del__(self):
        argv_ready(sys.argv)


if hasattr(sys, 'argv'):
    argv_ready(sys.argv)
else:
    sys.argv = argv_placeholder()
