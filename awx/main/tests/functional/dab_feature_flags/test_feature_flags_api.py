import pytest
from flags.state import get_flags, flag_state
from ansible_base.feature_flags.models import AAPFlag
from ansible_base.feature_flags.utils import create_initial_data as seed_feature_flags
from django.conf import settings
from awx.main.models import User


@pytest.mark.django_db
def test_feature_flags_list_endpoint(get):
    bob = User.objects.create(username='bob', password='test_user', is_superuser=True)
    url = "/api/v2/feature_flags/states/"
    response = get(url, user=bob, expect=200)
    assert len(get_flags()) > 0
    assert len(response.data["results"]) == len(get_flags())


@pytest.mark.django_db
@pytest.mark.parametrize('flag_val', (True, False))
def test_feature_flags_list_endpoint_override(get, flag_val):
    bob = User.objects.create(username='bob', password='test_user', is_superuser=True)

    AAPFlag.objects.all().delete()
    flag_name = "FEATURE_DISPATCHERD_ENABLED"
    setattr(settings, flag_name, flag_val)
    seed_feature_flags()
    url = "/api/v2/feature_flags/states/"
    response = get(url, user=bob, expect=200)
    assert len(response.data["results"]) == 5
    assert flag_state(flag_name) == flag_val
