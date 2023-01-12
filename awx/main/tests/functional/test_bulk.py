import pytest

from uuid import uuid4

from awx.api.versioning import reverse

import json
from contextlib import contextmanager
from django.test.utils import CaptureQueriesContext
from django.db import connections


@contextmanager
def withAssertNumQueriesLessThan(num_queries):
    with CaptureQueriesContext(connections['default']) as context:
        yield
        fail_msg = f"\r\n{json.dumps(context.captured_queries, indent=4)}"
    assert len(context.captured_queries) < num_queries, fail_msg


@pytest.mark.django_db
@pytest.mark.parametrize('num_hosts, num_queries', [(9, 15), (99, 20), (999, 25)])
def test_bulk_host_create_num_queries(organization, inventory, post, get, user, num_hosts, num_queries):
    '''
    If I am a...
      org admin
      inventory admin at org level
      admin of a particular inventory
      superuser

    Bulk Host create should take under a certain number of queries
    '''
    inventory.organization = organization
    inventory_admin = user('inventory_admin', False)
    org_admin = user('org_admin', False)
    org_inv_admin = user('org_admin', False)
    superuser = user('admin', True)
    for u in [org_admin, org_inv_admin, inventory_admin]:
        organization.member_role.members.add(u)
    organization.admin_role.members.add(org_admin)
    organization.inventory_admin_role.members.add(org_inv_admin)
    inventory.admin_role.members.add(inventory_admin)

    for u in [org_admin, inventory_admin, org_inv_admin, superuser]:
        hosts = [{'name': uuid4()} for i in range(num_hosts)]
        with withAssertNumQueriesLessThan(num_queries):
            bulk_host_create_response = post(reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': hosts}, u, expect=201).data
            assert bulk_host_create_response['created'] == len(hosts), f"unexpected number of hosts created for user {u}"


@pytest.mark.django_db
def test_bulk_host_create_rbac(organization, inventory, post, get, user):
    '''
    If I am a...
      org admin
      inventory admin at org level
      admin of a particular invenotry
          ... I can bulk add hosts

    Everyone else cannot
    '''
    inventory.organization = organization
    inventory_admin = user('inventory_admin', False)
    org_admin = user('org_admin', False)
    org_inv_admin = user('org_admin', False)
    auditor = user('auditor', False)
    member = user('member', False)
    use_inv_member = user('member', False)
    for u in [org_admin, org_inv_admin, auditor, member, inventory_admin, use_inv_member]:
        organization.member_role.members.add(u)
    organization.admin_role.members.add(org_admin)
    organization.inventory_admin_role.members.add(org_inv_admin)
    inventory.admin_role.members.add(inventory_admin)
    inventory.use_role.members.add(use_inv_member)
    organization.auditor_role.members.add(auditor)

    for indx, u in enumerate([org_admin, inventory_admin, org_inv_admin]):
        bulk_host_create_response = post(
            reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': [{'name': f'foobar-{indx}'}]}, u, expect=201
        ).data
        assert bulk_host_create_response['created'] == 1, f"unexpected number of hosts created for user {u}"

    for indx, u in enumerate([member, auditor, use_inv_member]):
        bulk_host_create_response = post(
            reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': [{'name': f'foobar2-{indx}'}]}, u, expect=400
        ).data
