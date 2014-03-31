# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
# Copyright 2012 Rackspace

# All Rights Reserved.
#
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

"""
Base utilities to build API operation managers and objects on top of.
"""

import six

import pyrax
import pyrax.utils as utils


class BaseResource(object):
    """
    A resource represents a particular instance of an object (server, flavor,
    etc). This is pretty much just a bag for attributes.
    """
    HUMAN_ID = False
    NAME_ATTR = "name"
    # Some resource do not have any additional details to lazy load,
    # so skip the unneeded API call by setting this to False.
    get_details = True
    # Atts not to display when showing the __repr__()
    _non_display = []
    # Properties to add to the __repr__() display
    _repr_properties = []


    def __init__(self, manager, info, key=None, loaded=False):
        self._loaded = loaded
        self.manager = manager
        if key:
            info = info[key]
        self._info = info
        self._add_details(info)


    @property
    def human_id(self):
        """Subclasses may override this to provide a pretty ID which can be used
        for bash completion.
        """
        if self.NAME_ATTR in self.__dict__ and self.HUMAN_ID:
            return utils.slugify(getattr(self, self.NAME_ATTR))
        return None


    def _add_details(self, info):
        """
        Takes the dict returned by the API call and sets the
        corresponding attributes on the object.
        """
        for (key, val) in info.iteritems():
            if isinstance(key, six.text_type):
                key = key.encode(pyrax.get_encoding())
            setattr(self, key, val)


    def __getattr__(self, key):
        """
        Many objects are lazy-loaded: only their most basic details
        are initially returned. The first time any of the other attributes
        are referenced, a GET is made to get the full details for the
        object.
        """
        if not self.loaded:
            self.get()
        # Attribute should be set; if not, it's not valid
        try:
            return self.__dict__[key]
        except KeyError:
            raise AttributeError("'%s' object has no attribute "
                    "'%s'." % (self.__class__, key))


    def __repr__(self):
        reprkeys = sorted(key for key in self.__dict__.keys()
                if (key[0] != "_")
                and (key not in ("manager", "created", "updated"))
                and (key not in self._non_display))
        reprkeys += self._repr_properties
        info = ", ".join("%s=%s" % (key, getattr(self, key))
                for key in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)


    def get(self):
        """Gets the details for the object."""
        # set 'loaded' first ... so if we have to bail, we know we tried.
        self.loaded = True
        if not hasattr(self.manager, "get"):
            return
        if not self.get_details:
            return
        new = self.manager.get(self)
        if new:
            self._add_details(new._info)
    # This alias is used to make its purpose clearer.
    reload = get


    def delete(self):
        """Deletes the object."""
        # set 'loaded' first ... so if we have to bail, we know we tried.
        self.loaded = True
        if not hasattr(self.manager, "delete"):
            return
        self.manager.delete(self)


    def __eq__(self, other):
        """
        Two resource objects that represent the same entity in the cloud
        should be considered equal if they have the same ID. If they
        don't have IDs, but their attribute info matches, they are equal.
        """
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, "id") and hasattr(other, "id"):
            return self.id == other.id
        return self._info == other._info


    def _get_loaded(self):
        return self._loaded

    def _set_loaded(self, val):
        self._loaded = val

    loaded = property(_get_loaded, _set_loaded)
