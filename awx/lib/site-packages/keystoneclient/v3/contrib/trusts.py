#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import timeutils

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _


class Trust(base.Resource):
    """Represents a Trust.

    Attributes:
        * id: a uuid that identifies the trust
        * impersonation: allow explicit impersonation
        * project_id: project ID
        * trustee_user_id: a uuid that identifies the trustee
        * trustor_user_id: a uuid that identifies the trustor
    """
    pass


class TrustManager(base.CrudManager):
    """Manager class for manipulating Trusts."""
    resource_class = Trust
    collection_key = 'trusts'
    key = 'trust'
    base_url = '/OS-TRUST'

    def create(self, trustee_user, trustor_user, role_names=None,
               project=None, impersonation=False, expires_at=None,
               remaining_uses=None, **kwargs):
        """Create a Trust.

        :param string trustee_user: user who is capable of consuming the trust
        :param string trustor_user: user who's authorization is being delegated
        :param string role_names: subset of trustor's roles to be granted
        :param string project: project which the trustor is delegating
        :param boolean impersonation: enable explicit impersonation
        :param datetime.datetime expires_at: expiry time
        :param integer remaining_uses: how many times this trust can be used
                                       to generate a token. None means
                                       unlimited tokens.

        """
        # Convert role_names list into list-of-dict API format
        if role_names:
            roles = [{'name': n} for n in role_names]
        else:
            roles = None

        # Convert datetime.datetime expires_at to iso format string
        if expires_at:
            expires_str = timeutils.isotime(at=expires_at, subsecond=True)
        else:
            expires_str = None

        return super(TrustManager, self).create(
            expires_at=expires_str,
            impersonation=impersonation,
            project_id=base.getid(project),
            remaining_uses=remaining_uses,
            roles=roles,
            trustee_user_id=base.getid(trustee_user),
            trustor_user_id=base.getid(trustor_user),
            **kwargs)

    def update(self):
        raise exceptions.MethodNotImplemented(
            _('Update not supported for trusts'))

    def list(self, trustee_user=None, trustor_user=None, **kwargs):
        """List Trusts."""
        trustee_user_id = base.getid(trustee_user)
        trustor_user_id = base.getid(trustor_user)
        return super(TrustManager, self).list(trustee_user_id=trustee_user_id,
                                              trustor_user_id=trustor_user_id,
                                              **kwargs)

    def get(self, trust):
        """Get a specific trust."""
        return super(TrustManager, self).get(trust_id=base.getid(trust))

    def delete(self, trust):
        """Delete a trust."""
        return super(TrustManager, self).delete(trust_id=base.getid(trust))
