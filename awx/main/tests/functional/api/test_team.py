import pytest

from django.core.urlresolvers import reverse

@pytest.mark.django_db
def test_team_role_list_no_read_role(organization_factory, admin, get):
    objects = organization_factory("test_org", teams=["test_team"])
    response = get(reverse('api:team_roles_list', args=(objects.teams.test_team.pk,)), admin)

    assert response.status_code == 200
    assert response.data['results'] == []
