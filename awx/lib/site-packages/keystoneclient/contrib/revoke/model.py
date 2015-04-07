# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_utils import timeutils

# The set of attributes common between the RevokeEvent
# and the dictionaries created from the token Data.
_NAMES = ['trust_id',
          'consumer_id',
          'access_token_id',
          'expires_at',
          'domain_id',
          'project_id',
          'user_id',
          'role_id']


# Additional arguments for creating a RevokeEvent
_EVENT_ARGS = ['issued_before', 'revoked_at']

# Values that will be in the token data but not in the event.
# These will compared with event values that have different names.
# For example: both trustor_id and trustee_id are compared against user_id
_TOKEN_KEYS = ['identity_domain_id',
               'assignment_domain_id',
               'issued_at',
               'trustor_id',
               'trustee_id']


REVOKE_KEYS = _NAMES + _EVENT_ARGS


def blank_token_data(issued_at):
    token_data = dict()
    for name in _NAMES:
        token_data[name] = None
    for name in _TOKEN_KEYS:
        token_data[name] = None
    # required field
    token_data['issued_at'] = issued_at
    return token_data


class RevokeEvent(object):
    def __init__(self, **kwargs):
        for k in REVOKE_KEYS:
            v = kwargs.get(k, None)
            setattr(self, k, v)
        if self.revoked_at is None:
            self.revoked_at = timeutils.utcnow()
        if self.issued_before is None:
            self.issued_before = self.revoked_at

    def to_dict(self):
        keys = ['user_id',
                'role_id',
                'domain_id',
                'project_id']
        event = dict((key, self.__dict__[key]) for key in keys
                     if self.__dict__[key] is not None)
        if self.trust_id is not None:
            event['OS-TRUST:trust_id'] = self.trust_id
        if self.consumer_id is not None:
            event['OS-OAUTH1:consumer_id'] = self.consumer_id
        if self.consumer_id is not None:
            event['OS-OAUTH1:access_token_id'] = self.access_token_id
        if self.expires_at is not None:
            event['expires_at'] = timeutils.isotime(self.expires_at,
                                                    subsecond=True)
        if self.issued_before is not None:
            event['issued_before'] = timeutils.isotime(self.issued_before,
                                                       subsecond=True)
        return event

    def key_for_name(self, name):
        return "%s=%s" % (name, getattr(self, name) or '*')


def attr_keys(event):
    return map(event.key_for_name, _NAMES)


class RevokeTree(object):
    """Fast Revocation Checking Tree Structure

    The Tree is an index to quickly match tokens against events.
    Each node is a hashtable of key=value combinations from revocation events.
    The

    """

    def __init__(self, revoke_events=None):
        self.revoke_map = dict()
        self.add_events(revoke_events)

    def add_event(self, event):
        """Updates the tree based on a revocation event.

        Creates any necessary internal nodes in the tree corresponding to the
        fields of the revocation event.  The leaf node will always be set to
        the latest 'issued_before' for events that are otherwise identical.

        :param: Event to add to the tree

        :returns: the event that was passed in.

        """
        revoke_map = self.revoke_map
        for key in attr_keys(event):
            revoke_map = revoke_map.setdefault(key, {})
        revoke_map['issued_before'] = max(
            event.issued_before, revoke_map.get(
                'issued_before', event.issued_before))
        return event

    def remove_event(self, event):
        """Update the tree based on the removal of a Revocation Event

        Removes empty nodes from the tree from the leaf back to the root.

        If multiple events trace the same path, but have different
        'issued_before' values, only the last is ever stored in the tree.
        So only an exact match on 'issued_before' ever triggers a removal

        :param: Event to remove from the tree

        """
        stack = []
        revoke_map = self.revoke_map
        for name in _NAMES:
            key = event.key_for_name(name)
            nxt = revoke_map.get(key)
            if nxt is None:
                break
            stack.append((revoke_map, key, nxt))
            revoke_map = nxt
        else:
            if event.issued_before == revoke_map['issued_before']:
                revoke_map.pop('issued_before')
        for parent, key, child in reversed(stack):
            if not any(child):
                del parent[key]

    def add_events(self, revoke_events):
        return map(self.add_event, revoke_events or [])

    def is_revoked(self, token_data):
        """Check if a token matches the revocation event

        Compare the values for each level of the tree with the values from
        the token, accounting for attributes that have alternative
        keys, and for wildcard matches.
        if there is a match, continue down the tree.
        if there is no match, exit early.

        token_data is a map based on a flattened view of token.
        The required fields are:

           'expires_at','user_id', 'project_id', 'identity_domain_id',
           'assignment_domain_id', 'trust_id', 'trustor_id', 'trustee_id'
           'consumer_id', 'access_token_id'

        """
        # Alternative names to be checked in token for every field in
        # revoke tree.
        alternatives = {
            'user_id': ['user_id', 'trustor_id', 'trustee_id'],
            'domain_id': ['identity_domain_id', 'assignment_domain_id'],
        }
        # Contains current forest (collection of trees) to be checked.
        partial_matches = [self.revoke_map]
        # We iterate over every layer of our revoke tree (except the last one).
        for name in _NAMES:
            # bundle is the set of partial matches for the next level down
            # the tree
            bundle = []
            wildcard = '%s=*' % (name,)
            # For every tree in current forest.
            for tree in partial_matches:
                # If there is wildcard node on current level we take it.
                bundle.append(tree.get(wildcard))
                if name == 'role_id':
                    # Roles are very special since a token has a list of them.
                    # If the revocation event matches any one of them,
                    # revoke the token.
                    for role_id in token_data.get('roles', []):
                        bundle.append(tree.get('role_id=%s' % role_id))
                else:
                    # For other fields we try to get any branch that concur
                    # with any alternative field in the token.
                    for alt_name in alternatives.get(name, [name]):
                        bundle.append(
                            tree.get('%s=%s' % (name, token_data[alt_name])))
            # tree.get returns `None` if there is no match, so `bundle.append`
            # adds a 'None' entry. This call remoes the `None` entries.
            partial_matches = [x for x in bundle if x is not None]
            if not partial_matches:
                # If we end up with no branches to follow means that the token
                # is definitely not in the revoke tree and all further
                # iterations will be for nothing.
                return False

        # The last (leaf) level is checked in a special way because we verify
        # issued_at field differently.
        for leaf in partial_matches:
            try:
                if leaf['issued_before'] > token_data['issued_at']:
                    return True
            except KeyError:
                pass
        # If we made it out of the loop then no element in revocation tree
        # corresponds to our token and it is good.
        return False


def build_token_values_v2(access, default_domain_id):
    token_data = access['token']
    token_values = {
        'expires_at': timeutils.normalize_time(
            timeutils.parse_isotime(token_data['expires'])),
        'issued_at': timeutils.normalize_time(
            timeutils.parse_isotime(token_data['issued_at']))}

    token_values['user_id'] = access.get('user', {}).get('id')

    project = token_data.get('tenant')
    if project is not None:
        token_values['project_id'] = project['id']
    else:
        token_values['project_id'] = None

    token_values['identity_domain_id'] = default_domain_id
    token_values['assignment_domain_id'] = default_domain_id

    trust = token_data.get('trust')
    if trust is None:
        token_values['trust_id'] = None
        token_values['trustor_id'] = None
        token_values['trustee_id'] = None
    else:
        token_values['trust_id'] = trust['id']
        token_values['trustor_id'] = trust['trustor_id']
        token_values['trustee_id'] = trust['trustee_id']

    token_values['consumer_id'] = None
    token_values['access_token_id'] = None

    role_list = []
    # Roles are by ID in metadata and by name in the user section
    roles = access.get('metadata', {}).get('roles', [])
    for role in roles:
        role_list.append(role)
    token_values['roles'] = role_list
    return token_values


def build_token_values(token_data):
    token_values = {
        'expires_at': timeutils.normalize_time(
            timeutils.parse_isotime(token_data['expires_at'])),
        'issued_at': timeutils.normalize_time(
            timeutils.parse_isotime(token_data['issued_at']))}

    user = token_data.get('user')
    if user is not None:
        token_values['user_id'] = user['id']
        token_values['identity_domain_id'] = user['domain']['id']
    else:
        token_values['user_id'] = None
        token_values['identity_domain_id'] = None

    project = token_data.get('project', token_data.get('tenant'))
    if project is not None:
        token_values['project_id'] = project['id']
        token_values['assignment_domain_id'] = project['domain']['id']
    else:
        token_values['project_id'] = None
        token_values['assignment_domain_id'] = None

    role_list = []
    roles = token_data.get('roles')
    if roles is not None:
        for role in roles:
            role_list.append(role['id'])
    token_values['roles'] = role_list

    trust = token_data.get('OS-TRUST:trust')
    if trust is None:
        token_values['trust_id'] = None
        token_values['trustor_id'] = None
        token_values['trustee_id'] = None
    else:
        token_values['trust_id'] = trust['id']
        token_values['trustor_id'] = trust['trustor_user']['id']
        token_values['trustee_id'] = trust['trustee_user']['id']

    oauth1 = token_data.get('OS-OAUTH1')
    if oauth1 is None:
        token_values['consumer_id'] = None
        token_values['access_token_id'] = None
    else:
        token_values['consumer_id'] = oauth1['consumer_id']
        token_values['access_token_id'] = oauth1['access_token_id']
    return token_values
