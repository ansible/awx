# Python
import pytest
import json

# Django Rest Framework
from rest_framework.test import APIRequestFactory

# AWX
from awx.api.views import HostList
from awx.main.models import Host, Group, Inventory
from awx.api.versioning import reverse


@pytest.mark.django_db
class TestSearchFilter:
    def test_related_research_filter_relation(self, admin):
        inv = Inventory.objects.create(name="inv")
        group1 = Group.objects.create(name="g1", inventory=inv)
        group2 = Group.objects.create(name="g2", inventory=inv)
        host1 = Host.objects.create(name="host1", inventory=inv)
        host2 = Host.objects.create(name="host2", inventory=inv)
        host3 = Host.objects.create(name="host3", inventory=inv)
        host1.groups.add(group1)
        host2.groups.add(group1)
        host2.groups.add(group2)
        host3.groups.add(group2)
        host1.save()
        host2.save()
        host3.save()
        # Login the client
        factory = APIRequestFactory()
        # Actually test the endpoint.
        host_list_url = reverse('api:host_list')

        # Test if the OR releation works.
        request = factory.get(host_list_url, data={'groups__search': ['g1', 'g2']})
        request.user = admin
        response = HostList.as_view()(request)
        response.render()
        result = json.loads(response.content)
        assert result['count'] == 3
        expected_hosts = ['host1', 'host2', 'host3']
        for i in result['results']:
            expected_hosts.remove(i['name'])
        assert not expected_hosts

        # Test if the AND relation works.
        request = factory.get(host_list_url, data={'groups__search': ['g1,g2']})
        request.user = admin
        response = HostList.as_view()(request)
        response.render()
        result = json.loads(response.content)
        assert result['count'] == 1
        assert result['results'][0]['name'] == 'host2'


@pytest.mark.django_db
class TestHostFilterSecurityGuard:
    """Regression tests: crafted host_filter values must not leak internals.

    Before the fix, the HostList view caught all exceptions and returned
    their str() verbatim, exposing Django FieldError schema dumps and raw
    PostgreSQL errors.  After the fix:
      - SmartFilter._expand_search validates the relation is a real Host
        field, raising ParseException (wrapped as RuntimeError) for
        anything else.
      - HostList.list splits error handling: RuntimeError still echoes its
        message; any other Exception returns a generic "Invalid host
        filter." string.
    """

    def _get_host_list(self, admin, host_filter):
        factory = APIRequestFactory()
        host_list_url = reverse('api:host_list')
        request = factory.get(host_list_url, data={'host_filter': host_filter})
        request.user = admin
        response = HostList.as_view()(request)
        response.render()
        return response

    # -- reject direction ------------------------------------------------

    def test_invalid_search_relation_rejected(self, admin):
        """credential__search=x must not leak a Django FieldError."""
        inv = Inventory.objects.create(name="inv")
        Host.objects.create(name="h1", inventory=inv)

        response = self._get_host_list(admin, 'credential__search=x')
        body = response.content.decode()

        assert response.status_code == 400
        # The FieldError schema dump must not appear in the response.
        assert 'Cannot resolve keyword' not in body
        assert 'Choices are:' not in body

    def test_invalid_regex_returns_generic_error(self, admin):
        """name__regex=[bad must not leak a raw PostgreSQL DataError."""
        inv = Inventory.objects.create(name="inv")
        Host.objects.create(name="h1", inventory=inv)

        response = self._get_host_list(admin, 'name__regex=[bad')
        body = response.content.decode()

        assert response.status_code == 400
        assert 'invalid regular expression' not in body
        assert 'Invalid host filter.' in body

    # -- permit direction -------------------------------------------------

    def test_plain_search_still_works(self, admin):
        """host_filter=search=h1 must still return the matching host."""
        inv = Inventory.objects.create(name="inv")
        Host.objects.create(name="h1", inventory=inv)
        Host.objects.create(name="other", inventory=inv)

        response = self._get_host_list(admin, 'search=h1')
        result = json.loads(response.content)

        assert response.status_code == 200
        assert result['count'] == 1
        assert result['results'][0]['name'] == 'h1'

    def test_valid_related_search_still_works(self, admin):
        """inventory__search=<name> must work (inventory is a Host field)."""
        inv = Inventory.objects.create(name="findme-inv")
        Host.objects.create(name="h1", inventory=inv)

        response = self._get_host_list(admin, 'inventory__search=findme')
        result = json.loads(response.content)

        assert response.status_code == 200
        assert result['count'] == 1
        assert result['results'][0]['name'] == 'h1'
