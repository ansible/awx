# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
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
Server interface.
"""

import base64

import six
from six.moves.urllib import parse

from novaclient import base
from novaclient import crypto
from novaclient.openstack.common.gettextutils import _
from novaclient.openstack.common import strutils

REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Server(base.Resource):
    HUMAN_ID = True

    def __repr__(self):
        return "<Server: %s>" % self.name

    def delete(self):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self.manager.delete(self)

    def update(self, name=None):
        """
        Update the name or the password for this server.

        :param name: Update the server's name.
        :param password: Update the root password.
        """
        self.manager.update(self, name=name)

    def get_console_output(self, length=None):
        """
        Get text console log output from Server.

        :param length: The number of lines you would like to retrieve (as int)
        """
        return self.manager.get_console_output(self, length)

    def get_vnc_console(self, console_type):
        """
        Get vnc console for a Server.

        :param console_type: Type of console ('novnc' or 'xvpvnc')
        """
        return self.manager.get_vnc_console(self, console_type)

    def get_spice_console(self, console_type):
        """
        Get spice console for a Server.

        :param console_type: Type of console ('spice-html5')
        """
        return self.manager.get_spice_console(self, console_type)

    def get_password(self, private_key):
        """
        Get password for a Server.

        :param private_key: Path to private key file for decryption
        """
        return self.manager.get_password(self, private_key)

    def clear_password(self):
        """
        Get password for a Server.

        """
        return self.manager.clear_password(self)

    def add_fixed_ip(self, network_id):
        """
        Add an IP address on a network.

        :param network_id: The ID of the network the IP should be on.
        """
        self.manager.add_fixed_ip(self, network_id)

    def remove_floating_ip(self, address):
        """
        Remove floating IP from an instance

        :param address: The ip address or FloatingIP to remove
        """
        self.manager.remove_floating_ip(self, address)

    def stop(self):
        """
        Stop -- Stop the running server.
        """
        self.manager.stop(self)

    def force_delete(self):
        """
        Force delete -- Force delete a server.
        """
        self.manager.force_delete(self)

    def restore(self):
        """
        Restore -- Restore a server in 'soft-deleted' state.
        """
        self.manager.restore(self)

    def start(self):
        """
        Start -- Start the paused server.
        """
        self.manager.start(self)

    def pause(self):
        """
        Pause -- Pause the running server.
        """
        self.manager.pause(self)

    def unpause(self):
        """
        Unpause -- Unpause the paused server.
        """
        self.manager.unpause(self)

    def lock(self):
        """
        Lock -- Lock the instance from certain operations.
        """
        self.manager.lock(self)

    def unlock(self):
        """
        Unlock -- Remove instance lock.
        """
        self.manager.unlock(self)

    def suspend(self):
        """
        Suspend -- Suspend the running server.
        """
        self.manager.suspend(self)

    def resume(self):
        """
        Resume -- Resume the suspended server.
        """
        self.manager.resume(self)

    def rescue(self):
        """
        Rescue -- Rescue the problematic server.
        """
        return self.manager.rescue(self)

    def unrescue(self):
        """
        Unrescue -- Unrescue the rescued server.
        """
        self.manager.unrescue(self)

    def shelve(self):
        """
        Shelve -- Shelve the server.
        """
        self.manager.shelve(self)

    def shelve_offload(self):
        """
        Shelve_offload -- Remove a shelved server from the compute node.
        """
        self.manager.shelve_offload(self)

    def unshelve(self):
        """
        Unshelve -- Unshelve the server.
        """
        self.manager.unshelve(self)

    def diagnostics(self):
        """Diagnostics -- Retrieve server diagnostics."""
        return self.manager.diagnostics(self)

    def migrate(self):
        """
        Migrate a server to a new host.
        """
        self.manager.migrate(self)

    def remove_fixed_ip(self, address):
        """
        Remove an IP address.

        :param address: The IP address to remove.
        """
        self.manager.remove_fixed_ip(self, address)

    def change_password(self, password):
        """
        Update the password for a server.
        """
        self.manager.change_password(self, password)

    def reboot(self, reboot_type=REBOOT_SOFT):
        """
        Reboot the server.

        :param reboot_type: either :data:`REBOOT_SOFT` for a software-level
                reboot, or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self.manager.reboot(self, reboot_type)

    def rebuild(self, image, password=None, **kwargs):
        """
        Rebuild -- shut down and then re-image -- this server.

        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as password on the rebuilt server.
        """
        return self.manager.rebuild(self, image, password=password, **kwargs)

    def resize(self, flavor, **kwargs):
        """
        Resize the server's resources.

        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self.manager.resize(self, flavor, **kwargs)

    def create_image(self, image_name, metadata=None):
        """
        Create an image based on this server.

        :param image_name: The name to assign the newly create image.
        :param metadata: Metadata to assign to the image.
        """
        return self.manager.create_image(self, image_name, metadata)

    def backup(self, backup_name, backup_type, rotation):
        """
        Backup a server instance.

        :param backup_name: Name of the backup image
        :param backup_type: The backup type, like 'daily' or 'weekly'
        :param rotation: Int parameter representing how many backups to
                        keep around.
        """
        self.manager.backup(self, backup_name, backup_type, rotation)

    def confirm_resize(self):
        """
        Confirm that the resize worked, thus removing the original server.
        """
        self.manager.confirm_resize(self)

    def revert_resize(self):
        """
        Revert a previous resize, switching back to the old server.
        """
        self.manager.revert_resize(self)

    @property
    def networks(self):
        """
        Generate a simplified list of addresses
        """
        networks = {}
        try:
            for network_label, address_list in self.addresses.items():
                networks[network_label] = [a['addr'] for a in address_list]
            return networks
        except Exception:
            return {}

    def live_migrate(self, host=None,
                     block_migration=False,
                     disk_over_commit=False):
        """
        Migrates a running instance to a new machine.
        """
        self.manager.live_migrate(self, host,
                                  block_migration,
                                  disk_over_commit)

    def reset_state(self, state='error'):
        """
        Reset the state of an instance to active or error.
        """
        self.manager.reset_state(self, state)

    def reset_network(self):
        """
        Reset network of an instance.
        """
        self.manager.reset_network(self)

    def evacuate(self, host, on_shared_storage, password=None):
        """
        Evacuate an instance from failed host to specified host.

        :param host: Name of the target host
        :param on_shared_storage: Specifies whether instance files located
                        on shared storage
        :param password: string to set as password on the evacuated server.
        """
        return self.manager.evacuate(self, host, on_shared_storage, password)

    def interface_list(self):
        """
        List interfaces attached to an instance.
        """
        return self.manager.interface_list(self)

    def interface_attach(self, port_id, net_id, fixed_ip):
        """
        Attach a network interface to an instance.
        """
        return self.manager.interface_attach(self, port_id, net_id, fixed_ip)

    def interface_detach(self, port_id):
        """
        Detach a network interface from an instance.
        """
        return self.manager.interface_detach(self, port_id)


class ServerManager(base.BootingManagerWithFind):
    resource_class = Server

    def _boot(self, resource_url, response_key, name, image, flavor,
              meta=None, userdata=None,
              reservation_id=None, return_raw=False, min_count=None,
              max_count=None, security_groups=None, key_name=None,
              availability_zone=None, block_device_mapping=None,
              block_device_mapping_v2=None, nics=None, scheduler_hints=None,
              config_drive=None, admin_pass=None, **kwargs):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param reservation_id: a UUID for the set of servers being requested.
        :param return_raw: If True, don't try to coearse the result into
                           a Resource object.
        :param security_groups: list of security group names
        :param key_name: (optional extension) name of keypair to inject into
                         the instance
        :param availability_zone: Name of the availability zone for instance
                                  placement.
        :param block_device_mapping: A dict of block device mappings for this
                                     server.
        :param block_device_mapping_v2: A dict of block device mappings V2 for
                                        this server.
        :param nics:  (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, etc.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                              specified by the client to help boot an instance.
        :param config_drive: (optional extension) value for config drive
                            either boolean, or volume-id
        :param admin_pass: admin password for the server.
        """
        body = {"server": {
            "name": name,
            "image_ref": str(base.getid(image)) if image else '',
            "flavor_ref": str(base.getid(flavor)),
        }}
        if userdata:
            if hasattr(userdata, 'read'):
                userdata = userdata.read()

            if six.PY3:
                userdata = userdata.encode("utf-8")
            else:
                userdata = strutils.safe_encode(userdata)

            data = base64.b64encode(userdata).decode('utf-8')
            body["server"]["os-user-data:user_data"] = data
        if meta:
            body["server"]["metadata"] = meta
        if reservation_id:
            body["server"][
                "os-multiple-create:return_reservation_id"] = reservation_id
        if key_name:
            body["server"]["key_name"] = key_name
        if scheduler_hints:
            body["server"][
                "os-scheduler-hints:scheduler_hints"] = scheduler_hints
        if config_drive:
            body["server"]["os-config-drive:config_drive"] = config_drive
        if admin_pass:
            body["server"]["admin_password"] = admin_pass
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        body["server"]["os-multiple-create:min_count"] = min_count
        body["server"]["os-multiple-create:max_count"] = max_count

        if security_groups:
            body["server"]["os-security-groups:security_groups"] = \
              [{'name': sg} for sg in security_groups]

        if availability_zone:
            body["server"][
                "os-availability-zone:availability_zone"] = availability_zone

        # Block device mappings are passed as a list of dictionaries
        if block_device_mapping:
            bdm_param = 'os-block-device-mapping:block_device_mapping'
            body['server'][bdm_param] = \
              self._parse_block_device_mapping(block_device_mapping)
        elif block_device_mapping_v2:
            # Append the image to the list only if we have new style BDMs
            if image:
                bdm_dict = {'uuid': image.id, 'source_type': 'image',
                            'destination_type': 'local', 'boot_index': 0,
                            'delete_on_termination': True}
                block_device_mapping_v2.insert(0, bdm_dict)

            body['server'][bdm_param] = block_device_mapping_v2

        if nics is not None:
            # NOTE(tr3buchet): nics can be an empty list
            all_net_data = []
            for nic_info in nics:
                net_data = {}
                # if value is empty string, do not send value in body
                if nic_info.get('net-id'):
                    net_data['uuid'] = nic_info['net-id']
                if (nic_info.get('v4-fixed-ip') and
                    nic_info.get('v6-fixed-ip')):
                    raise base.exceptions.CommandError(_(
                        "Only one of 'v4-fixed-ip' and 'v6-fixed-ip' may be"
                        " provided."))
                elif nic_info.get('v4-fixed-ip'):
                    net_data['fixed_ip'] = nic_info['v4-fixed-ip']
                elif nic_info.get('v6-fixed-ip'):
                    net_data['fixed_ip'] = nic_info['v6-fixed-ip']
                if nic_info.get('port-id'):
                    net_data['port'] = nic_info['port-id']
                all_net_data.append(net_data)
            body['server']['networks'] = all_net_data

        return self._create(resource_url, body, response_key,
                            return_raw=return_raw, **kwargs)

    def get(self, server):
        """
        Get a server.

        :param server: ID of the :class:`Server` to get.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % base.getid(server), "server")

    def list(self, detailed=True, search_opts=None, marker=None, limit=None):
        """
        Get a list of servers.

        :param detailed: Whether to return detailed server info (optional).
        :param search_opts: Search options to filter out servers (optional).
        :param marker: Begin returning servers that appear later in the server
                       list than that represented by this server id (optional).
        :param limit: Maximum number of servers to return (optional).

        :rtype: list of :class:`Server`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in six.iteritems(search_opts):
            if val:
                qparams[opt] = val

        if marker:
            qparams['marker'] = marker

        if limit:
            qparams['limit'] = limit

        # Transform the dict to a sequence of two-element tuples in fixed
        # order, then the encoded string will be consistent in Python 2&3.
        if qparams:
            new_qparams = sorted(qparams.items(), key=lambda x: x[0])
            query_string = "?%s" % parse.urlencode(new_qparams)
        else:
            query_string = ""

        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/servers%s%s" % (detail, query_string), "servers")

    def add_fixed_ip(self, server, network_id):
        """
        Add an IP address on a network.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param network_id: The ID of the network the IP should be on.
        """
        self._action('add_fixed_ip', server, {'network_id': network_id})

    def remove_fixed_ip(self, server, address):
        """
        Remove an IP address.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param address: The IP address to remove.
        """
        self._action('remove_fixed_ip', server, {'address': address})

    def get_vnc_console(self, server, console_type):
        """
        Get a vnc console for an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param console_type: Type of vnc console to get ('novnc' or 'xvpvnc')
        """

        return self._action('get_vnc_console', server,
                            {'type': console_type})[1]

    def get_spice_console(self, server, console_type):
        """
        Get a spice console for an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param console_type: Type of spice console to get ('spice-html5')
        """

        return self._action('get_spice_console', server,
                            {'type': console_type})[1]

    def get_password(self, server, private_key):
        """
        Get password for an instance

        Requires that openssl is installed and in the path

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param private_key: The private key to decrypt password
        """

        _resp, body = self.api.client.get("/servers/%s/os-server-password"
                                          % base.getid(server))
        if body and body.get('password'):
            try:
                return crypto.decrypt_password(private_key, body['password'])
            except Exception as exc:
                return '%sFailed to decrypt:\n%s' % (exc, body['password'])
        return ''

    def clear_password(self, server):
        """
        Clear password for an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        """

        return self._delete("/servers/%s/os-server-password"
                            % base.getid(server))

    def stop(self, server):
        """
        Stop the server.
        """
        return self._action('stop', server, None)

    def force_delete(self, server):
        """
        Force delete the server.
        """
        return self._action('force_delete', server, None)

    def restore(self, server):
        """
        Restore soft-deleted server.
        """
        return self._action('restore', server, None)

    def start(self, server):
        """
        Start the server.
        """
        self._action('start', server, None)

    def pause(self, server):
        """
        Pause the server.
        """
        self._action('pause', server, None)

    def unpause(self, server):
        """
        Unpause the server.
        """
        self._action('unpause', server, None)

    def lock(self, server):
        """
        Lock the server.
        """
        self._action('lock', server, None)

    def unlock(self, server):
        """
        Unlock the server.
        """
        self._action('unlock', server, None)

    def suspend(self, server):
        """
        Suspend the server.
        """
        self._action('suspend', server, None)

    def resume(self, server):
        """
        Resume the server.
        """
        self._action('resume', server, None)

    def rescue(self, server):
        """
        Rescue the server.
        """
        return self._action('rescue', server, None)

    def unrescue(self, server):
        """
        Unrescue the server.
        """
        self._action('unrescue', server, None)

    def shelve(self, server):
        """
        Shelve the server.
        """
        self._action('shelve', server, None)

    def shelve_offload(self, server):
        """
        Remove a shelved instance from the compute node.
        """
        self._action('shelve_offload', server, None)

    def unshelve(self, server):
        """
        Unshelve the server.
        """
        self._action('unshelve', server, None)

    def diagnostics(self, server):
        """Retrieve server diagnostics."""
        return self.api.client.get("/servers/%s/os-server-diagnostics" %
                                   base.getid(server))

    def create(self, name, image, flavor, meta=None, files=None,
               reservation_id=None, min_count=None,
               max_count=None, security_groups=None, userdata=None,
               key_name=None, availability_zone=None,
               block_device_mapping=None, block_device_mapping_v2=None,
               nics=None, scheduler_hints=None,
               config_drive=None, **kwargs):
        # TODO(anthony): indicate in doc string if param is an extension
        # and/or optional
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param userdata: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param reservation_id: a UUID for the set of servers being requested.
        :param key_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param availability_zone: Name of the availability zone for instance
                                  placement.
        :param block_device_mapping: (optional extension) A dict of block
                      device mappings for this server.
        :param block_device_mapping_v2: (optional extension) A dict of block
                      device mappings for this server.
        :param nics:  (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, port etc.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                            specified by the client to help boot an instance
        :param config_drive: (optional extension) value for config drive
                            either boolean, or volume-id
        """
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        if min_count > max_count:
            min_count = max_count

        boot_args = [name, image, flavor]

        boot_kwargs = dict(
            meta=meta, files=files, userdata=userdata,
            reservation_id=reservation_id, min_count=min_count,
            max_count=max_count, security_groups=security_groups,
            key_name=key_name, availability_zone=availability_zone,
            scheduler_hints=scheduler_hints, config_drive=config_drive,
            **kwargs)

        if block_device_mapping:
            boot_kwargs['block_device_mapping'] = block_device_mapping
        elif block_device_mapping_v2:
            boot_kwargs['block_device_mapping_v2'] = block_device_mapping_v2
        resource_url = "/servers"
        if nics:
            boot_kwargs['nics'] = nics

        response_key = "server"
        return self._boot(resource_url, response_key, *boot_args,
                **boot_kwargs)

    def update(self, server, name=None):
        """
        Update the name or the password for a server.

        :param server: The :class:`Server` (or its ID) to update.
        :param name: Update the server's name.
        """
        if name is None:
            return

        body = {
            "server": {
                "name": name,
            },
        }

        return self._update("/servers/%s" % base.getid(server), body, "server")

    def change_password(self, server, password):
        """
        Update the password for a server.
        """
        self._action("change_password", server, {"admin_password": password})

    def delete(self, server):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self._delete("/servers/%s" % base.getid(server))

    def reboot(self, server, reboot_type=REBOOT_SOFT):
        """
        Reboot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param reboot_type: either :data:`REBOOT_SOFT` for a software-level
                reboot, or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self._action('reboot', server, {'type': reboot_type})

    def rebuild(self, server, image, password=None, **kwargs):
        """
        Rebuild -- shut down and then re-image -- a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as password on the rebuilt server.
        """
        body = {'image_ref': base.getid(image)}
        if password is not None:
            body['admin_password'] = password

        _resp, body = self._action('rebuild', server, body, **kwargs)
        return Server(self, body['server'])

    def migrate(self, server):
        """
        Migrate a server to a new host.

        :param server: The :class:`Server` (or its ID).
        """
        self._action('migrate', server)

    def resize(self, server, flavor, **kwargs):
        """
        Resize a server's resources.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        info = {'flavor_ref': base.getid(flavor)}

        self._action('resize', server, info=info, **kwargs)

    def confirm_resize(self, server):
        """
        Confirm that the resize worked, thus removing the original server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('confirm_resize', server)

    def revert_resize(self, server):
        """
        Revert a previous resize, switching back to the old server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('revert_resize', server)

    def create_image(self, server, image_name, metadata=None):
        """
        Snapshot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image_name: Name to give the snapshot image
        :param meta: Metadata to give newly-created image entity
        """
        body = {'name': image_name, 'metadata': metadata or {}}
        resp = self._action('create_image', server, body)[0]
        location = resp.headers['location']
        image_uuid = location.split('/')[-1]
        return image_uuid

    def backup(self, server, backup_name, backup_type, rotation):
        """
        Backup a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param backup_name: Name of the backup image
        :param backup_type: The backup type, like 'daily' or 'weekly'
        :param rotation: Int parameter representing how many backups to
                        keep around.
        """
        body = {'name': backup_name,
                'backup_type': backup_type,
                'rotation': rotation}
        self._action('create_backup', server, body)

    def set_meta(self, server, metadata):
        """
        Set a servers metadata
        :param server: The :class:`Server` to add metadata to
        :param metadata: A dict of metadata to add to the server
        """
        body = {'metadata': metadata}
        return self._create("/servers/%s/metadata" % base.getid(server),
                             body, "metadata")

    def get_console_output(self, server, length=None):
        """
        Get text console log output from Server.

        :param server: The :class:`Server` (or its ID) whose console output
                        you would like to retrieve.
        :param length: The number of tail loglines you would like to retrieve.
        """
        if length is None:
            # NOTE: On v3 get_console_output API, -1 means an unlimited length.
            # Here translates None, which means an unlimited in the internal
            # implementation, to -1.
            length = -1
        return self._action('get_console_output',
                            server, {'length': length})[1]['output']

    def delete_meta(self, server, keys):
        """
        Delete metadata from an server
        :param server: The :class:`Server` to add metadata to
        :param keys: A list of metadata keys to delete from the server
        """
        for k in keys:
            self._delete("/servers/%s/metadata/%s" % (base.getid(server), k))

    def live_migrate(self, server, host, block_migration, disk_over_commit):
        """
        Migrates a running instance to a new machine.

        :param server: instance id which comes from nova list.
        :param host: destination host name.
        :param block_migration: if True, do block_migration.
        :param disk_over_commit: if True, Allow overcommit.

        """
        self._action('migrate_live', server,
                     {'host': host,
                      'block_migration': block_migration,
                      'disk_over_commit': disk_over_commit})

    def reset_state(self, server, state='error'):
        """
        Reset the state of an instance to active or error.

        :param server: ID of the instance to reset the state of.
        :param state: Desired state; either 'active' or 'error'.
                      Defaults to 'error'.
        """
        self._action('reset_state', server, dict(state=state))

    def reset_network(self, server):
        """
        Reset network of an instance.
        """
        self._action('reset_network', server)

    def evacuate(self, server, host, on_shared_storage, password=None):
        """
        Evacuate a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param host: Name of the target host.
        :param on_shared_storage: Specifies whether instance files located
                        on shared storage
        :param password: string to set as password on the evacuated server.
        """
        body = {
                'host': host,
                'on_shared_storage': on_shared_storage,
                }

        if password is not None:
            body['admin_password'] = password

        return self._action('evacuate', server, body)

    def interface_list(self, server):
        """
        List attached network interfaces

        :param server: The :class:`Server` (or its ID) to query.
        """
        return self._list('/servers/%s/os-attach-interfaces'
                          % base.getid(server), 'interface_attachments')

    def interface_attach(self, server, port_id, net_id, fixed_ip):
        """
        Attach a network_interface to an instance.

        :param server: The :class:`Server` (or its ID) to attach to.
        :param port_id: The port to attach.
        """

        body = {'interface_attachment': {}}
        if port_id:
            body['interface_attachment']['port_id'] = port_id
        if net_id:
            body['interface_attachment']['net_id'] = net_id
        if fixed_ip:
            body['interface_attachment']['fixed_ips'] = [
                {'ip_address': fixed_ip}]

        return self._create('/servers/%s/os-attach-interfaces'
                            % base.getid(server),
                            body, 'interface_attachment')

    def interface_detach(self, server, port_id):
        """
        Detach a network_interface from an instance.

        :param server: The :class:`Server` (or its ID) to detach from.
        :param port_id: The port to detach.
        """
        self._delete('/servers/%s/os-attach-interfaces/%s'
                     % (base.getid(server), port_id))

    def _action(self, action, server, info=None, **kwargs):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/servers/%s/action' % base.getid(server)
        return self.api.client.post(url, body=body)
