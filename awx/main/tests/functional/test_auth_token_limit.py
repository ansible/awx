import pytest
from datetime import timedelta

from django.utils.timezone import now as tz_now
from django.test.utils import override_settings

from awx.main.models import AuthToken, User


@override_settings(AUTH_TOKEN_PER_USER=3)
@pytest.mark.django_db
def test_get_tokens_over_limit():
    now = tz_now()
    # Times are relative to now
    # (key, created on in seconds , expiration in seconds)
    test_data = [
        # a is implicitly expired
        ("a", -1000, -10),
        # b's are invalid due to session limit of 3
        ("b", -100, 60),
        ("bb", -100, 60),
        ("c", -90, 70),
        ("d", -80, 80),
        ("e", -70, 90),
    ]
    user = User.objects.create_superuser('admin', 'foo@bar.com', 'password')
    for key, t_create, t_expire in test_data:
        AuthToken.objects.create(
            user=user,
            key=key,
            request_hash='this_is_a_hash',
            created=now + timedelta(seconds=t_create),
            expires=now + timedelta(seconds=t_expire),
        )
    invalid_tokens = AuthToken.get_tokens_over_limit(user, now=now)
    invalid_keys = [x.key for x in invalid_tokens]
    assert len(invalid_keys) == 2
    assert 'b' in invalid_keys
    assert 'bb' in invalid_keys
