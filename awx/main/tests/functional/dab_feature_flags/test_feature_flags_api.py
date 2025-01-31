import pytest
from django.test import override_settings

from awx.main.models import User


@pytest.mark.django_db
def test_feature_flags_list_endpoint(get):
    bob = User.objects.create(username='bob', password='test_user', is_superuser=False)

    url = "/api/v2/feature_flags_state/"
    response = get(url, user=bob, expect=200)
    assert len(response.data) == 1


@override_settings(
    FLAGS={
        "FEATURE_SOME_PLATFORM_FLAG_ENABLED": [
            {"condition": "boolean", "value": False},
            {"condition": "before date", "value": "2022-06-01T12:00Z"},
        ],
        "FEATURE_SOME_PLATFORM_FLAG_FOO_ENABLED": [
            {"condition": "boolean", "value": True},
        ],
    }
)
@pytest.mark.django_db
def test_feature_flags_list_endpoint_override(get):
    bob = User.objects.create(username='bob', password='test_user', is_superuser=False)

    url = "/api/v2/feature_flags_state/"
    response = get(url, user=bob, expect=200)
    assert len(response.data) == 2
    assert response.data["FEATURE_SOME_PLATFORM_FLAG_ENABLED"] is False
    assert response.data["FEATURE_SOME_PLATFORM_FLAG_FOO_ENABLED"] is True
