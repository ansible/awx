import pytest

from django.test.utils import override_settings

from rest_framework.serializers import ValidationError

from awx.api.serializers import UserSerializer
from django.contrib.auth.models import User


@pytest.mark.parametrize(
    "password,min_length,min_digits,min_upper,min_special,expect_error",
    [
        # Test length
        ("a", 1, 0, 0, 0, False),
        ("a", 2, 0, 0, 0, True),
        ("aa", 2, 0, 0, 0, False),
        ("aaabcDEF123$%^", 2, 0, 0, 0, False),
        # Test digits
        ("a", 0, 1, 0, 0, True),
        ("1", 0, 1, 0, 0, False),
        ("1", 0, 2, 0, 0, True),
        ("12", 0, 2, 0, 0, False),
        ("12abcDEF123$%^", 0, 2, 0, 0, False),
        # Test upper
        ("a", 0, 0, 1, 0, True),
        ("A", 0, 0, 1, 0, False),
        ("A", 0, 0, 2, 0, True),
        ("AB", 0, 0, 2, 0, False),
        ("ABabcDEF123$%^", 0, 0, 2, 0, False),
        # Test special
        ("a", 0, 0, 0, 1, True),
        ("!", 0, 0, 0, 1, False),
        ("!", 0, 0, 0, 2, True),
        ("!@", 0, 0, 0, 2, False),
        ("!@abcDEF123$%^", 0, 0, 0, 2, False),
    ],
)
@pytest.mark.django_db
def test_validate_password_rules(password, min_length, min_digits, min_upper, min_special, expect_error):
    user_serializer = UserSerializer()

    # First test password with no params, this should always pass
    try:
        user_serializer.validate_password(password)
    except ValidationError:
        assert False, f"Password {password} should not have validation issue if no params are used"

    with override_settings(
        LOCAL_PASSWORD_MIN_LENGTH=min_length, LOCAL_PASSWORD_MIN_DIGITS=min_digits, LOCAL_PASSWORD_MIN_UPPER=min_upper, LOCAL_PASSWORD_MIN_SPECIAL=min_special
    ):
        if expect_error:
            with pytest.raises(ValidationError):
                user_serializer.validate_password(password)
        else:
            try:
                user_serializer.validate_password(password)
            except ValidationError:
                assert False, "validate_password raised an unexpected exception"


@pytest.mark.django_db
def test_validate_password_too_long():
    password_max_length = User._meta.get_field('password').max_length
    password = "x" * password_max_length

    user_serializer = UserSerializer()
    try:
        user_serializer.validate_password(password)
    except ValidationError:
        assert False, f"Password {password} should not have validation"

    password = f"{password}x"
    with pytest.raises(ValidationError):
        user_serializer.validate_password(password)
