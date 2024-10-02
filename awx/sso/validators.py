# Django
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

__all__ = [
    'validate_tacacsplus_disallow_nonascii',
]


def validate_tacacsplus_disallow_nonascii(value):
    try:
        value.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        raise ValidationError(_('TACACS+ secret does not allow non-ascii characters'))
