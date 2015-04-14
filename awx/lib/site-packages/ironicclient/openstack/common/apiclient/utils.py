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

from oslo.utils import encodeutils
import six

from ironicclient.openstack.common._i18n import _
from ironicclient.openstack.common.apiclient import exceptions
from ironicclient.openstack.common import uuidutils


def find_resource(manager, name_or_id, **find_args):
    """Look for resource in a given manager.

    Used as a helper for the _find_* methods.
    Example:

    .. code-block:: python

        def _find_hypervisor(cs, hypervisor):
            #Get a hypervisor by name or ID.
            return cliutils.find_resource(cs.hypervisors, hypervisor)
    """
    # first try to get entity as integer id
    try:
        return manager.get(int(name_or_id))
    except (TypeError, ValueError, exceptions.NotFound):
        pass

    # now try to get entity as uuid
    try:
        if six.PY2:
            tmp_id = encodeutils.safe_encode(name_or_id)
        else:
            tmp_id = encodeutils.safe_decode(name_or_id)

        if uuidutils.is_uuid_like(tmp_id):
            return manager.get(tmp_id)
    except (TypeError, ValueError, exceptions.NotFound):
        pass

    # for str id which is not uuid
    if getattr(manager, 'is_alphanum_id_allowed', False):
        try:
            return manager.get(name_or_id)
        except exceptions.NotFound:
            pass

    try:
        try:
            return manager.find(human_id=name_or_id, **find_args)
        except exceptions.NotFound:
            pass

        # finally try to find entity by name
        try:
            resource = getattr(manager, 'resource_class', None)
            name_attr = resource.NAME_ATTR if resource else 'name'
            kwargs = {name_attr: name_or_id}
            kwargs.update(find_args)
            return manager.find(**kwargs)
        except exceptions.NotFound:
            msg = _("No %(name)s with a name or "
                    "ID of '%(name_or_id)s' exists.") % \
                {
                    "name": manager.resource_class.__name__.lower(),
                    "name_or_id": name_or_id
                }
            raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = _("Multiple %(name)s matches found for "
                "'%(name_or_id)s', use an ID to be more specific.") % \
            {
                "name": manager.resource_class.__name__.lower(),
                "name_or_id": name_or_id
            }
        raise exceptions.CommandError(msg)
