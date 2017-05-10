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
#           "machine_id": "4da7d1f8-14f3-4cdc-acd5-a3465a41f25d"
#        }, ... }
'''


INSIGHTS_MACHINE_ID_FILE='/etc/redhat-access-insights/machine-id'


def get_machine_uuid(filname):
    machine_uuid = None
    try:
        f = open(INSIGHTS_MACHINE_ID_FILE, "r")
    except IOError:
        return None
    else:
        try:
            data = f.readline()
            machine_uuid = str(uuid.UUID(data))
        except (IOError, ValueError):
            pass
        finally:
            f.close()
            return machine_uuid


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )

    machine_uuid = get_machine_uuid(INSIGHTS_MACHINE_ID_FILE)

    if machine_uuid is not None:
        results = {
            'ansible_facts': {
                'insights': {
                    'machine_id': machine_uuid
                }
            }
        }
    else:
        results = dict(skipped=True, msg="Insights machine id not found")
    module.exit_json(**results)


main()
