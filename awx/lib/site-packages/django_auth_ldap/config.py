# Copyright (c) 2009, Peter Sagerson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
This module contains classes that will be needed for configuration of LDAP
authentication. Unlike backend.py, this is safe to import into settings.py.
Please see the docstring on the backend module for more information, including
notes on naming conventions.
"""

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

import logging
import pprint


class _LDAPConfig(object):
    """
    A private class that loads and caches some global objects.
    """
    ldap = None
    logger = None

    _ldap_configured = False

    def get_ldap(cls, global_options=None):
        """
        Returns the ldap module. The unit test harness will assign a mock object
        to _LDAPConfig.ldap. It is imperative that the ldap module not be
        imported anywhere else so that the unit tests will pass in the absence
        of python-ldap.
        """
        if cls.ldap is None:
            import ldap
            import ldap.filter

            # Support for python-ldap < 2.0.6
            try:
                import ldap.dn
            except ImportError:
                from django_auth_ldap import dn
                ldap.dn = dn

            cls.ldap = ldap

        # Apply global LDAP options once
        if (not cls._ldap_configured) and (global_options is not None):
            for opt, value in global_options.iteritems():
                cls.ldap.set_option(opt, value)

            cls._ldap_configured = True

        return cls.ldap
    get_ldap = classmethod(get_ldap)

    def get_logger(cls):
        """
        Initializes and returns our logger instance.
        """
        if cls.logger is None:
            class NullHandler(logging.Handler):
                def emit(self, record):
                    pass

            cls.logger = logging.getLogger('django_auth_ldap')
            cls.logger.addHandler(NullHandler())

        return cls.logger
    get_logger = classmethod(get_logger)


# Our global logger
logger = _LDAPConfig.get_logger()


class LDAPSearch(object):
    """
    Public class that holds a set of LDAP search parameters. Objects of this
    class should be considered immutable. Only the initialization method is
    documented for configuration purposes. Internal clients may use the other
    methods to refine and execute the search.
    """
    def __init__(self, base_dn, scope, filterstr=u'(objectClass=*)'):
        """
        These parameters are the same as the first three parameters to
        ldap.search_s.
        """
        self.base_dn = base_dn
        self.scope = scope
        self.filterstr = filterstr
        self.ldap = _LDAPConfig.get_ldap()

    def search_with_additional_terms(self, term_dict, escape=True):
        """
        Returns a new search object with additional search terms and-ed to the
        filter string. term_dict maps attribute names to assertion values. If
        you don't want the values escaped, pass escape=False.
        """
        term_strings = [self.filterstr]

        for name, value in term_dict.iteritems():
            if escape:
                value = self.ldap.filter.escape_filter_chars(value)
            term_strings.append(u'(%s=%s)' % (name, value))

        filterstr = u'(&%s)' % ''.join(term_strings)

        return self.__class__(self.base_dn, self.scope, filterstr)

    def search_with_additional_term_string(self, filterstr):
        """
        Returns a new search object with filterstr and-ed to the original filter
        string. The caller is responsible for passing in a properly escaped
        string.
        """
        filterstr = u'(&%s%s)' % (self.filterstr, filterstr)

        return self.__class__(self.base_dn, self.scope, filterstr)

    def execute(self, connection, filterargs=()):
        """
        Executes the search on the given connection (an LDAPObject). filterargs
        is an object that will be used for expansion of the filter string.

        The python-ldap library returns utf8-encoded strings. For the sake of
        sanity, this method will decode all result strings and return them as
        Unicode.
        """
        try:
            filterstr = self.filterstr % filterargs
            results = connection.search_s(self.base_dn.encode('utf-8'),
                self.scope, filterstr.encode('utf-8'))
        except self.ldap.LDAPError, e:
            results = []
            logger.error(u"search_s('%s', %d, '%s') raised %s" %
                (self.base_dn, self.scope, filterstr, pprint.pformat(e)))

        return self._process_results(results)

    def _begin(self, connection, filterargs=()):
        """
        Begins an asynchronous search and returns the message id to retrieve
        the results.
        """
        try:
            filterstr = self.filterstr % filterargs
            msgid = connection.search(self.base_dn.encode('utf-8'),
                self.scope, filterstr.encode('utf-8'))
        except self.ldap.LDAPError, e:
            msgid = None
            logger.error(u"search('%s', %d, '%s') raised %s" %
                (self.base_dn, self.scope, filterstr, pprint.pformat(e)))

        return msgid

    def _results(self, connection, msgid):
        """
        Returns the result of a previous asynchronous query.
        """
        try:
            kind, results = connection.result(msgid)
            if kind != self.ldap.RES_SEARCH_RESULT:
                results = []
        except self.ldap.LDAPError, e:
            results = []
            logger.error(u"result(%d) raised %s" % (msgid, pprint.pformat(e)))

        return self._process_results(results)

    def _process_results(self, results):
        """
        Returns a sanitized copy of raw LDAP results. This scrubs out
        references, decodes utf8, normalizes DNs, etc.
        """
        results = filter(lambda r: r[0] is not None, results)
        results = _DeepStringCoder('utf-8').decode(results)

        # The normal form of a DN is lower case.
        results = map(lambda r: (r[0].lower(), r[1]), results)

        result_dns = [result[0] for result in results]
        logger.debug(u"search_s('%s', %d, '%s') returned %d objects: %s" %
            (self.base_dn, self.scope, self.filterstr, len(result_dns), "; ".join(result_dns)))

        return results


class LDAPSearchUnion(object):
    """
    A compound search object that returns the union of the results. Instantiate
    it with one or more LDAPSearch objects.
    """
    def __init__(self, *args):
        self.searches = args
        self.ldap = _LDAPConfig.get_ldap()

    def execute(self, connection, filterargs=()):
        msgids = [search._begin(connection, filterargs) for search in self.searches]
        results = {}

        for search, msgid in zip(self.searches, msgids):
            result = search._results(connection, msgid)
            results.update(dict(result))

        return results.items()


class _DeepStringCoder(object):
    """
    Encodes and decodes strings in a nested structure of lists, tuples, and
    dicts. This is helpful when interacting with the Unicode-unaware
    python-ldap.
    """
    def __init__(self, encoding):
        self.encoding = encoding
        self.ldap = _LDAPConfig.get_ldap()

    def decode(self, value):
        try:
            if isinstance(value, str):
                value = value.decode(self.encoding)
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, tuple):
                value = tuple(self._decode_list(value))
            elif isinstance(value, dict):
                value = self._decode_dict(value)
        except UnicodeDecodeError:
            pass

        return value

    def _decode_list(self, value):
        return [self.decode(v) for v in value]

    def _decode_dict(self, value):
        # Attribute dictionaries should be case-insensitive. python-ldap
        # defines this, although for some reason, it doesn't appear to use it
        # for search results.
        decoded = self.ldap.cidict.cidict()

        for k, v in value.iteritems():
            decoded[self.decode(k)] = self.decode(v)

        return decoded


class LDAPGroupType(object):
    """
    This is an abstract base class for classes that determine LDAP group
    membership. A group can mean many different things in LDAP, so we will need
    a concrete subclass for each grouping mechanism. Clients may subclass this
    if they have a group mechanism that is not handled by a built-in
    implementation.

    name_attr is the name of the LDAP attribute from which we will take the
    Django group name.

    Subclasses in this file must use self.ldap to access the python-ldap module.
    This will be a mock object during unit tests.
    """
    def __init__(self, name_attr="cn"):
        self.name_attr = name_attr
        self.ldap = _LDAPConfig.get_ldap()

    def user_groups(self, ldap_user, group_search):
        """
        Returns a list of group_info structures, each one a group to which
        ldap_user belongs. group_search is an LDAPSearch object that returns all
        of the groups that the user might belong to. Typical implementations
        will apply additional filters to group_search and return the results of
        the search. ldap_user represents the user and has the following three
        properties:

        dn: the distinguished name
        attrs: a dictionary of LDAP attributes (with lists of values)
        connection: an LDAPObject that has been bound with credentials

        This is the primitive method in the API and must be implemented.
        """
        return []

    def is_member(self, ldap_user, group_dn):
        """
        This method is an optimization for determining group membership without
        loading all of the user's groups. Subclasses that are able to do this
        may return True or False. ldap_user is as above. group_dn is the
        distinguished name of the group in question.

        The base implementation returns None, which means we don't have enough
        information. The caller will have to call user_groups() instead and look
        for group_dn in the results.
        """
        return None

    def group_name_from_info(self, group_info):
        """
        Given the (DN, attrs) 2-tuple of an LDAP group, this returns the name of
        the Django group. This may return None to indicate that a particular
        LDAP group has no corresponding Django group.

        The base implementation returns the value of the cn attribute, or
        whichever attribute was given to __init__ in the name_attr
        parameter.
        """
        try:
            name = group_info[1][self.name_attr][0]
        except (KeyError, IndexError):
            name = None

        return name


class PosixGroupType(LDAPGroupType):
    """
    An LDAPGroupType subclass that handles groups of class posixGroup.
    """
    def user_groups(self, ldap_user, group_search):
        """
        Searches for any group that is either the user's primary or contains the
        user as a member.
        """
        groups = []

        try:
            user_uid = ldap_user.attrs['uid'][0]
            user_gid = ldap_user.attrs['gidNumber'][0]

            filterstr = u'(|(gidNumber=%s)(memberUid=%s))' % (
                self.ldap.filter.escape_filter_chars(user_gid),
                self.ldap.filter.escape_filter_chars(user_uid)
            )

            search = group_search.search_with_additional_term_string(filterstr)
            groups = search.execute(ldap_user.connection)
        except (KeyError, IndexError):
            pass

        return groups

    def is_member(self, ldap_user, group_dn):
        """
        Returns True if the group is the user's primary group or if the user is
        listed in the group's memberUid attribute.
        """
        try:
            user_uid = ldap_user.attrs['uid'][0]
            user_gid = ldap_user.attrs['gidNumber'][0]

            try:
                is_member = ldap_user.connection.compare_s(group_dn.encode('utf-8'), 'memberUid', user_uid.encode('utf-8'))
            except self.ldap.NO_SUCH_ATTRIBUTE:
                is_member = False

            if not is_member:
                try:
                    is_member = ldap_user.connection.compare_s(group_dn.encode('utf-8'), 'gidNumber', user_gid.encode('utf-8'))
                except self.ldap.NO_SUCH_ATTRIBUTE:
                    is_member = False
        except (KeyError, IndexError):
            is_member = False

        return is_member


class MemberDNGroupType(LDAPGroupType):
    """
    A group type that stores lists of members as distinguished names.
    """
    def __init__(self, member_attr, name_attr='cn'):
        """
        member_attr is the attribute on the group object that holds the list of
        member DNs.
        """
        self.member_attr = member_attr

        super(MemberDNGroupType, self).__init__(name_attr)

    def user_groups(self, ldap_user, group_search):
        search = group_search.search_with_additional_terms({self.member_attr: ldap_user.dn})
        groups = search.execute(ldap_user.connection)

        return groups

    def is_member(self, ldap_user, group_dn):
        try:
            result = ldap_user.connection.compare_s(
                group_dn.encode('utf-8'),
                self.member_attr.encode('utf-8'),
                ldap_user.dn.encode('utf-8')
            )
        except self.ldap.NO_SUCH_ATTRIBUTE:
            result = 0

        return result


class NestedMemberDNGroupType(LDAPGroupType):
    """
    A group type that stores lists of members as distinguished names and
    supports nested groups. There is no shortcut for is_member in this case, so
    it's left unimplemented.
    """
    def __init__(self, member_attr, name_attr='cn'):
        """
        member_attr is the attribute on the group object that holds the list of
        member DNs.
        """
        self.member_attr = member_attr

        super(NestedMemberDNGroupType, self).__init__(name_attr)

    def user_groups(self, ldap_user, group_search):
        """
        This searches for all of a user's groups from the bottom up. In other
        words, it returns the groups that the user belongs to, the groups that
        those groups belong to, etc. Circular references will be detected and
        pruned.
        """
        group_info_map = {} # Maps group_dn to group_info of groups we've found
        member_dn_set = set([ldap_user.dn]) # Member DNs to search with next
        handled_dn_set = set() # Member DNs that we've already searched with

        while len(member_dn_set) > 0:
            group_infos = self.find_groups_with_any_member(member_dn_set,
                group_search, ldap_user.connection)
            new_group_info_map = dict([(info[0], info) for info in group_infos])
            group_info_map.update(new_group_info_map)
            handled_dn_set.update(member_dn_set)

            # Get ready for the next iteration. To avoid cycles, we make sure
            # never to search with the same member DN twice.
            member_dn_set = set(new_group_info_map.keys()) - handled_dn_set

        return group_info_map.values()

    def find_groups_with_any_member(self, member_dn_set, group_search, connection):
        terms = [
            u"(%s=%s)" % (self.member_attr, self.ldap.filter.escape_filter_chars(dn))
            for dn in member_dn_set
        ]

        filterstr = u"(|%s)" % "".join(terms)
        search = group_search.search_with_additional_term_string(filterstr)

        return search.execute(connection)


class GroupOfNamesType(MemberDNGroupType):
    """
    An LDAPGroupType subclass that handles groups of class groupOfNames.
    """
    def __init__(self, name_attr='cn'):
        super(GroupOfNamesType, self).__init__('member', name_attr)


class NestedGroupOfNamesType(NestedMemberDNGroupType):
    """
    An LDAPGroupType subclass that handles groups of class groupOfNames with
    nested group references.
    """
    def __init__(self, name_attr='cn'):
        super(NestedGroupOfNamesType, self).__init__('member', name_attr)


class GroupOfUniqueNamesType(MemberDNGroupType):
    """
    An LDAPGroupType subclass that handles groups of class groupOfUniqueNames.
    """
    def __init__(self, name_attr='cn'):
        super(GroupOfUniqueNamesType, self).__init__('uniqueMember', name_attr)


class NestedGroupOfUniqueNamesType(NestedMemberDNGroupType):
    """
    An LDAPGroupType subclass that handles groups of class groupOfUniqueNames
    with nested group references.
    """
    def __init__(self, name_attr='cn'):
        super(NestedGroupOfUniqueNamesType, self).__init__('uniqueMember', name_attr)


class ActiveDirectoryGroupType(MemberDNGroupType):
    """
    An LDAPGroupType subclass that handles Active Directory groups.
    """
    def __init__(self, name_attr='cn'):
        super(ActiveDirectoryGroupType, self).__init__('member', name_attr)


class NestedActiveDirectoryGroupType(NestedMemberDNGroupType):
    """
    An LDAPGroupType subclass that handles Active Directory groups with nested
    group references.
    """
    def __init__(self, name_attr='cn'):
        super(NestedActiveDirectoryGroupType, self).__init__('member', name_attr)
