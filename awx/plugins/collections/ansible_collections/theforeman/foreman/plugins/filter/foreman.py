# Copyright (c) 2019 Matthias Dellweg
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


import re


def cp_label(value):
    p = re.compile(r'[^-\w]+')
    return p.sub('_', value)


# ---- Ansible filters ----
class FilterModule(object):
    ''' Foreman filter '''

    def filters(self):
        return {
            'cp_label': cp_label,
        }
