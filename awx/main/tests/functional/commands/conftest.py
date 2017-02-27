import pytest
import time

from datetime import datetime


@pytest.fixture
def fact_msg_base(inventory, hosts):
    host_objs = hosts(1)
    return {
        'host': host_objs[0].name,
        'date_key': time.mktime(datetime.utcnow().timetuple()),
        'facts' : { },
        'inventory_id': inventory.id
    }


@pytest.fixture
def fact_msg_small(fact_msg_base):
    fact_msg_base['facts'] = {
        'packages': {
            "accountsservice": [
                {
                    "architecture": "amd64",
                    "name": "accountsservice",
                    "source": "apt",
                    "version": "0.6.35-0ubuntu7.1"
                }
            ],
            "acpid": [
                {
                    "architecture": "amd64",
                    "name": "acpid",
                    "source": "apt",
                    "version": "1:2.0.21-1ubuntu2"
                }
            ],
            "adduser": [
                {
                    "architecture": "all",
                    "name": "adduser",
                    "source": "apt",
                    "version": "3.113+nmu3ubuntu3"
                }
            ],
        },
        'services': [
            {
                "name": "acpid",
                "source": "sysv",
                "state": "running"
            },
            {
                "name": "apparmor",
                "source": "sysv",
                "state": "stopped"
            },
            {
                "name": "atd",
                "source": "sysv",
                "state": "running"
            },
            {
                "name": "cron",
                "source": "sysv",
                "state": "running"
            }
        ],
        'ansible': {
            'ansible_fact_simple': 'hello world',
            'ansible_fact_complex': {
                'foo': 'bar',
                'hello': [
                    'scooby',
                    'dooby',
                    'doo'
                ]
            },
        }
    }
    return fact_msg_base


'''
Facts sent from ansible to our fact cache reciever.
The fact module type is implicit i.e

Note: The 'ansible' module is an expection to this rule.
It is NOT nested in a dict, and thus does NOT contain a first-level
key of 'ansible'

{
    'fact_module_name': { ... },
}
'''


@pytest.fixture
def fact_msg_ansible(fact_msg_base, fact_ansible_json):
    fact_msg_base['facts'] = fact_ansible_json
    return fact_msg_base


@pytest.fixture
def fact_msg_packages(fact_msg_base, fact_packages_json):
    fact_msg_base['facts']['packages'] = fact_packages_json
    return fact_msg_base


@pytest.fixture
def fact_msg_services(fact_msg_base, fact_services_json):
    fact_msg_base['facts']['services'] = fact_services_json
    return fact_msg_base
