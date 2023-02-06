import pytest
from awx.sso.backends import _update_m2m_from_groups


class MockLDAPGroups(object):
    def is_member_of(self, group_dn):
        return bool(group_dn)


class MockLDAPUser(object):
    def _get_groups(self):
        return MockLDAPGroups()


@pytest.mark.parametrize(
    "setting, expected_result",
    [
        (True, True),
        ('something', True),
        (False, False),
        ('', False),
    ],
)
def test_mock_objects(setting, expected_result):
    ldap_user = MockLDAPUser()
    assert ldap_user._get_groups().is_member_of(setting) == expected_result


@pytest.mark.parametrize(
    "opts, remove, expected_result",
    [
        # In these case we will pass no opts so we should get None as a return in all cases
        (
            None,
            False,
            None,
        ),
        (
            None,
            True,
            None,
        ),
        # Next lets test with empty opts ([]) This should return False if remove is True and None otherwise
        (
            [],
            True,
            False,
        ),
        (
            [],
            False,
            None,
        ),
        # Next opts is True, this will always return True
        (
            True,
            True,
            True,
        ),
        (
            True,
            False,
            True,
        ),
        # If we get only a non-string as an option we hit a continue and will either return None or False depending on the remove flag
        (
            [32],
            False,
            None,
        ),
        (
            [32],
            True,
            False,
        ),
        # Finally we need to test whether or not a user should be allowed in or not.
        # We use a mock class for ldap_user that simply returns true/false based on the otps
        (
            ['true'],
            False,
            True,
        ),
        # In this test we are going to pass a string to test the part of the code that coverts strings into array, this should give us True
        (
            'something',
            True,
            True,
        ),
        (
            [''],
            False,
            None,
        ),
        (
            False,
            True,
            False,
        ),
        # Empty strings are considered opts == None and will result in None or False based on the remove flag
        (
            '',
            True,
            False,
        ),
        (
            '',
            False,
            None,
        ),
    ],
)
@pytest.mark.django_db
def test__update_m2m_from_groups(opts, remove, expected_result):
    ldap_user = MockLDAPUser()
    assert expected_result == _update_m2m_from_groups(ldap_user, opts, remove)
