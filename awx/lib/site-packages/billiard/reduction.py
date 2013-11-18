from __future__ import absolute_import

import sys

if sys.version_info[0] == 3:
    from . import _reduction3 as reduction
else:
    from . import _reduction as reduction  # noqa

sys.modules[__name__] = reduction
