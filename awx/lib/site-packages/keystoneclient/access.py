# Copyright 2012 Nebula, Inc.
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import datetime

from oslo_utils import timeutils

from keystoneclient.i18n import _
from keystoneclient import service_catalog


# gap, in seconds, to determine whether the given token is about to expire
STALE_TOKEN_DURATION = 30


class AccessInfo(dict):
    """Encapsulates a raw authentication token from keystone.

    Provides helper methods for extracting useful values from that token.

    """

    @classmethod
    def factory(cls, resp=None, body=None, region_name=None, auth_token=None,
                **kwargs):
        """Create AccessInfo object given a successful auth response & body
           or a user-provided dict.
        """
        # FIXME(jamielennox): Passing region_name is deprecated. Provide an
        # appropriate warning.
        auth_ref = None

        if body is not None or len(kwargs):
            if AccessInfoV3.is_valid(body, **kwargs):
                if resp and not auth_token:
                    auth_token = resp.headers['X-Subject-Token']
                # NOTE(jamielennox): these return AccessInfo because they
                # already have auth_token installed on them.
                if body:
                    if region_name:
                        body['token']['region_name'] = region_name
                    return AccessInfoV3(auth_token, **body['token'])
                else:
                    return AccessInfoV3(auth_token, **kwargs)
            elif AccessInfoV2.is_valid(body, **kwargs):
                if body:
                    if region_name:
                        body['access']['region_name'] = region_name
                    auth_ref = AccessInfoV2(**body['access'])
                else:
                    auth_ref = AccessInfoV2(**kwargs)
            else:
                raise NotImplementedError(_('Unrecognized auth response'))
        else:
            auth_ref = AccessInfoV2(**kwargs)

        if auth_token:
            auth_ref.auth_token = auth_token

        return auth_ref

    def __init__(self, *args, **kwargs):
        super(AccessInfo, self).__init__(*args, **kwargs)
        self.service_catalog = service_catalog.ServiceCatalog.factory(
            resource_dict=self, region_name=self._region_name)

    @property
    def _region_name(self):
        return self.get('region_name')

    def will_expire_soon(self, stale_duration=None):
        """Determines if expiration is about to occur.

        :returns: true if expiration is within the given duration
        :rtype: boolean

        """
        stale_duration = (STALE_TOKEN_DURATION if stale_duration is None
                          else stale_duration)
        norm_expires = timeutils.normalize_time(self.expires)
        # (gyee) should we move auth_token.will_expire_soon() to timeutils
        # instead of duplicating code here?
        soon = (timeutils.utcnow() + datetime.timedelta(
                seconds=stale_duration))
        return norm_expires < soon

    @classmethod
    def is_valid(cls, body, **kwargs):
        """Determines if processing v2 or v3 token given a successful
        auth body or a user-provided dict.

        :returns: true if auth body matches implementing class
        :rtype: boolean
        """
        raise NotImplementedError()

    def has_service_catalog(self):
        """Returns true if the authorization token has a service catalog.

        :returns: boolean
        """
        raise NotImplementedError()

    @property
    def auth_token(self):
        """Returns the token_id associated with the auth request, to be used
        in headers for authenticating OpenStack API requests.

        :returns: str
        """
        return self['auth_token']

    @auth_token.setter
    def auth_token(self, value):
        self['auth_token'] = value

    @auth_token.deleter
    def auth_token(self):
        try:
            del self['auth_token']
        except KeyError:
            pass

    @property
    def expires(self):
        """Returns the token expiration (as datetime object)

        :returns: datetime
        """
        raise NotImplementedError()

    @property
    def issued(self):
        """Returns the token issue time (as datetime object)

        :returns: datetime
        """
        raise NotImplementedError()

    @property
    def username(self):
        """Returns the username associated with the authentication request.
        Follows the pattern defined in the V2 API of first looking for 'name',
        returning that if available, and falling back to 'username' if name
        is unavailable.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_id(self):
        """Returns the user id associated with the authentication request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_domain_id(self):
        """Returns the domain id of the user associated with the authentication
        request.

        For v2, it always returns 'default' which may be different from the
        Keystone configuration.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_domain_name(self):
        """Returns the domain name of the user associated with the
        authentication request.

        For v2, it always returns 'Default' which may be different from the
        Keystone configuration.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def role_ids(self):
        """Returns a list of role ids of the user associated with the
        authentication request.

        :returns: a list of strings of role ids
        """
        raise NotImplementedError()

    @property
    def role_names(self):
        """Returns a list of role names of the user associated with the
        authentication request.

        :returns: a list of strings of role names
        """
        raise NotImplementedError()

    @property
    def domain_name(self):
        """Returns the domain name associated with the authentication token.

        :returns: str or None (if no domain associated with the token)
        """
        raise NotImplementedError()

    @property
    def domain_id(self):
        """Returns the domain id associated with the authentication token.

        :returns: str or None (if no domain associated with the token)
        """
        raise NotImplementedError()

    @property
    def project_name(self):
        """Returns the project name associated with the authentication request.

        :returns: str or None (if no project associated with the token)
        """
        raise NotImplementedError()

    @property
    def tenant_name(self):
        """Synonym for project_name."""
        return self.project_name

    @property
    def scoped(self):
        """Returns true if the authorization token was scoped to a tenant
           (project), and contains a populated service catalog.

           This is deprecated, use project_scoped instead.

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def project_scoped(self):
        """Returns true if the authorization token was scoped to a tenant
           (project).

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def domain_scoped(self):
        """Returns true if the authorization token was scoped to a domain.

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def trust_id(self):
        """Returns the trust id associated with the authentication token.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def trust_scoped(self):
        """Returns true if the authorization token was scoped as delegated in a
        trust, via the OS-TRUST v3 extension.

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def trustee_user_id(self):
        """Returns the trustee user id associated with a trust.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def trustor_user_id(self):
        """Returns the trustor user id associated with a trust.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def project_id(self):
        """Returns the project ID associated with the authentication
        request, or None if the authentication request wasn't scoped to a
        project.

        :returns: str or None (if no project associated with the token)
        """
        raise NotImplementedError()

    @property
    def tenant_id(self):
        """Synonym for project_id."""
        return self.project_id

    @property
    def project_domain_id(self):
        """Returns the domain id of the project associated with the
        authentication request.

        For v2, it returns 'default' if a project is scoped or None which may
        be different from the keystone configuration.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def project_domain_name(self):
        """Returns the domain name of the project associated with the
        authentication request.

        For v2, it returns 'Default' if a project is scoped or None  which may
        be different from the keystone configuration.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def auth_url(self):
        """Returns a tuple of URLs from publicURL and adminURL for the service
        'identity' from the service catalog associated with the authorization
        request. If the authentication request wasn't scoped to a tenant
        (project), this property will return None.

        DEPRECATED: this doesn't correctly handle region name. You should fetch
        it from the service catalog yourself.

        :returns: tuple of urls
        """
        raise NotImplementedError()

    @property
    def management_url(self):
        """Returns the first adminURL for 'identity' from the service catalog
        associated with the authorization request, or None if the
        authentication request wasn't scoped to a tenant (project).

        DEPRECATED: this doesn't correctly handle region name. You should fetch
        it from the service catalog yourself.

        :returns: tuple of urls
        """
        raise NotImplementedError()

    @property
    def version(self):
        """Returns the version of the auth token from identity service.

        :returns: str
        """
        return self.get('version')

    @property
    def oauth_access_token_id(self):
        """Return the access token ID if OAuth authentication used.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def oauth_consumer_id(self):
        """Return the consumer ID if OAuth authentication used.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def is_federated(self):
        """Returns true if federation was used to get the token.

        :returns: boolean
        """
        raise NotImplementedError()


class AccessInfoV2(AccessInfo):
    """An object for encapsulating a raw v2 auth token from identity
       service.
    """

    def __init__(self, *args, **kwargs):
        super(AccessInfo, self).__init__(*args, **kwargs)
        self.update(version='v2.0')
        self.service_catalog = service_catalog.ServiceCatalog.factory(
            resource_dict=self,
            token=self['token']['id'],
            region_name=self._region_name)

    @classmethod
    def is_valid(cls, body, **kwargs):
        if body:
            return 'access' in body
        elif kwargs:
            return kwargs.get('version') == 'v2.0'
        else:
            return False

    def has_service_catalog(self):
        return 'serviceCatalog' in self

    @AccessInfo.auth_token.getter
    def auth_token(self):
        try:
            return super(AccessInfoV2, self).auth_token
        except KeyError:
            return self['token']['id']

    @property
    def expires(self):
        return timeutils.parse_isotime(self['token']['expires'])

    @property
    def issued(self):
        return timeutils.parse_isotime(self['token']['issued_at'])

    @property
    def username(self):
        return self['user'].get('name', self['user'].get('username'))

    @property
    def user_id(self):
        return self['user']['id']

    @property
    def user_domain_id(self):
        return 'default'

    @property
    def user_domain_name(self):
        return 'Default'

    @property
    def role_ids(self):
        return self.get('metadata', {}).get('roles', [])

    @property
    def role_names(self):
        return [r['name'] for r in self['user'].get('roles', [])]

    @property
    def domain_name(self):
        return None

    @property
    def domain_id(self):
        return None

    @property
    def project_name(self):
        try:
            tenant_dict = self['token']['tenant']
        except KeyError:
            pass
        else:
            return tenant_dict.get('name')

        # pre grizzly
        try:
            return self['user']['tenantName']
        except KeyError:
            pass

        # pre diablo, keystone only provided a tenantId
        try:
            return self['token']['tenantId']
        except KeyError:
            pass

    @property
    def scoped(self):
        if ('serviceCatalog' in self
                and self['serviceCatalog']
                and 'tenant' in self['token']):
            return True
        return False

    @property
    def project_scoped(self):
        return 'tenant' in self['token']

    @property
    def domain_scoped(self):
        return False

    @property
    def trust_id(self):
        return self.get('trust', {}).get('id')

    @property
    def trust_scoped(self):
        return 'trust' in self

    @property
    def trustee_user_id(self):
        return self.get('trust', {}).get('trustee_user_id')

    @property
    def trustor_user_id(self):
        # this information is not available in the v2 token bug: #1331882
        return None

    @property
    def project_id(self):
        try:
            tenant_dict = self['token']['tenant']
        except KeyError:
            pass
        else:
            return tenant_dict.get('id')

        # pre grizzly
        try:
            return self['user']['tenantId']
        except KeyError:
            pass

        # pre diablo
        try:
            return self['token']['tenantId']
        except KeyError:
            pass

    @property
    def project_domain_id(self):
        if self.project_id:
            return 'default'

    @property
    def project_domain_name(self):
        if self.project_id:
            return 'Default'

    @property
    def auth_url(self):
        # FIXME(jamielennox): this is deprecated in favour of retrieving it
        # from the service catalog. Provide a warning.
        if self.service_catalog:
            return self.service_catalog.get_urls(service_type='identity',
                                                 endpoint_type='publicURL',
                                                 region_name=self._region_name)
        else:
            return None

    @property
    def management_url(self):
        # FIXME(jamielennox): this is deprecated in favour of retrieving it
        # from the service catalog. Provide a warning.
        if self.service_catalog:
            return self.service_catalog.get_urls(service_type='identity',
                                                 endpoint_type='adminURL',
                                                 region_name=self._region_name)
        else:
            return None

    @property
    def oauth_access_token_id(self):
        return None

    @property
    def oauth_consumer_id(self):
        return None

    @property
    def is_federated(self):
        return False


class AccessInfoV3(AccessInfo):
    """An object for encapsulating a raw v3 auth token from identity
       service.
    """

    def __init__(self, token, *args, **kwargs):
        super(AccessInfo, self).__init__(*args, **kwargs)
        self.update(version='v3')
        self.service_catalog = service_catalog.ServiceCatalog.factory(
            resource_dict=self,
            token=token,
            region_name=self._region_name)
        if token:
            self.auth_token = token

    @classmethod
    def is_valid(cls, body, **kwargs):
        if body:
            return 'token' in body
        elif kwargs:
            return kwargs.get('version') == 'v3'
        else:
            return False

    def has_service_catalog(self):
        return 'catalog' in self

    @property
    def is_federated(self):
        return 'OS-FEDERATION' in self['user']

    @property
    def expires(self):
        return timeutils.parse_isotime(self['expires_at'])

    @property
    def issued(self):
        return timeutils.parse_isotime(self['issued_at'])

    @property
    def user_id(self):
        return self['user']['id']

    @property
    def user_domain_id(self):
        try:
            return self['user']['domain']['id']
        except KeyError:
            if self.is_federated:
                return None
            raise

    @property
    def user_domain_name(self):
        try:
            return self['user']['domain']['name']
        except KeyError:
            if self.is_federated:
                return None
            raise

    @property
    def role_ids(self):
        return [r['id'] for r in self.get('roles', [])]

    @property
    def role_names(self):
        return [r['name'] for r in self.get('roles', [])]

    @property
    def username(self):
        return self['user']['name']

    @property
    def domain_name(self):
        domain = self.get('domain')
        if domain:
            return domain['name']

    @property
    def domain_id(self):
        domain = self.get('domain')
        if domain:
            return domain['id']

    @property
    def project_id(self):
        project = self.get('project')
        if project:
            return project['id']

    @property
    def project_domain_id(self):
        project = self.get('project')
        if project:
            return project['domain']['id']

    @property
    def project_domain_name(self):
        project = self.get('project')
        if project:
            return project['domain']['name']

    @property
    def project_name(self):
        project = self.get('project')
        if project:
            return project['name']

    @property
    def scoped(self):
        return ('catalog' in self and self['catalog'] and 'project' in self)

    @property
    def project_scoped(self):
        return 'project' in self

    @property
    def domain_scoped(self):
        return 'domain' in self

    @property
    def trust_id(self):
        return self.get('OS-TRUST:trust', {}).get('id')

    @property
    def trust_scoped(self):
        return 'OS-TRUST:trust' in self

    @property
    def trustee_user_id(self):
        return self.get('OS-TRUST:trust', {}).get('trustee_user', {}).get('id')

    @property
    def trustor_user_id(self):
        return self.get('OS-TRUST:trust', {}).get('trustor_user', {}).get('id')

    @property
    def auth_url(self):
        # FIXME(jamielennox): this is deprecated in favour of retrieving it
        # from the service catalog. Provide a warning.
        if self.service_catalog:
            return self.service_catalog.get_urls(service_type='identity',
                                                 endpoint_type='public',
                                                 region_name=self._region_name)
        else:
            return None

    @property
    def management_url(self):
        # FIXME(jamielennox): this is deprecated in favour of retrieving it
        # from the service catalog. Provide a warning.
        if self.service_catalog:
            return self.service_catalog.get_urls(service_type='identity',
                                                 endpoint_type='admin',
                                                 region_name=self._region_name)

        else:
            return None

    @property
    def oauth_access_token_id(self):
        return self.get('OS-OAUTH1', {}).get('access_token_id')

    @property
    def oauth_consumer_id(self):
        return self.get('OS-OAUTH1', {}).get('consumer_id')
