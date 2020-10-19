import collections
import copy
import inspect
import json
import re

# Python LDAP
import ldap
import awx

# Django
from django.utils import six
from django.utils.translation import ugettext_lazy as _

# Django Auth LDAP
import django_auth_ldap.config
from django_auth_ldap.config import (
    LDAPSearch,
    LDAPSearchUnion,
)

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty, Field, SkipField

# This must be imported so get_subclasses picks it up
from awx.sso.ldap_group_types import PosixUIDGroupType  # noqa

# Tower
from awx.conf import fields
from awx.main.validators import validate_certificate
from awx.sso.validators import (  # noqa
    validate_ldap_dn,
    validate_ldap_bind_dn,
    validate_ldap_dn_with_user,
    validate_ldap_filter,
    validate_ldap_filter_with_user,
    validate_tacacsplus_disallow_nonascii,
)


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        for subsubclass in get_subclasses(subclass):
            yield subsubclass
        yield subclass


def find_class_in_modules(class_name):
    '''
    Used to find ldap subclasses by string
    '''
    module_search_space = [django_auth_ldap.config, awx.sso.ldap_group_types]
    for m in module_search_space:
        cls = getattr(m, class_name, None)
        if cls:
            return cls
    return None


class DependsOnMixin():
    def get_depends_on(self):
        """
        Get the value of the dependent field.
        First try to find the value in the request.
        Then fall back to the raw value from the setting in the DB.
        """
        from django.conf import settings
        dependent_key = next(iter(self.depends_on))

        if self.context:
            request = self.context.get('request', None)
            if request and request.data and \
                    request.data.get(dependent_key, None):
                return request.data.get(dependent_key)
        res = settings._get_local(dependent_key, validate=False)
        return res


class _Forbidden(Field):
    default_error_messages = {
        'invalid': _('Invalid field.'),
    }

    def run_validation(self, value):
        self.fail('invalid')


class HybridDictField(fields.DictField):
    """A DictField, but with defined fixed Fields for certain keys.
    """

    def __init__(self, *args, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)

        fields = [
            sorted(
                ((field_name, obj) for field_name, obj in cls.__dict__.items()
                 if isinstance(obj, Field) and field_name != 'child'),
                key=lambda x: x[1]._creation_counter
            )
            for cls in reversed(self.__class__.__mro__)
        ]
        self._declared_fields = collections.OrderedDict(f for group in fields for f in group)

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        fields = copy.deepcopy(self._declared_fields)
        return {
            key: field.to_representation(val) if val is not None else None
            for key, val, field in (
                (six.text_type(key), val, fields.get(key, self.child))
                for key, val in value.items()
            )
            if not field.write_only
        }

    def run_child_validation(self, data):
        result = {}

        if not data and self.allow_blank:
            return result

        errors = collections.OrderedDict()
        fields = copy.deepcopy(self._declared_fields)
        keys = set(fields.keys()) | set(data.keys())

        for key in keys:
            value = data.get(key, empty)
            key = six.text_type(key)
            field = fields.get(key, self.child)
            try:
                if field.read_only:
                    continue  # Ignore read_only fields, as Serializer seems to do.
                result[key] = field.run_validation(value)
            except ValidationError as e:
                errors[key] = e.detail
            except SkipField:
                pass

        if not errors:
            return result
        raise ValidationError(errors)


class AuthenticationBackendsField(fields.StringListField):

    # Mapping of settings that must be set in order to enable each
    # authentication backend.
    REQUIRED_BACKEND_SETTINGS = collections.OrderedDict([
        ('awx.sso.backends.LDAPBackend', [
            'AUTH_LDAP_SERVER_URI',
        ]),
        ('awx.sso.backends.LDAPBackend1', [
            'AUTH_LDAP_1_SERVER_URI',
        ]),
        ('awx.sso.backends.LDAPBackend2', [
            'AUTH_LDAP_2_SERVER_URI',
        ]),
        ('awx.sso.backends.LDAPBackend3', [
            'AUTH_LDAP_3_SERVER_URI',
        ]),
        ('awx.sso.backends.LDAPBackend4', [
            'AUTH_LDAP_4_SERVER_URI',
        ]),
        ('awx.sso.backends.LDAPBackend5', [
            'AUTH_LDAP_5_SERVER_URI',
        ]),
        ('awx.sso.backends.RADIUSBackend', [
            'RADIUS_SERVER',
        ]),
        ('social_core.backends.google.GoogleOAuth2', [
            'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY',
            'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET',
        ]),
        ('social_core.backends.github.GithubOAuth2', [
            'SOCIAL_AUTH_GITHUB_KEY',
            'SOCIAL_AUTH_GITHUB_SECRET',
        ]),
        ('social_core.backends.github.GithubOrganizationOAuth2', [
            'SOCIAL_AUTH_GITHUB_ORG_KEY',
            'SOCIAL_AUTH_GITHUB_ORG_SECRET',
            'SOCIAL_AUTH_GITHUB_ORG_NAME',
        ]),
        ('social_core.backends.github.GithubTeamOAuth2', [
            'SOCIAL_AUTH_GITHUB_TEAM_KEY',
            'SOCIAL_AUTH_GITHUB_TEAM_SECRET',
            'SOCIAL_AUTH_GITHUB_TEAM_ID',
        ]),
        ('social_core.backends.azuread.AzureADOAuth2', [
            'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY',
            'SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET',
        ]),
        ('awx.sso.backends.SAMLAuth', [
            'SOCIAL_AUTH_SAML_SP_ENTITY_ID',
            'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT',
            'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY',
            'SOCIAL_AUTH_SAML_ORG_INFO',
            'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT',
            'SOCIAL_AUTH_SAML_SUPPORT_CONTACT',
            'SOCIAL_AUTH_SAML_ENABLED_IDPS',
        ]),
        ('django.contrib.auth.backends.ModelBackend', []),
    ])

    @classmethod
    def get_all_required_settings(cls):
        all_required_settings = set(['LICENSE'])
        for required_settings in cls.REQUIRED_BACKEND_SETTINGS.values():
            all_required_settings.update(required_settings)
        return all_required_settings

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', self._default_from_required_settings)
        super(AuthenticationBackendsField, self).__init__(*args, **kwargs)

    def _default_from_required_settings(self):
        from django.conf import settings
        try:
            backends = settings._awx_conf_settings._get_default('AUTHENTICATION_BACKENDS')
        except AttributeError:
            backends = self.REQUIRED_BACKEND_SETTINGS.keys()
        # Filter which authentication backends are enabled based on their
        # required settings being defined and non-empty.
        for backend, required_settings in self.REQUIRED_BACKEND_SETTINGS.items():
            if backend not in backends:
                continue
            if all([getattr(settings, rs, None) for rs in required_settings]):
                continue
            backends = [x for x in backends if x != backend]
        return backends


class LDAPServerURIField(fields.URLField):

    def __init__(self, **kwargs):
        kwargs.setdefault('schemes', ('ldap', 'ldaps'))
        kwargs.setdefault('allow_plain_hostname', True)
        super(LDAPServerURIField, self).__init__(**kwargs)

    def run_validators(self, value):
        for url in filter(None, re.split(r'[, ]', (value or ''))):
            super(LDAPServerURIField, self).run_validators(url)
        return value


class LDAPConnectionOptionsField(fields.DictField):

    default_error_messages = {
        'invalid_options': _('Invalid connection option(s): {invalid_options}.'),
    }

    def to_representation(self, value):
        value = value or {}
        opt_names = ldap.OPT_NAMES_DICT
        # Convert integer options to their named constants.
        repr_value = {}
        for opt, opt_value in value.items():
            if opt in opt_names:
                repr_value[opt_names[opt]] = opt_value
        return repr_value

    def to_internal_value(self, data):
        data = super(LDAPConnectionOptionsField, self).to_internal_value(data)
        valid_options = dict([(v, k) for k, v in ldap.OPT_NAMES_DICT.items()])
        invalid_options = set(data.keys()) - set(valid_options.keys())
        if invalid_options:
            invalid_options = sorted(list(invalid_options))
            options_display = json.dumps(invalid_options).lstrip('[').rstrip(']')
            self.fail('invalid_options', invalid_options=options_display)
        # Convert named options to their integer constants.
        internal_data = {}
        for opt_name, opt_value in data.items():
            internal_data[valid_options[opt_name]] = opt_value
        return internal_data


class LDAPDNField(fields.CharField):

    def __init__(self, **kwargs):
        super(LDAPDNField, self).__init__(**kwargs)
        self.validators.append(validate_ldap_dn)

    def run_validation(self, data=empty):
        value = super(LDAPDNField, self).run_validation(data)
        # django-auth-ldap expects DN fields (like AUTH_LDAP_REQUIRE_GROUP)
        # to be either a valid string or ``None`` (not an empty string)
        return None if value == '' else value


class LDAPDNListField(fields.StringListField):

    def __init__(self, **kwargs):
        super(LDAPDNListField, self).__init__(**kwargs)
        self.validators.append(lambda dn: list(map(validate_ldap_dn, dn)))

    def run_validation(self, data=empty):
        if not isinstance(data, (list, tuple)):
            data = [data]
        return super(LDAPDNListField, self).run_validation(data)


class LDAPDNWithUserField(fields.CharField):

    def __init__(self, **kwargs):
        super(LDAPDNWithUserField, self).__init__(**kwargs)
        self.validators.append(validate_ldap_dn_with_user)

    def run_validation(self, data=empty):
        value = super(LDAPDNWithUserField, self).run_validation(data)
        # django-auth-ldap expects DN fields (like AUTH_LDAP_USER_DN_TEMPLATE)
        # to be either a valid string or ``None`` (not an empty string)
        return None if value == '' else value


class LDAPFilterField(fields.CharField):

    def __init__(self, **kwargs):
        super(LDAPFilterField, self).__init__(**kwargs)
        self.validators.append(validate_ldap_filter)


class LDAPFilterWithUserField(fields.CharField):

    def __init__(self, **kwargs):
        super(LDAPFilterWithUserField, self).__init__(**kwargs)
        self.validators.append(validate_ldap_filter_with_user)


class LDAPScopeField(fields.ChoiceField):

    def __init__(self, choices=None, **kwargs):
        choices = choices or [
            ('SCOPE_BASE', _('Base')),
            ('SCOPE_ONELEVEL', _('One Level')),
            ('SCOPE_SUBTREE', _('Subtree')),
        ]
        super(LDAPScopeField, self).__init__(choices, **kwargs)

    def to_representation(self, value):
        for choice in self.choices.keys():
            if value == getattr(ldap, choice):
                return choice
        return super(LDAPScopeField, self).to_representation(value)

    def to_internal_value(self, data):
        value = super(LDAPScopeField, self).to_internal_value(data)
        return getattr(ldap, value)


class LDAPSearchField(fields.ListField):

    default_error_messages = {
        'invalid_length': _('Expected a list of three items but got {length} instead.'),
        'type_error': _('Expected an instance of LDAPSearch but got {input_type} instead.'),
    }
    ldap_filter_field_class = LDAPFilterField

    def to_representation(self, value):
        if not value:
            return []
        if not isinstance(value, LDAPSearch):
            self.fail('type_error', input_type=type(value))
        return [
            LDAPDNField().to_representation(value.base_dn),
            LDAPScopeField().to_representation(value.scope),
            self.ldap_filter_field_class().to_representation(value.filterstr),
        ]

    def to_internal_value(self, data):
        data = super(LDAPSearchField, self).to_internal_value(data)
        if len(data) == 0:
            return None
        if len(data) != 3:
            self.fail('invalid_length', length=len(data))
        return LDAPSearch(
            LDAPDNField().run_validation(data[0]),
            LDAPScopeField().run_validation(data[1]),
            self.ldap_filter_field_class().run_validation(data[2]),
        )


class LDAPSearchWithUserField(LDAPSearchField):

    ldap_filter_field_class = LDAPFilterWithUserField


class LDAPSearchUnionField(fields.ListField):

    default_error_messages = {
        'type_error': _('Expected an instance of LDAPSearch or LDAPSearchUnion but got {input_type} instead.'),
    }
    ldap_search_field_class = LDAPSearchWithUserField

    def to_representation(self, value):
        if not value:
            return []
        elif isinstance(value, LDAPSearchUnion):
            return [self.ldap_search_field_class().to_representation(s) for s in value.searches]
        elif isinstance(value, LDAPSearch):
            return self.ldap_search_field_class().to_representation(value)
        else:
            self.fail('type_error', input_type=type(value))

    def to_internal_value(self, data):
        data = super(LDAPSearchUnionField, self).to_internal_value(data)
        if len(data) == 0:
            return None
        if len(data) == 3 and isinstance(data[0], str):
            return self.ldap_search_field_class().run_validation(data)
        else:
            search_args = []
            for i in range(len(data)):
                if not isinstance(data[i], list):
                    raise ValidationError('In order to ultilize LDAP Union, input element No. %d'
                                          ' should be a search query array.' % (i + 1))
                try:
                    search_args.append(self.ldap_search_field_class().run_validation(data[i]))
                except Exception as e:
                    if hasattr(e, 'detail') and isinstance(e.detail, list):
                        e.detail.insert(0, "Error parsing LDAP Union element No. %d:" % (i + 1))
                    raise e
            return LDAPSearchUnion(*search_args)


class LDAPUserAttrMapField(fields.DictField):

    default_error_messages = {
        'invalid_attrs': _('Invalid user attribute(s): {invalid_attrs}.'),
    }
    valid_user_attrs = {'first_name', 'last_name', 'email'}
    child = fields.CharField()

    def to_internal_value(self, data):
        data = super(LDAPUserAttrMapField, self).to_internal_value(data)
        invalid_attrs = (set(data.keys()) - self.valid_user_attrs)
        if invalid_attrs:
            invalid_attrs = sorted(list(invalid_attrs))
            attrs_display = json.dumps(invalid_attrs).lstrip('[').rstrip(']')
            self.fail('invalid_attrs', invalid_attrs=attrs_display)
        return data


class LDAPGroupTypeField(fields.ChoiceField, DependsOnMixin):

    default_error_messages = {
        'type_error': _('Expected an instance of LDAPGroupType but got {input_type} instead.'),
        'missing_parameters': _('Missing required parameters in {dependency}.')
    }

    def __init__(self, choices=None, **kwargs):
        group_types = get_subclasses(django_auth_ldap.config.LDAPGroupType)
        choices = choices or [(x.__name__, x.__name__) for x in group_types]
        super(LDAPGroupTypeField, self).__init__(choices, **kwargs)

    def to_representation(self, value):
        if not value:
            return 'MemberDNGroupType'
        if not isinstance(value, django_auth_ldap.config.LDAPGroupType):
            self.fail('type_error', input_type=type(value))
        return value.__class__.__name__

    def to_internal_value(self, data):
        data = super(LDAPGroupTypeField, self).to_internal_value(data)
        if not data:
            return None

        params = self.get_depends_on() or {}
        cls = find_class_in_modules(data)
        if not cls:
            return None

        # Per-group type parameter validation and handling here

        # Backwords compatability. Before AUTH_LDAP_GROUP_TYPE_PARAMS existed
        # MemberDNGroupType was the only group type, of the underlying lib, that
        # took a parameter.
        params_sanitized = dict()
        for attr in inspect.getargspec(cls.__init__).args[1:]:
            if attr in params:
                params_sanitized[attr] = params[attr]

        try:
            return cls(**params_sanitized)
        except TypeError:
            self.fail('missing_parameters', dependency=list(self.depends_on)[0])


class LDAPGroupTypeParamsField(fields.DictField, DependsOnMixin):
    default_error_messages = {
        'invalid_keys': _('Invalid key(s): {invalid_keys}.'),
    }

    def to_internal_value(self, value):
        value = super(LDAPGroupTypeParamsField, self).to_internal_value(value)
        if not value:
            return value
        group_type_str = self.get_depends_on()
        group_type_str = group_type_str or ''

        group_type_cls = find_class_in_modules(group_type_str)
        if not group_type_cls:
            # Fail safe
            return {}

        invalid_keys = set(value.keys()) - set(inspect.getargspec(group_type_cls.__init__).args[1:])
        if invalid_keys:
            invalid_keys = sorted(list(invalid_keys))
            keys_display = json.dumps(invalid_keys).lstrip('[').rstrip(']')
            self.fail('invalid_keys', invalid_keys=keys_display)
        return value


class LDAPUserFlagsField(fields.DictField):

    default_error_messages = {
        'invalid_flag': _('Invalid user flag: "{invalid_flag}".'),
    }
    valid_user_flags = {'is_superuser', 'is_system_auditor'}
    child = LDAPDNListField()

    def to_internal_value(self, data):
        data = super(LDAPUserFlagsField, self).to_internal_value(data)
        invalid_flags = (set(data.keys()) - self.valid_user_flags)
        if invalid_flags:
            self.fail('invalid_flag', invalid_flag=list(invalid_flags)[0])
        return data


class LDAPDNMapField(fields.StringListBooleanField):

    child = LDAPDNField()


class LDAPSingleOrganizationMapField(HybridDictField):

    admins = LDAPDNMapField(allow_null=True, required=False)
    users = LDAPDNMapField(allow_null=True, required=False)
    auditors = LDAPDNMapField(allow_null=True, required=False)
    remove_admins = fields.BooleanField(required=False)
    remove_users = fields.BooleanField(required=False)
    remove_auditors = fields.BooleanField(required=False)

    child = _Forbidden()


class LDAPOrganizationMapField(fields.DictField):

    child = LDAPSingleOrganizationMapField()


class LDAPSingleTeamMapField(HybridDictField):

    organization = fields.CharField()
    users = LDAPDNMapField(allow_null=True, required=False)
    remove = fields.BooleanField(required=False)

    child = _Forbidden()


class LDAPTeamMapField(fields.DictField):

    child = LDAPSingleTeamMapField()


class SocialMapStringRegexField(fields.CharField):

    def to_representation(self, value):
        if isinstance(value, type(re.compile(''))):
            flags = []
            if value.flags & re.I:
                flags.append('i')
            if value.flags & re.M:
                flags.append('m')
            return '/{}/{}'.format(value.pattern, ''.join(flags))
        else:
            return super(SocialMapStringRegexField, self).to_representation(value)

    def to_internal_value(self, data):
        data = super(SocialMapStringRegexField, self).to_internal_value(data)
        match = re.match(r'^/(?P<pattern>.*)/(?P<flags>[im]+)?$', data)
        if match:
            flags = 0
            if match.group('flags'):
                if 'i' in match.group('flags'):
                    flags |= re.I
                if 'm' in match.group('flags'):
                    flags |= re.M
            try:
                return re.compile(match.group('pattern'), flags)
            except re.error as e:
                raise ValidationError('{}: {}'.format(e, data))
        return data


class SocialMapField(fields.ListField):

    default_error_messages = {
        'type_error': _('Expected None, True, False, a string or list of strings but got {input_type} instead.'),
    }
    child = SocialMapStringRegexField()

    def to_representation(self, value):
        if isinstance(value, (list, tuple)):
            return super(SocialMapField, self).to_representation(value)
        elif value in fields.NullBooleanField.TRUE_VALUES:
            return True
        elif value in fields.NullBooleanField.FALSE_VALUES:
            return False
        elif value in fields.NullBooleanField.NULL_VALUES:
            return None
        elif isinstance(value, (str, type(re.compile('')))):
            return self.child.to_representation(value)
        else:
            self.fail('type_error', input_type=type(value))

    def to_internal_value(self, data):
        if isinstance(data, (list, tuple)):
            return super(SocialMapField, self).to_internal_value(data)
        elif data in fields.NullBooleanField.TRUE_VALUES:
            return True
        elif data in fields.NullBooleanField.FALSE_VALUES:
            return False
        elif data in fields.NullBooleanField.NULL_VALUES:
            return None
        elif isinstance(data, str):
            return self.child.run_validation(data)
        else:
            self.fail('type_error', input_type=type(data))


class SocialSingleOrganizationMapField(HybridDictField):

    admins = SocialMapField(allow_null=True, required=False)
    users = SocialMapField(allow_null=True, required=False)
    remove_admins = fields.BooleanField(required=False)
    remove_users = fields.BooleanField(required=False)

    child = _Forbidden()


class SocialOrganizationMapField(fields.DictField):

    child = SocialSingleOrganizationMapField()


class SocialSingleTeamMapField(HybridDictField):

    organization = fields.CharField()
    users = SocialMapField(allow_null=True, required=False)
    remove = fields.BooleanField(required=False)

    child = _Forbidden()


class SocialTeamMapField(fields.DictField):

    child = SocialSingleTeamMapField()


class SAMLOrgInfoValueField(HybridDictField):

    name = fields.CharField()
    displayname = fields.CharField()
    url = fields.URLField()


class SAMLOrgInfoField(fields.DictField):

    default_error_messages = {
        'invalid_lang_code': _('Invalid language code(s) for org info: {invalid_lang_codes}.'),
    }
    child = SAMLOrgInfoValueField()

    def to_internal_value(self, data):
        data = super(SAMLOrgInfoField, self).to_internal_value(data)
        invalid_keys = set()
        for key in data.keys():
            if not re.match(r'^[a-z]{2}(?:-[a-z]{2})??$', key, re.I):
                invalid_keys.add(key)
        if invalid_keys:
            invalid_keys = sorted(list(invalid_keys))
            keys_display = json.dumps(invalid_keys).lstrip('[').rstrip(']')
            self.fail('invalid_lang_code', invalid_lang_codes=keys_display)
        return data


class SAMLContactField(HybridDictField):

    givenName = fields.CharField()
    emailAddress = fields.EmailField()


class SAMLIdPField(HybridDictField):

    entity_id = fields.CharField()
    url = fields.URLField()
    x509cert = fields.CharField(validators=[validate_certificate])
    attr_user_permanent_id = fields.CharField(required=False)
    attr_first_name = fields.CharField(required=False)
    attr_last_name = fields.CharField(required=False)
    attr_username = fields.CharField(required=False)
    attr_email = fields.CharField(required=False)


class SAMLEnabledIdPsField(fields.DictField):

    child = SAMLIdPField()


class SAMLSecurityField(HybridDictField):

    nameIdEncrypted = fields.BooleanField(required=False)
    authnRequestsSigned = fields.BooleanField(required=False)
    logoutRequestSigned = fields.BooleanField(required=False)
    logoutResponseSigned = fields.BooleanField(required=False)
    signMetadata = fields.BooleanField(required=False)
    wantMessagesSigned = fields.BooleanField(required=False)
    wantAssertionsSigned = fields.BooleanField(required=False)
    wantAssertionsEncrypted = fields.BooleanField(required=False)
    wantNameId = fields.BooleanField(required=False)
    wantNameIdEncrypted = fields.BooleanField(required=False)
    wantAttributeStatement = fields.BooleanField(required=False)
    requestedAuthnContext = fields.StringListBooleanField(required=False)
    requestedAuthnContextComparison = fields.CharField(required=False)
    metadataValidUntil = fields.CharField(allow_null=True, required=False)
    metadataCacheDuration = fields.CharField(allow_null=True, required=False)
    signatureAlgorithm = fields.CharField(allow_null=True, required=False)
    digestAlgorithm = fields.CharField(allow_null=True, required=False)


class SAMLOrgAttrField(HybridDictField):

    remove = fields.BooleanField(required=False)
    saml_attr = fields.CharField(required=False, allow_null=True)
    remove_admins = fields.BooleanField(required=False)
    saml_admin_attr = fields.CharField(required=False, allow_null=True)
    remove_auditors = fields.BooleanField(required=False)
    saml_auditor_attr = fields.CharField(required=False, allow_null=True)

    child = _Forbidden()


class SAMLTeamAttrTeamOrgMapField(HybridDictField):

    team = fields.CharField(required=True, allow_null=False)
    team_alias = fields.CharField(required=False, allow_null=True)
    organization = fields.CharField(required=True, allow_null=False)
    organization_alias = fields.CharField(required=False, allow_null=True)

    child = _Forbidden()


class SAMLTeamAttrField(HybridDictField):

    team_org_map = fields.ListField(required=False, child=SAMLTeamAttrTeamOrgMapField(), allow_null=True)
    remove = fields.BooleanField(required=False)
    saml_attr = fields.CharField(required=False, allow_null=True)

    child = _Forbidden()
