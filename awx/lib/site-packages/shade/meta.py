# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import six

NON_CALLABLES = (six.string_types, bool, dict, int, list, type(None))


def find_nova_addresses(addresses, ext_tag=None, key_name=None, version=4):

    ret = []
    for (k, v) in iter(addresses.items()):
        if key_name and k == key_name:
            ret.extend([addrs['addr'] for addrs in v
                        if addrs['version'] == version])
        else:
            for interface_spec in v:
                if ('OS-EXT-IPS:type' in interface_spec
                        and interface_spec['OS-EXT-IPS:type'] == ext_tag
                        and interface_spec['version'] == version):
                    ret.append(interface_spec['addr'])
    return ret


def get_server_ip(server, **kwargs):
    addrs = find_nova_addresses(server.addresses, **kwargs)
    if not addrs:
        return None
    return addrs[0]


def get_server_private_ip(server):
    return get_server_ip(server, ext_tag='fixed', key_name='private')


def get_server_public_ip(server):
    return get_server_ip(server, ext_tag='floating', key_name='public')


def get_groups_from_server(cloud, server, server_vars):
    groups = []

    region = cloud.region_name
    cloud_name = cloud.name

    # Create a group for the cloud
    groups.append(cloud_name)

    # Create a group on region
    groups.append(region)

    # And one by cloud_region
    groups.append("%s_%s" % (cloud_name, region))

    # Check if group metadata key in servers' metadata
    group = server.metadata.get('group')
    if group:
        groups.append(group)

    for extra_group in server.metadata.get('groups', '').split(','):
        if extra_group:
            groups.append(extra_group)

    groups.append('instance-%s' % server.id)

    for key in ('flavor', 'image'):
        if 'name' in server_vars[key]:
            groups.append('%s-%s' % (key, server_vars[key]['name']))

    for key, value in iter(server.metadata.items()):
        groups.append('meta-%s_%s' % (key, value))

    az = server_vars.get('az', None)
    if az:
        # Make groups for az, region_az and cloud_region_az
        groups.append(az)
        groups.append('%s_%s' % (region, az))
        groups.append('%s_%s_%s' % (cloud.name, region, az))
    return groups


def get_hostvars_from_server(cloud, server, mounts=None):
    server_vars = obj_to_dict(server)

    # Fist, add an IP address
    server_vars['public_v4'] = get_server_public_ip(server)
    server_vars['private_v4'] = get_server_private_ip(server)
    if cloud.private:
        interface_ip = server_vars['private_v4']
    else:
        interface_ip = server_vars['public_v4']
    if interface_ip:
        server_vars['interface_ip'] = interface_ip

    server_vars['region'] = cloud.region_name
    server_vars['cloud'] = cloud.name

    flavor_id = server.flavor['id']
    flavor_name = cloud.get_flavor_name(flavor_id)
    if flavor_name:
        server_vars['flavor']['name'] = flavor_name

    # OpenStack can return image as a string when you've booted from volume
    if unicode(server.image) == server.image:
        image_id = server.image
    else:
        image_id = server.image.get('id', None)
    if image_id:
        image_name = cloud.get_image_name(image_id)
        if image_name:
            server_vars['image']['name'] = image_name

    volumes = []
    for vol in cloud.get_volumes(server):
        volume = obj_to_dict(vol)
        # Make things easier to consume elsewhere
        volume['device'] = volume['attachments'][0]['device']
        volumes.append(volume)
    server_vars['volumes'] = volumes
    if mounts:
        for mount in mounts:
            for vol in server_vars['volumes']:
                if vol['display_name'] == mount['display_name']:
                    if 'mount' in mount:
                        vol['mount'] = mount['mount']

    az = server_vars.get('OS-EXT-AZ:availability_zone', None)
    if az:
        server_vars['az'] = az

    return server_vars


def obj_to_dict(obj):
    """ Turn an object with attributes into a dict suitable for serializing.

    Some of the things that are returned in OpenStack are objects with
    attributes. That's awesome - except when you want to expose them as JSON
    structures. We use this as the basis of get_hostvars_from_server above so
    that we can just have a plain dict of all of the values that exist in the
    nova metadata for a server.
    """
    instance = {}
    for key in dir(obj):
        value = getattr(obj, key)
        if isinstance(value, NON_CALLABLES) and not key.startswith('_'):
            instance[key] = value
    return instance


def warlock_to_dict(obj):
    # glanceclient v2 uses warlock to construct its objects. Warlock does
    # deep black magic to attribute look up to support validation things that
    # means we cannot use normal obj_to_dict
    obj_dict = {}
    for key in obj.keys():
        obj_dict[key] = obj[key]
    return obj_dict
