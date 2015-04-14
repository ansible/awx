# -*- coding: utf-8 -*-

from __future__ import absolute_import

from six.moves import configparser as ConfigParser

import pyrax
from ..base_identity import BaseIdentity
from ..base_identity import User
from ..cloudnetworks import CloudNetworkClient
from .. import exceptions as exc
from .. import utils as utils

AUTH_ENDPOINT = "https://identity.api.rackspacecloud.com/v2.0/"


class RaxIdentity(BaseIdentity):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    _auth_endpoint = None
    _creds_style = "apikey"


    def _get_auth_endpoint(self):
        return (self._auth_endpoint or pyrax.get_setting("auth_endpoint")
                or AUTH_ENDPOINT)


    def _read_credential_file(self, cfg):
        """
        Parses the credential file with Rackspace-specific labels.
        """
        self.username = cfg.get("rackspace_cloud", "username")
        try:
            self.password = cfg.get("rackspace_cloud", "api_key", raw=True)
        except ConfigParser.NoOptionError as e:
            # Allow either the use of either 'api_key' or 'password'.
            self.password = cfg.get("rackspace_cloud", "password", raw=True)


    def _format_credentials(self):
        """
        Returns the current credentials in the format expected by the
        authentication service. Note that by default Rackspace credentials
        expect 'api_key' instead of 'password'. However, if authentication
        fails, return the creds in standard password format, in case they are
        using a username / password combination.
        """
        if self._creds_style == "apikey":
            return {"auth": {"RAX-KSKEY:apiKeyCredentials":
                    {"username": "%s" % self.username,
                    "apiKey": "%s" % self.api_key}}}
        else:
            # Return in the default password-style
            return super(RaxIdentity, self)._format_credentials()


    def set_credentials(self, username, password=None, region=None,
            tenant_id=None, authenticate=False):
        """
        Sets the username and password directly. Because Rackspace auth uses
        the api_key, make sure that any old values are cleared.
        """
        self.api_key = None
        super(RaxIdentity, self).set_credentials(username, password=password,
                region=region, tenant_id=tenant_id, authenticate=authenticate)


    def authenticate(self, username=None, password=None, api_key=None,
            tenant_id=None, connect=False):
        """
        If the user's credentials include an API key, the default behavior will
        work. But if they are using a password, the initial attempt will fail,
        so try again, but this time using the standard password format.

        The 'connect' parameter is retained for backwards compatibility. It no
        longer has any effect.
        """
        try:
            super(RaxIdentity, self).authenticate(username=username,
                    password=password, api_key=api_key, tenant_id=tenant_id)
        except exc.AuthenticationFailed:
            self._creds_style = "password"
            super(RaxIdentity, self).authenticate(username=username,
                    password=password, api_key=api_key, tenant_id=tenant_id)


    def auth_with_token(self, token, tenant_id=None, tenant_name=None):
        """
        If a valid token is already known, this call will use it to generate
        the service catalog.
        """
        # Implementation note:
        # Rackspace auth uses one tenant ID for the object_store services and
        # another for everything else. The one that the user would know is the
        # 'everything else' ID, so we need to extract the object_store tenant
        # ID from the initial response, and call the superclass
        # auth_with_token() method a second time with that tenant ID to get the
        # object_store endpoints. We can then add these to the initial
        # endpoints returned by the primary tenant ID, and then continue with
        # the auth process.
        main_resp, main_body = self._call_token_auth(token, tenant_id,
                tenant_name)
        # Get the swift tenant ID
        roles = main_body["access"]["user"]["roles"]
        ostore = [role for role in roles
                if role["name"] == "object-store:default"]
        if ostore:
            ostore_tenant_id = ostore[0]["tenantId"]
            ostore_resp, ostore_body = self._call_token_auth(token,
                    ostore_tenant_id, None)
            ostore_cat = ostore_body["access"]["serviceCatalog"]
            main_cat = main_body["access"]["serviceCatalog"]
            main_cat.extend(ostore_cat)
        self._parse_response(main_body)
        self.authenticated = True


    def _parse_response(self, resp):
        """Gets the authentication information from the returned JSON."""
        super(RaxIdentity, self)._parse_response(resp)
        user = resp["access"]["user"]
        defreg = user.get("RAX-AUTH:defaultRegion")
        if defreg:
            self._default_region = defreg


    def get_client(self, service, region, public=True, cached=True):
        """
        Returns the client object for the specified service and region.

        By default the public endpoint is used. If you wish to work with a
        services internal endpoints, specify `public=False`.

        By default, if a client has already been created for the given service,
        region, and public values, that will be returned. To force a new client
        to be created, pass 'cached=False'.
        """
        client_class = None
        # Cloud Networks currently uses nova-networks, so it doesn't appear as
        # a separate entry in the service catalog. This hack will allow context
        # objects to continue to work with Rackspace Cloud Networks. When the
        # Neutron service is implemented, this hack will have to be removed.
        if service in ("compute:networks", "networks", "network",
                "cloudnetworks", "cloud_networks"):
            service = "compute"
            client_class = CloudNetworkClient
        return super(RaxIdentity, self).get_client(service, region,
                public=public, cached=cached, client_class=client_class)


    def find_user_by_name(self, name):
        """
        Returns a User object by searching for the supplied user name. Returns
        None if there is no match for the given name.
        """
        return self.get_user(username=name)


    def find_user_by_email(self, email):
        """
        Returns a User object by searching for the supplied user's email
        address. Returns None if there is no match for the given ID.
        """
        return self.get_user(email=email)


    def find_user_by_id(self, uid):
        """
        Returns a User object by searching for the supplied user ID. Returns
        None if there is no match for the given ID.
        """
        return self.get_user(user_id=uid)


    def get_user(self, user_id=None, username=None, email=None):
        """
        Returns the user specified by either ID, username or email.

        Since more than user can have the same email address, searching by that
        term will return a list of 1 or more User objects. Searching by
        username or ID will return a single User.

        If a user_id that doesn't belong to the current account is searched
        for, a Forbidden exception is raised. When searching by username or
        email, a NotFound exception is raised if there is no matching user.
        """
        if user_id:
            uri = "/users/%s" % user_id
        elif username:
            uri = "/users?name=%s" % username
        elif email:
            uri = "/users?email=%s" % email
        else:
            raise ValueError("You must include one of 'user_id', "
                    "'username', or 'email' when calling get_user().")
        resp, resp_body = self.method_get(uri)
        if resp.status_code == 404:
            raise exc.NotFound("No such user exists.")
        users = resp_body.get("users", [])
        if users:
            return [User(self, user) for user in users]
        else:
            user = resp_body.get("user", {})
            if user:
                return User(self, user)
            else:
                raise exc.NotFound("No such user exists.")


    def update_user(self, user, email=None, username=None,
            uid=None, defaultRegion=None, enabled=None):
        """
        Allows you to update settings for a given user.
        """
        user_id = utils.get_id(user)
        uri = "users/%s" % user_id
        upd = {"id": user_id}
        if email is not None:
            upd["email"] = email
        if defaultRegion is not None:
            upd["RAX-AUTH:defaultRegion"] = defaultRegion
        if username is not None:
            upd["username"] = username
        if enabled is not None:
            upd["enabled"] = enabled
        data = {"user": upd}
        resp, resp_body = self.method_put(uri, data=data)
        if resp.status_code in (401, 403, 404):
            raise exc.AuthorizationFailure("You are not authorized to update "
                    "users.")
        return User(self, resp_body)


    def reset_api_key(self, user=None):
        """
        Resets the API key for the specified user, or if no user is specified,
        for the current user. Returns the newly-created API key.

        Resetting an API key does not invalidate any authenticated sessions,
        nor does it revoke any tokens.
        """
        if user is None:
            user_id = utils.get_id(self)
        else:
            user_id = utils.get_id(user)
        uri = "users/%s/OS-KSADM/credentials/" % user_id
        uri += "RAX-KSKEY:apiKeyCredentials/RAX-AUTH/reset"
        resp, resp_body = self.method_post(uri)
        return resp_body.get("RAX-KSKEY:apiKeyCredentials", {}).get("apiKey")
