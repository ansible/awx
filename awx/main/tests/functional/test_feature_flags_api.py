# -*- coding: utf-8 -*-
import pytest

from awx.main.models import (  # noqa
    User,
)


@pytest.mark.django_db
def test_feature_flags_list_endpoint(get):
    bob = User.objects.create(username='bob', password='test_user', is_superuser=False)

    url = "/api/v2/feature_flags_definition/"
    response = get(url, user=bob, expect=200)
    assert len(response.data) == 1
