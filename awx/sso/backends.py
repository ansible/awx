# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.utils.encoding import force_str
from django.http import HttpResponse

# radiusauth
from radiusauth.backends import RADIUSBackend as BaseRADIUSBackend

# tacacs+ auth
import tacacs_plus

# social
from social_core.backends.saml import OID_USERID
from social_core.backends.saml import SAMLAuth as BaseSAMLAuth
from social_core.backends.saml import SAMLIdentityProvider as BaseSAMLIdentityProvider

# Ansible Tower
from awx.sso.models import UserEnterpriseAuth

logger = logging.getLogger('awx.sso.backends')


def _decorate_enterprise_user(user, provider):
    user.set_unusable_password()
    user.save()
    enterprise_auth, _ = UserEnterpriseAuth.objects.get_or_create(user=user, provider=provider)
    return enterprise_auth


def _get_or_set_enterprise_user(username, password, provider):
    created = False
    try:
        user = User.objects.prefetch_related('enterprise_auth').get(username=username)
    except User.DoesNotExist:
        user = User(username=username)
        enterprise_auth = _decorate_enterprise_user(user, provider)
        logger.debug("Created enterprise user %s via %s backend." % (username, enterprise_auth.get_provider_display()))
        created = True
    if created or user.is_in_enterprise_category(provider):
        return user
    logger.warning("Enterprise user %s already defined in Tower." % username)


class RADIUSBackend(BaseRADIUSBackend):
    """
    Custom Radius backend to verify license status
    """

    def authenticate(self, request, username, password):
        if not django_settings.RADIUS_SERVER:
            return None
        return super(RADIUSBackend, self).authenticate(request, username, password)

    def get_user(self, user_id):
        if not django_settings.RADIUS_SERVER:
            return None
        user = super(RADIUSBackend, self).get_user(user_id)
        if not user.has_usable_password():
            return user

    def get_django_user(self, username, password=None, groups=[], is_staff=False, is_superuser=False):
        return _get_or_set_enterprise_user(force_str(username), force_str(password), 'radius')


class TACACSPlusBackend(object):
    """
    Custom TACACS+ auth backend for AWX
    """

    def authenticate(self, request, username, password):
        if not django_settings.TACACSPLUS_HOST:
            return None
        try:
            # Upstream TACACS+ client does not accept non-string, so convert if needed.
            tacacs_client = tacacs_plus.TACACSClient(
                django_settings.TACACSPLUS_HOST,
                django_settings.TACACSPLUS_PORT,
                django_settings.TACACSPLUS_SECRET,
                timeout=django_settings.TACACSPLUS_SESSION_TIMEOUT,
            )
            auth_kwargs = {'authen_type': tacacs_plus.TAC_PLUS_AUTHEN_TYPES[django_settings.TACACSPLUS_AUTH_PROTOCOL]}
            if django_settings.TACACSPLUS_AUTH_PROTOCOL:
                client_ip = self._get_client_ip(request)
                if client_ip:
                    auth_kwargs['rem_addr'] = client_ip
            auth = tacacs_client.authenticate(username, password, **auth_kwargs)
        except Exception as e:
            logger.exception("TACACS+ Authentication Error: %s" % str(e))
            return None
        if auth.valid:
            return _get_or_set_enterprise_user(username, password, 'tacacs+')

    def get_user(self, user_id):
        if not django_settings.TACACSPLUS_HOST:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _get_client_ip(self, request):
        if not request or not hasattr(request, 'META'):
            return None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TowerSAMLIdentityProvider(BaseSAMLIdentityProvider):
    """
    Custom Identity Provider to make attributes to what we expect.
    """

    def get_user_permanent_id(self, attributes):
        uid = attributes[self.conf.get('attr_user_permanent_id', OID_USERID)]
        if isinstance(uid, str):
            return uid
        return uid[0]

    def get_attr(self, attributes, conf_key, default_attribute):
        """
        Get the attribute 'default_attribute' out of the attributes,
        unless self.conf[conf_key] overrides the default by specifying
        another attribute to use.
        """
        key = self.conf.get(conf_key, default_attribute)
        value = attributes[key] if key in attributes else None
        # In certain implementations (like https://pagure.io/ipsilon) this value is a string, not a list
        if isinstance(value, (list, tuple)):
            value = value[0]
        if conf_key in ('attr_first_name', 'attr_last_name', 'attr_username', 'attr_email') and value is None:
            logger.warning(
                "Could not map user detail '%s' from SAML attribute '%s'; update SOCIAL_AUTH_SAML_ENABLED_IDPS['%s']['%s'] with the correct SAML attribute.",
                conf_key[5:],
                key,
                self.name,
                conf_key,
            )
        return str(value) if value is not None else value


class SAMLAuth(BaseSAMLAuth):
    """
    Custom SAMLAuth backend to verify license status
    """

    def get_idp(self, idp_name):
        idp_config = self.setting('ENABLED_IDPS')[idp_name]
        return TowerSAMLIdentityProvider(idp_name, **idp_config)

    def authenticate(self, request, *args, **kwargs):
        if not all(
            [
                django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID,
                django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY,
                django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS,
            ]
        ):
            return None
        pipeline_result = super(SAMLAuth, self).authenticate(request, *args, **kwargs)

        if isinstance(pipeline_result, HttpResponse):
            return pipeline_result
        else:
            user = pipeline_result

        # Comes from https://github.com/omab/python-social-auth/blob/v0.2.21/social/backends/base.py#L91
        if getattr(user, 'is_new', False):
            enterprise_auth = _decorate_enterprise_user(user, 'saml')
            logger.debug("Created enterprise user %s from %s backend." % (user.username, enterprise_auth.get_provider_display()))
        elif user and not user.is_in_enterprise_category('saml'):
            return None
        if user:
            logger.debug("Enterprise user %s already created in Tower." % user.username)
        return user

    def get_user(self, user_id):
        if not all(
            [
                django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID,
                django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY,
                django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS,
            ]
        ):
            return None
        return super(SAMLAuth, self).get_user(user_id)
