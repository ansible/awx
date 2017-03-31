import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_admin_visible_to_orphaned_users(get, alice):
    names = set()

    response = get(reverse('api:role_list'), user=alice)
    for item in response.data['results']:
        names.add(item['name'])
    assert 'System Auditor' in names
    assert 'System Administrator' in names
