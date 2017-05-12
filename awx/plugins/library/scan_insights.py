#!/usr/bin/env python

from ansible.module_utils.basic import * # noqa
import uuid

DOCUMENTATION = '''
---
module: scan_insights
short_description: Return insights UUID as fact data
description:
    - Inspects the /etc/redhat-access-insights/machine-id file for insights uuid and returns the found UUID as fact data
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


def get_system_uuid(filname):
    system_uuid = None
    try:
        f = open(INSIGHTS_SYSTEM_ID_FILE, "r")
    except IOError:
        return None
    else:
        try:
            data = f.readline()
            system_uuid = str(uuid.UUID(data))
        except (IOError, ValueError):
            pass
        finally:
            f.close()
            return system_uuid


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )

    system_uuid = get_system_uuid(INSIGHTS_SYSTEM_ID_FILE)

    if system_uuid is not None:
        results = {
            'ansible_facts': {
                'insights': {
                    'system_id': system_uuid
                }
            }
        }
    else:
        results = dict(skipped=True, msg="Insights system id not found")
    module.exit_json(**results)


main()
