#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six.moves import configparser

from pyrax.base_identity import BaseAuth
from pyrax.base_identity import User
import pyrax.exceptions as exc
import pyrax.utils as utils

AUTH_ENDPOINT = "https://identity.api.rackspacecloud.com/v2.0/"


class RaxIdentity(BaseAuth):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    _auth_endpoint = None
    _creds_style = "apikey"


    def _get_auth_endpoint(self):
        return self._auth_endpoint or AUTH_ENDPOINT


    def _read_credential_file(self, cfg):
        """
        Parses the credential file with Rackspace-specific labels.
        """
        self.username = cfg.get("rackspace_cloud", "username")
        try:
            self.password = cfg.get("rackspace_cloud", "api_key", raw=True)
        except configparser.NoOptionError as e:
            # Allow either the use of either 'api_key' or 'password'.
            self.password = cfg.get("rackspace_cloud", "password", raw=True)


    def _get_credentials(self):
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
                    "apiKey": "%s" % self.password}}}
        else:
            # Return in the default password-style
            return super(RaxIdentity, self)._get_credentials()


    def authenticate(self):
        """
        If the user's credentials include an API key, the default behavior will
        work. But if they are using a password, the initial attempt will fail,
        so try again, but this time using the standard password format.
        """
        try:
            super(RaxIdentity, self).authenticate()
        except exc.AuthenticationFailed:
            self._creds_style = "password"
            super(RaxIdentity, self).authenticate()


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
        main_resp = self._call_token_auth(token, tenant_id, tenant_name)
        main_body = main_resp.json()
        # Get the swift tenant ID
        roles = main_body["access"]["user"]["roles"]
        ostore = [role for role in roles
                if role["name"] == "object-store:default"]
        if ostore:
            ostore_tenant_id = ostore[0]["tenantId"]
            ostore_resp = self._call_token_auth(token, ostore_tenant_id, None)
            ostore_body = ostore_resp.json()
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


    def find_user_by_name(self, name):
        """
        Returns a User object by searching for the supplied user name. Returns
        None if there is no match for the given name.
        """
        uri = "users?name=%s" % name
        return self._find_user(uri)


    def find_user_by_id(self, uid):
        """
        Returns a User object by searching for the supplied user ID. Returns
        None if there is no match for the given ID.
        """
        uri = "users/%s" % uid
        return self._find_user(uri)


    def _find_user(self, uri):
        """Handles the 'find' code for both name and ID searches."""
        resp = self.method_get(uri)
        if resp.status_code in (403, 404):
            return None
        jusers = resp.json()
        user_info = jusers["user"]
        return User(self, user_info)


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
        resp = self.method_put(uri, data=data)
        return User(self, resp.json())


    def list_credentials(self, user):
        """
        Returns a user's non-password credentials.
        """
        user_id = utils.get_id(user)
        uri = "users/%s/OS-KSADM/credentials" % user_id
        return self.method_get(uri)


    def get_user_credentials(self, user):
        """
        Returns a user's non-password credentials.
        """
        user_id = utils.get_id(user)
        base_uri = "users/%s/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials"
        uri = base_uri % user_id
        return self.method_get(uri)
