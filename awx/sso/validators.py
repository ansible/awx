# Python
import re

# Python-LDAP
import ldap

# Django
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

__all__ = ['validate_ldap_dn', 'validate_ldap_dn_with_user',
           'validate_ldap_bind_dn', 'validate_ldap_filter',
           'validate_ldap_filter_with_user',
           'validate_tacacsplus_disallow_nonascii']


def validate_ldap_dn(value, with_user=False):
    if with_user:
        if '%(user)s' not in value:
            raise ValidationError(_('DN must include "%%(user)s" placeholder for username: %s') % value)
        dn_value = value.replace('%(user)s', 'USER')
    else:
        dn_value = value
    try:
        ldap.dn.str2dn(dn_value.encode('utf-8'))
    except ldap.DECODING_ERROR:
        raise ValidationError(_('Invalid DN: %s') % value)


def validate_ldap_dn_with_user(value):
    validate_ldap_dn(value, with_user=True)


def validate_ldap_bind_dn(value):
    if not re.match(r'^[A-Za-z][A-Za-z0-9._-]*?\\[A-Za-z0-9 ._-]+?$', value.strip()) and \
            not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value.strip()):
        validate_ldap_dn(value)


def validate_ldap_filter(value, with_user=False):
    value = value.strip()
    if not value:
        return
    if with_user:
        if '%(user)s' not in value:
            raise ValidationError(_('DN must include "%%(user)s" placeholder for username: %s') % value)
        dn_value = value.replace('%(user)s', 'USER')
    else:
        dn_value = value
    if re.match(r'^\([A-Za-z0-9-]+?=[^()]+?\)$', dn_value):
        return
    elif re.match(r'^\([&|!]\(.*?\)\)$', dn_value):
        try:
            map(validate_ldap_filter, ['(%s)' % x for x in dn_value[3:-2].split(')(')])
            return
        except ValidationError:
            pass
    raise ValidationError(_('Invalid filter: %s') % value)


def validate_ldap_filter_with_user(value):
    validate_ldap_filter(value, with_user=True)


def validate_tacacsplus_disallow_nonascii(value):
    try:
        value.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        raise ValidationError(_('TACACS+ secret does not allow non-ascii characters'))
