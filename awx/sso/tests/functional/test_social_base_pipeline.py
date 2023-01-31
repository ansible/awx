import pytest

from awx.main.models import User
from awx.sso.social_base_pipeline import AuthNotFound, check_user_found_or_created, set_is_active_for_new_user, prevent_inactive_login, AuthInactive


@pytest.mark.django_db
class TestSocialBasePipeline:
    def test_check_user_found_or_created_no_exception(self):
        # If we have a user (the True param, we should not get an exception)
        try:
            check_user_found_or_created(None, {}, True)
        except AuthNotFound:
            assert False, 'check_user_found_or_created should not have raised an exception with a user'

    @pytest.mark.parametrize(
        "details, kwargs, expected_id",
        [
            (
                {},
                {},
                '???',
            ),
            (
                {},
                {'uid': 'kwargs_uid'},
                'kwargs_uid',
            ),
            (
                {},
                {'uid': 'kwargs_uid', 'email': 'kwargs_email'},
                'kwargs_email',
            ),
            (
                {'email': 'details_email'},
                {'uid': 'kwargs_uid', 'email': 'kwargs_email'},
                'details_email',
            ),
        ],
    )
    def test_check_user_found_or_created_exceptions(self, details, expected_id, kwargs):
        with pytest.raises(AuthNotFound) as e:
            check_user_found_or_created(None, details, False, None, **kwargs)
        assert f'An account cannot be found for {expected_id}' == str(e.value)

    @pytest.mark.parametrize(
        "kwargs, expected_details, expected_response",
        [
            ({}, {}, None),
            ({'is_new': False}, {}, None),
            ({'is_new': True}, {'is_active': True}, {'details': {'is_active': True}}),
        ],
    )
    def test_set_is_active_for_new_user(self, kwargs, expected_details, expected_response):
        details = {}
        response = set_is_active_for_new_user(None, details, None, None, **kwargs)
        assert details == expected_details
        assert response == expected_response

    def test_prevent_inactive_login_no_exception_no_user(self):
        try:
            prevent_inactive_login(None, None, None, None, None)
        except AuthInactive:
            assert False, 'prevent_inactive_login should not have raised an exception with no user'

    def test_prevent_inactive_login_no_exception_active_user(self):
        user = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com', is_active=True)
        try:
            prevent_inactive_login(None, None, user, None, None)
        except AuthInactive:
            assert False, 'prevent_inactive_login should not have raised an exception with an active user'

    def test_prevent_inactive_login_no_exception_inactive_user(self):
        user = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com', is_active=False)
        with pytest.raises(AuthInactive):
            prevent_inactive_login(None, None, user, None, None)
