"""
__init__.py

Created by Kang Zhang on 2009-07-09
"""

from __future__ import absolute_import

import logging
logger = logging.getLogger('keyring')

from .core import (set_keyring, get_keyring, set_password, get_password,
                  delete_password)
from .getpassbackend import get_password as get_pass_get_password
