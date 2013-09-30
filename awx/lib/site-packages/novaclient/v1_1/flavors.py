# Copyright 2010 Jacob Kaplan-Moss
"""
Flavor interface.
"""
from novaclient import base
from novaclient import exceptions
from novaclient import utils
from novaclient.openstack.common.py3kcompat import urlutils


class Flavor(base.Resource):
    """
    A flavor is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Flavor: %s>" % self.name

    @property
    def ephemeral(self):
        """
        Provide a user-friendly accessor to OS-FLV-EXT-DATA:ephemeral
        """
        return self._info.get("OS-FLV-EXT-DATA:ephemeral", 'N/A')

    @property
    def is_public(self):
        """
        Provide a user-friendly accessor to os-flavor-access:is_public
        """
        return self._info.get("os-flavor-access:is_public", 'N/A')

    def get_keys(self):
        """
        Get extra specs from a flavor.

        :param flavor: The :class:`Flavor` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
                            "/flavors/%s/os-extra_specs" %
                            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """
        Set extra specs on a flavor.

        :param flavor: The :class:`Flavor` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
                            "/flavors/%s/os-extra_specs" % base.getid(self),
                            body,
                            "extra_specs",
                            return_raw=True)

    def unset_keys(self, keys):
        """
        Unset extra specs on a flavor.

        :param flavor: The :class:`Flavor` to unset extra spec on
        :param keys: A list of keys to be unset
        """
        for k in keys:
            return self.manager._delete(
                            "/flavors/%s/os-extra_specs/%s" % (
                            base.getid(self), k))

    def delete(self):
        """
        Delete this flavor.
        """
        self.manager.delete(self)


class FlavorManager(base.ManagerWithFind):
    """
    Manage :class:`Flavor` resources.
    """
    resource_class = Flavor
    is_alphanum_id_allowed = True

    def list(self, detailed=True, is_public=True):
        """
        Get a list of all flavors.

        :rtype: list of :class:`Flavor`.
        """
        qparams = {}
        # is_public is ternary - None means give all flavors.
        # By default Nova assumes True and gives admins public flavors
        # and flavors from their own projects only.
        if not is_public:
            qparams['is_public'] = is_public
        query_string = "?%s" % urlutils.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        return self._list("/flavors%s%s" % (detail, query_string), "flavors")

    def get(self, flavor):
        """
        Get a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :rtype: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor), "flavor")

    def delete(self, flavor):
        """
        Delete a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :param purge: Whether to purge record from the database
        """
        self._delete("/flavors/%s" % base.getid(flavor))

    def create(self, name, ram, vcpus, disk, flavorid="auto",
               ephemeral=0, swap=0, rxtx_factor=1.0, is_public=True):
        """
        Create (allocate) a  floating ip for a tenant

        :param name: Descriptive name of the flavor
        :param ram: Memory in MB for the flavor
        :param vcpu: Number of VCPUs for the flavor
        :param disk: Size of local disk in GB
        :param flavorid: ID for the flavor (optional). You can use the reserved
                         value ``"auto"`` to have Nova generate a UUID for the
                         flavor in cases where you cannot simply pass ``None``.
        :param swap: Swap space in MB
        :param rxtx_factor: RX/TX factor
        :rtype: :class:`Flavor`
        """

        try:
            ram = int(ram)
        except (TypeError, ValueError):
            raise exceptions.CommandError("Ram must be an integer.")
        try:
            vcpus = int(vcpus)
        except (TypeError, ValueError):
            raise exceptions.CommandError("VCPUs must be an integer.")
        try:
            disk = int(disk)
        except (TypeError, ValueError):
            raise exceptions.CommandError("Disk must be an integer.")

        if flavorid == "auto":
            flavorid = None

        try:
            swap = int(swap)
        except (TypeError, ValueError):
            raise exceptions.CommandError("Swap must be an integer.")
        try:
            ephemeral = int(ephemeral)
        except (TypeError, ValueError):
            raise exceptions.CommandError("Ephemeral must be an integer.")
        try:
            rxtx_factor = float(rxtx_factor)
        except (TypeError, ValueError):
            raise exceptions.CommandError("rxtx_factor must be a float.")

        try:
            is_public = utils.bool_from_str(is_public)
        except Exception:
            raise exceptions.CommandError("is_public must be a boolean.")

        body = {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "id": flavorid,
                "swap": swap,
                "OS-FLV-EXT-DATA:ephemeral": ephemeral,
                "rxtx_factor": rxtx_factor,
                "os-flavor-access:is_public": is_public,
            }
        }

        return self._create("/flavors", body, "flavor")
