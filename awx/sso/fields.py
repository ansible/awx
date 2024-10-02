import collections
import copy
import json
import re

import six

# Django
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty, Field, SkipField

# AWX
from awx.conf import fields
from awx.main.validators import validate_certificate


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        for subsubclass in get_subclasses(subclass):
            yield subsubclass
        yield subclass


class DependsOnMixin:
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
            if request and request.data and request.data.get(dependent_key, None):
                return request.data.get(dependent_key)
        res = settings._get_local(dependent_key, validate=False)
        return res


class _Forbidden(Field):
    default_error_messages = {'invalid': _('Invalid field.')}

    def run_validation(self, value):
        self.fail('invalid')


class HybridDictField(fields.DictField):
    """A DictField, but with defined fixed Fields for certain keys."""

    def __init__(self, *args, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)

        fields = [
            sorted(
                ((field_name, obj) for field_name, obj in cls.__dict__.items() if isinstance(obj, Field) and field_name != 'child'),
                key=lambda x: x[1]._creation_counter,
            )
            for cls in reversed(self.__class__.__mro__)
        ]
        self._declared_fields = collections.OrderedDict(f for group in fields for f in group)

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        fields = copy.deepcopy(self._declared_fields)
        return {
            key: field.to_representation(val) if val is not None else None
            for key, val, field in ((six.text_type(key), val, fields.get(key, self.child)) for key, val in value.items())
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
    REQUIRED_BACKEND_SETTINGS = collections.OrderedDict(
        [
            ('social_core.backends.open_id_connect.OpenIdConnectAuth', ['SOCIAL_AUTH_OIDC_KEY', 'SOCIAL_AUTH_OIDC_SECRET', 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT']),
            (
                'awx.sso.backends.SAMLAuth',
                [
                    'SOCIAL_AUTH_SAML_SP_ENTITY_ID',
                    'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT',
                    'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY',
                    'SOCIAL_AUTH_SAML_ORG_INFO',
                    'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT',
                    'SOCIAL_AUTH_SAML_SUPPORT_CONTACT',
                    'SOCIAL_AUTH_SAML_ENABLED_IDPS',
                ],
            ),
            ('django.contrib.auth.backends.ModelBackend', []),
            ('awx.main.backends.AWXModelBackend', []),
        ]
    )

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
    default_error_messages = {'type_error': _('Expected None, True, False, a string or list of strings but got {input_type} instead.')}
    child = SocialMapStringRegexField()

    def to_representation(self, value):
        if isinstance(value, (list, tuple)):
            return super(SocialMapField, self).to_representation(value)
        elif value in fields.BooleanField.TRUE_VALUES:
            return True
        elif value in fields.BooleanField.FALSE_VALUES:
            return False
        elif value in fields.BooleanField.NULL_VALUES:
            return None
        elif isinstance(value, (str, type(re.compile('')))):
            return self.child.to_representation(value)
        else:
            self.fail('type_error', input_type=type(value))

    def to_internal_value(self, data):
        if isinstance(data, (list, tuple)):
            return super(SocialMapField, self).to_internal_value(data)
        elif data in fields.BooleanField.TRUE_VALUES:
            return True
        elif data in fields.BooleanField.FALSE_VALUES:
            return False
        elif data in fields.BooleanField.NULL_VALUES:
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
    organization_alias = SocialMapField(allow_null=True, required=False)

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
    default_error_messages = {'invalid_lang_code': _('Invalid language code(s) for org info: {invalid_lang_codes}.')}
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

    child = _Forbidden()


class SAMLTeamAttrField(HybridDictField):
    team_org_map = fields.ListField(required=False, child=SAMLTeamAttrTeamOrgMapField(), allow_null=True)
    remove = fields.BooleanField(required=False)
    saml_attr = fields.CharField(required=False, allow_null=True)

    child = _Forbidden()


class SAMLUserFlagsAttrField(HybridDictField):
    is_superuser_attr = fields.CharField(required=False, allow_null=True)
    is_superuser_value = fields.StringListField(required=False, allow_null=True)
    is_superuser_role = fields.StringListField(required=False, allow_null=True)
    remove_superusers = fields.BooleanField(required=False, allow_null=True)
    is_system_auditor_attr = fields.CharField(required=False, allow_null=True)
    is_system_auditor_value = fields.StringListField(required=False, allow_null=True)
    is_system_auditor_role = fields.StringListField(required=False, allow_null=True)
    remove_system_auditors = fields.BooleanField(required=False, allow_null=True)

    child = _Forbidden()
