# TODO: As of writing this our only concern is ensuring that the fact feature is reflected in the Host endpoint.
# Other host tests should live here to make this test suite more complete.
import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_basic_fields(hosts, fact_scans, get, user):
    hosts = hosts(host_count=1)

    url = reverse('api:host_detail', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    assert 'related' in response.data
    assert 'fact_versions' in response.data['related']
    assert reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk}) == response.data['related']['fact_versions']

