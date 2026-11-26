# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # Automation Platform Controller documentation fragment
    DOCUMENTATION = r'''
options:
  aap_session_id:
    description:
    - Authenticate using session cookies obtained via other means such as Single Sign-On.
    - This is a dictionary requiring two keys, C(csrftoken) and C(gateway_sessionid),
      which are provided as authentication cookies.
    - If value not set, will try environment variable C(AAP_SESSION_ID) and then
      C(CONTROLLER_SESSION_ID) or C(GATEWAY_SESSION_ID).
    type: dict
    required: False
    version_added: "4.6.0"
    aliases: [ controller_session_id, gateway_session_id ]
'''


