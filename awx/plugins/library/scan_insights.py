#!/usr/bin/env python

from ansible.module_utils.basic import * # noqa

DOCUMENTATION = '''
---
module: scan_insights
short_description: Return insights id as fact data
description:
    - Inspects the /etc/redhat-access-insights/machine-id file for insights id and returns the found id as fact data
version_added: "2.3"
options:
requirements: [ ]
author: Chris Meyers
'''

EXAMPLES = '''
# Example fact output:
# host | success >> {
#    "ansible_facts": {
#        "insights": {
#           "system_id": "4da7d1f8-14f3-4cdc-acd5-a3465a41f25d"
#        }, ... }
'''


INSIGHTS_SYSTEM_ID_FILE='/etc/redhat-access-insights/machine-id'


def get_system_id(filname):
    system_id = None
    try:
        f = open(INSIGHTS_SYSTEM_ID_FILE, "r")
    except IOError:
        return None
    else:
        try:
            data = f.readline()
            system_id = str(data)
        except (IOError, ValueError):
            pass
        finally:
            f.close()
            if system_id:
                system_id = system_id.strip()
            return system_id


def main():
    module = AnsibleModule(  # noqa
        argument_spec = dict()
    )

    system_id = get_system_id(INSIGHTS_SYSTEM_ID_FILE)

    results = {
        'ansible_facts': {
            'insights': {
                'system_id': system_id
            }
        }
    }
    module.exit_json(**results)


main()
