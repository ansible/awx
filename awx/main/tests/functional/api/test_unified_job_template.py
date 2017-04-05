import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_aliased_forward_reverse_field_searches(instance, options, get, admin):
    url = reverse('api:unified_job_template_list')
    response = options(url, None, admin)
    assert 'job_template__search' in response.data['related_search_fields']
    get(reverse("api:unified_job_template_list") + "?job_template__search=anything", user=admin, expect=200)
