import json

from django.utils.translation import ugettext_lazy as _


FrozenInjectors = dict()


class PluginFileInjector(object):
    plugin_name = None  # Ansible core name used to reference plugin
    # every source should have collection, these are for the collection name
    namespace = None
    collection = None

    def inventory_as_dict(self, inventory_source, private_data_dir):
        """Default implementation of inventory plugin file contents.
        There are some valid cases when all parameters can be obtained from
        the environment variables, example "plugin: linode" is valid
        ideally, however, some options should be filled from the inventory source data
        """
        if self.plugin_name is None:
            raise NotImplementedError('At minimum the plugin name is needed for inventory plugin use.')
        proper_name = f'{self.namespace}.{self.collection}.{self.plugin_name}'
        return {'plugin': proper_name}


class azure_rm(PluginFileInjector):
    plugin_name = 'azure_rm'
    namespace = 'azure'
    collection = 'azcollection'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(azure_rm, self).inventory_as_dict(inventory_source, private_data_dir)

        source_vars = inventory_source.source_vars_dict

        ret['fail_on_template_errors'] = False

        group_by_hostvar = {
            'location': {'prefix': '', 'separator': '', 'key': 'location'},
            'tag': {'prefix': '', 'separator': '', 'key': 'tags.keys() | list if tags else []'},
            # Introduced with https://github.com/ansible/ansible/pull/53046
            'security_group': {'prefix': '', 'separator': '', 'key': 'security_group'},
            'resource_group': {'prefix': '', 'separator': '', 'key': 'resource_group'},
            # Note, os_family was not documented correctly in script, but defaulted to grouping by it
            'os_family': {'prefix': '', 'separator': '', 'key': 'os_disk.operating_system_type'}
        }
        # by default group by everything
        # always respect user setting, if they gave it
        group_by = [
            grouping_name for grouping_name in group_by_hostvar
            if source_vars.get('group_by_{}'.format(grouping_name), True)
        ]
        ret['keyed_groups'] = [group_by_hostvar[grouping_name] for grouping_name in group_by]
        if 'tag' in group_by:
            # Nasty syntax to reproduce "key_value" group names in addition to "key"
            ret['keyed_groups'].append({
                'prefix': '', 'separator': '',
                'key': r'dict(tags.keys() | map("regex_replace", "^(.*)$", "\1_") | list | zip(tags.values() | list)) if tags else []'
            })

        # Compatibility content
        # TODO: add proper support for instance_filters non-specific to compatibility
        # TODO: add proper support for group_by non-specific to compatibility
        # Dashes were not configurable in azure_rm.py script, we do not want unicode, so always use this
        ret['use_contrib_script_compatible_sanitization'] = True
        # use same host names as script
        ret['plain_host_names'] = True
        # By default the script did not filter hosts
        ret['default_host_filters'] = []
        # User-given host filters
        user_filters = []
        old_filterables = [
            ('resource_groups', 'resource_group'),
            ('tags', 'tags')
            # locations / location would be an entry
            # but this would conflict with source_regions
        ]
        for key, loc in old_filterables:
            value = source_vars.get(key, None)
            if value and isinstance(value, str):
                # tags can be list of key:value pairs
                #  e.g. 'Creator:jmarshall, peanutbutter:jelly'
                # or tags can be a list of keys
                #  e.g. 'Creator, peanutbutter'
                if key == "tags":
                    # grab each key value pair
                    for kvpair in value.split(','):
                        # split into key and value
                        kv = kvpair.split(':')
                        # filter out any host that does not have key
                        # in their tags.keys() variable
                        user_filters.append('"{}" not in tags.keys()'.format(kv[0].strip()))
                        # if a value is provided, check that the key:value pair matches
                        if len(kv) > 1:
                            user_filters.append('tags["{}"] != "{}"'.format(kv[0].strip(), kv[1].strip()))
                else:
                    user_filters.append('{} not in {}'.format(
                        loc, value.split(',')
                    ))
        if user_filters:
            ret.setdefault('exclude_host_filters', [])
            ret['exclude_host_filters'].extend(user_filters)

        ret['conditional_groups'] = {'azure': True}
        ret['hostvar_expressions'] = {
            'provisioning_state': 'provisioning_state | title',
            'computer_name': 'name',
            'type': 'resource_type',
            'private_ip': 'private_ipv4_addresses[0] if private_ipv4_addresses else None',
            'public_ip': 'public_ipv4_addresses[0] if public_ipv4_addresses else None',
            'public_ip_name': 'public_ip_name if public_ip_name is defined else None',
            'public_ip_id': 'public_ip_id if public_ip_id is defined else None',
            'tags': 'tags if tags else None'
        }
        # Special functionality from script
        if source_vars.get('use_private_ip', False):
            ret['hostvar_expressions']['ansible_host'] = 'private_ipv4_addresses[0]'
        # end compatibility content

        if inventory_source.source_regions and 'all' not in inventory_source.source_regions:
            # initialize a list for this section in inventory file
            ret.setdefault('exclude_host_filters', [])
            # make a python list of the regions we will use
            python_regions = [x.strip() for x in inventory_source.source_regions.split(',')]
            # convert that list in memory to python syntax in a string
            # now put that in jinja2 syntax operating on hostvar key "location"
            # and put that as an entry in the exclusions list
            ret['exclude_host_filters'].append("location not in {}".format(repr(python_regions)))
        return ret

class ec2(PluginFileInjector):
    plugin_name = 'aws_ec2'
    namespace = 'amazon'
    collection = 'aws'


    def _get_ec2_group_by_choices(self):
        return [
            ('ami_id', _('Image ID')),
            ('availability_zone', _('Availability Zone')),
            ('aws_account', _('Account')),
            ('instance_id', _('Instance ID')),
            ('instance_state', _('Instance State')),
            ('platform', _('Platform')),
            ('instance_type', _('Instance Type')),
            ('key_pair', _('Key Name')),
            ('region', _('Region')),
            ('security_group', _('Security Group')),
            ('tag_keys', _('Tags')),
            ('tag_none', _('Tag None')),
            ('vpc_id', _('VPC ID')),
        ]

    def _compat_compose_vars(self):
        return {
            # vars that change
            'ec2_block_devices': (
                "dict(block_device_mappings | map(attribute='device_name') | list | zip(block_device_mappings "
                "| map(attribute='ebs.volume_id') | list))"
            ),
            'ec2_dns_name': 'public_dns_name',
            'ec2_group_name': 'placement.group_name',
            'ec2_instance_profile': 'iam_instance_profile | default("")',
            'ec2_ip_address': 'public_ip_address',
            'ec2_kernel': 'kernel_id | default("")',
            'ec2_monitored':  "monitoring.state in ['enabled', 'pending']",
            'ec2_monitoring_state': 'monitoring.state',
            'ec2_placement': 'placement.availability_zone',
            'ec2_ramdisk': 'ramdisk_id | default("")',
            'ec2_reason': 'state_transition_reason',
            'ec2_security_group_ids': "security_groups | map(attribute='group_id') | list |  join(',')",
            'ec2_security_group_names': "security_groups | map(attribute='group_name') | list |  join(',')",
            'ec2_tag_Name': 'tags.Name',
            'ec2_state': 'state.name',
            'ec2_state_code': 'state.code',
            'ec2_state_reason': 'state_reason.message if state_reason is defined else ""',
            'ec2_sourceDestCheck': 'source_dest_check | default(false) | lower | string',  # snake_case syntax intended
            'ec2_account_id': 'owner_id',
            # vars that just need ec2_ prefix
            'ec2_ami_launch_index': 'ami_launch_index | string',
            'ec2_architecture': 'architecture',
            'ec2_client_token': 'client_token',
            'ec2_ebs_optimized': 'ebs_optimized',
            'ec2_hypervisor': 'hypervisor',
            'ec2_image_id': 'image_id',
            'ec2_instance_type': 'instance_type',
            'ec2_key_name': 'key_name',
            'ec2_launch_time': r'launch_time | regex_replace(" ", "T") | regex_replace("(\+)(\d\d):(\d)(\d)$", ".\g<2>\g<3>Z")',
            'ec2_platform': 'platform | default("")',
            'ec2_private_dns_name': 'private_dns_name',
            'ec2_private_ip_address': 'private_ip_address',
            'ec2_public_dns_name': 'public_dns_name',
            'ec2_region': 'placement.region',
            'ec2_root_device_name': 'root_device_name',
            'ec2_root_device_type': 'root_device_type',
            # many items need blank defaults because the script tended to keep a common schema
            'ec2_spot_instance_request_id': 'spot_instance_request_id | default("")',
            'ec2_subnet_id': 'subnet_id | default("")',
            'ec2_virtualization_type': 'virtualization_type',
            'ec2_vpc_id': 'vpc_id | default("")',
            # same as ec2_ip_address, the script provided this
            'ansible_host': 'public_ip_address',
            # new with https://github.com/ansible/ansible/pull/53645
            'ec2_eventsSet': 'events | default("")',
            'ec2_persistent': 'persistent | default(false)',
            'ec2_requester_id': 'requester_id | default("")'
        }

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(ec2, self).inventory_as_dict(inventory_source, private_data_dir)

        keyed_groups = []
        group_by_hostvar = {
            'ami_id': {'prefix': '', 'separator': '', 'key': 'image_id', 'parent_group': 'images'},
            # 2 entries for zones for same groups to establish 2 parentage trees
            'availability_zone': {'prefix': '', 'separator': '', 'key': 'placement.availability_zone', 'parent_group': 'zones'},
            'aws_account': {'prefix': '', 'separator': '', 'key': 'ec2_account_id', 'parent_group': 'accounts'},  # composed var
            'instance_id': {'prefix': '', 'separator': '', 'key': 'instance_id', 'parent_group': 'instances'},  # normally turned off
            'instance_state': {'prefix': 'instance_state', 'key': 'ec2_state', 'parent_group': 'instance_states'},  # composed var
            # ec2_platform is a composed var, but group names do not match up to hostvar exactly
            'platform': {'prefix': 'platform', 'key': 'platform | default("undefined")', 'parent_group': 'platforms'},
            'instance_type': {'prefix': 'type', 'key': 'instance_type', 'parent_group': 'types'},
            'key_pair': {'prefix': 'key', 'key': 'key_name', 'parent_group': 'keys'},
            'region': {'prefix': '', 'separator': '', 'key': 'placement.region', 'parent_group': 'regions'},
            # Security requires some ninja jinja2 syntax, credit to s-hertel
            'security_group': {'prefix': 'security_group', 'key': 'security_groups | map(attribute="group_name")', 'parent_group': 'security_groups'},
            # tags cannot be parented in exactly the same way as the script due to
            # https://github.com/ansible/ansible/pull/53812
            'tag_keys': [
                {'prefix': 'tag', 'key': 'tags', 'parent_group': 'tags'},
                {'prefix': 'tag', 'key': 'tags.keys()', 'parent_group': 'tags'}
            ],
            # 'tag_none': None,  # grouping by no tags isn't a different thing with plugin
            # naming is redundant, like vpc_id_vpc_8c412cea, but intended
            'vpc_id': {'prefix': 'vpc_id', 'key': 'vpc_id', 'parent_group': 'vpcs'},
        }
        # -- same-ish as script here --
        group_by = [x.strip().lower() for x in inventory_source.group_by.split(',') if x.strip()]
        for choice in self._get_ec2_group_by_choices():
            value = bool((group_by and choice[0] in group_by) or (not group_by and choice[0] != 'instance_id'))
            # -- end sameness to script --
            if value:
                this_keyed_group = group_by_hostvar.get(choice[0], None)
                # If a keyed group syntax does not exist, there is nothing we can do to get this group
                if this_keyed_group is not None:
                    if isinstance(this_keyed_group, list):
                        keyed_groups.extend(this_keyed_group)
                    else:
                        keyed_groups.append(this_keyed_group)
        # special case, this parentage is only added if both zones and regions are present
        if not group_by or ('region' in group_by and 'availability_zone' in group_by):
            keyed_groups.append({'prefix': '', 'separator': '', 'key': 'placement.availability_zone', 'parent_group': '{{ placement.region }}'})

        source_vars = inventory_source.source_vars_dict
        # This is a setting from the script, hopefully no one used it
        # if true, it replaces dashes, but not in region / loc names
        replace_dash = bool(source_vars.get('replace_dash_in_groups', True))
        # Compatibility content
        legacy_regex = {
            True: r"[^A-Za-z0-9\_]",
            False: r"[^A-Za-z0-9\_\-]"  # do not replace dash, dash is allowed
        }[replace_dash]
        list_replacer = 'map("regex_replace", "{rx}", "_") | list'.format(rx=legacy_regex)
        # this option, a plugin option, will allow dashes, but not unicode
        # when set to False, unicode will be allowed, but it was not allowed by script
        # thus, we always have to use this option, and always use our custom regex
        ret['use_contrib_script_compatible_sanitization'] = True
        for grouping_data in keyed_groups:
            if grouping_data['key'] in ('placement.region', 'placement.availability_zone'):
                # us-east-2 is always us-east-2 according to ec2.py
                # no sanitization in region-ish groups for the script standards, ever ever
                continue
            if grouping_data['key'] == 'tags':
                # dict jinja2 transformation
                grouping_data['key'] = 'dict(tags.keys() | {replacer} | zip(tags.values() | {replacer}))'.format(
                    replacer=list_replacer
                )
            elif grouping_data['key'] == 'tags.keys()' or grouping_data['prefix'] == 'security_group':
                # list jinja2 transformation
                grouping_data['key'] += ' | {replacer}'.format(replacer=list_replacer)
            else:
                # string transformation
                grouping_data['key'] += ' | regex_replace("{rx}", "_")'.format(rx=legacy_regex)
        # end compatibility content

        if source_vars.get('iam_role_arn', None):
            ret['iam_role_arn'] = source_vars['iam_role_arn']

        # This was an allowed ec2.ini option, also plugin option, so pass through
        if source_vars.get('boto_profile', None):
            ret['boto_profile'] = source_vars['boto_profile']

        elif not replace_dash:
            # Using the plugin, but still want dashes allowed
            ret['use_contrib_script_compatible_sanitization'] = True

        if source_vars.get('nested_groups') is False:
            for this_keyed_group in keyed_groups:
                this_keyed_group.pop('parent_group', None)

        if keyed_groups:
            ret['keyed_groups'] = keyed_groups

        # Instance ID not part of compat vars, because of settings.EC2_INSTANCE_ID_VAR
        compose_dict = {'ec2_id': 'instance_id'}
        inst_filters = {}

        # Compatibility content
        compose_dict.update(self._compat_compose_vars())
        # plugin provides "aws_ec2", but not this which the script gave
        ret['groups'] = {'ec2': True}
        if source_vars.get('hostname_variable') is not None:
            hnames = []
            for expr in source_vars.get('hostname_variable').split(','):
                if expr == 'public_dns_name':
                    hnames.append('dns-name')
                elif not expr.startswith('tag:') and '_' in expr:
                    hnames.append(expr.replace('_', '-'))
                else:
                    hnames.append(expr)
            ret['hostnames'] = hnames
        else:
            # public_ip as hostname is non-default plugin behavior, script behavior
            ret['hostnames'] = [
                'network-interface.addresses.association.public-ip',
                'dns-name',
                'private-dns-name'
            ]
        # The script returned only running state by default, the plugin does not
        # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options
        # options: pending | running | shutting-down | terminated | stopping | stopped
        inst_filters['instance-state-name'] = ['running']
        # end compatibility content

        if source_vars.get('destination_variable') or source_vars.get('vpc_destination_variable'):
            for fd in ('destination_variable', 'vpc_destination_variable'):
                if source_vars.get(fd):
                    compose_dict['ansible_host'] = source_vars.get(fd)
                    break

        if compose_dict:
            ret['compose'] = compose_dict

        if inventory_source.instance_filters:
            # logic used to live in ec2.py, now it belongs to us. Yay more code?
            filter_sets = [f for f in inventory_source.instance_filters.split(',') if f]

            for instance_filter in filter_sets:
                # AND logic not supported, unclear how to...
                instance_filter = instance_filter.strip()
                if not instance_filter or '=' not in instance_filter:
                    continue
                filter_key, filter_value = [x.strip() for x in instance_filter.split('=', 1)]
                if not filter_key:
                    continue
                inst_filters[filter_key] = filter_value

        if inst_filters:
            ret['filters'] = inst_filters

        if inventory_source.source_regions and 'all' not in inventory_source.source_regions:
            ret['regions'] = inventory_source.source_regions.split(',')

        return ret


class gce(PluginFileInjector):
    plugin_name = 'gcp_compute'
    namespace = 'google'
    collection = 'cloud'

    def _compat_compose_vars(self):
        # missing: gce_image, gce_uuid
        # https://github.com/ansible/ansible/issues/51884
        return {
            'gce_description': 'description if description else None',
            'gce_machine_type': 'machineType',
            'gce_name': 'name',
            'gce_network': 'networkInterfaces[0].network.name',
            'gce_private_ip': 'networkInterfaces[0].networkIP',
            'gce_public_ip': 'networkInterfaces[0].accessConfigs[0].natIP | default(None)',
            'gce_status': 'status',
            'gce_subnetwork': 'networkInterfaces[0].subnetwork.name',
            'gce_tags': 'tags.get("items", [])',
            'gce_zone': 'zone',
            'gce_metadata': 'metadata.get("items", []) | items2dict(key_name="key", value_name="value")',
            # NOTE: image hostvar is enabled via retrieve_image_info option
            'gce_image': 'image',
            # We need this as long as hostnames is non-default, otherwise hosts
            # will not be addressed correctly, was returned in script
            'ansible_ssh_host': 'networkInterfaces[0].accessConfigs[0].natIP | default(networkInterfaces[0].networkIP)'
        }

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(gce, self).inventory_as_dict(inventory_source, private_data_dir)

        # auth related items
        ret['auth_kind'] = "serviceaccount"

        filters = []
        # TODO: implement gce group_by options
        # gce never processed the group_by field, if it had, we would selectively
        # apply those options here, but it did not, so all groups are added here
        keyed_groups = [
            # the jinja2 syntax is duplicated with compose
            # https://github.com/ansible/ansible/issues/51883
            {'prefix': 'network', 'key': 'gce_subnetwork'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'gce_private_ip'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'gce_public_ip'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'machineType'},
            {'prefix': '', 'separator': '', 'key': 'zone'},
            {'prefix': 'tag', 'key': 'gce_tags'},  # composed var
            {'prefix': 'status', 'key': 'status | lower'},
            # NOTE: image hostvar is enabled via retrieve_image_info option
            {'prefix': '', 'separator': '', 'key': 'image'},
        ]
        # This will be used as the gce instance_id, must be universal, non-compat
        compose_dict = {'gce_id': 'id'}

        # Compatibility content
        # TODO: proper group_by and instance_filters support, irrelevant of compat mode
        # The gce.py script never sanitized any names in any way
        ret['use_contrib_script_compatible_sanitization'] = True
        # Perform extra API query to get the image hostvar
        ret['retrieve_image_info'] = True
        # Add in old hostvars aliases
        compose_dict.update(self._compat_compose_vars())
        # Non-default names to match script
        ret['hostnames'] = ['name', 'public_ip', 'private_ip']
        # end compatibility content

        if keyed_groups:
            ret['keyed_groups'] = keyed_groups
        if filters:
            ret['filters'] = filters
        if compose_dict:
            ret['compose'] = compose_dict
        if inventory_source.source_regions and 'all' not in inventory_source.source_regions:
            ret['zones'] = inventory_source.source_regions.split(',')
        return ret


class vmware(PluginFileInjector):
    plugin_name = 'vmware_vm_inventory'
    namespace = 'community'
    collection = 'vmware'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(vmware, self).inventory_as_dict(inventory_source, private_data_dir)
        ret['strict'] = False
        # Documentation of props, see
        # https://github.com/ansible/ansible/blob/devel/docs/docsite/rst/scenario_guides/vmware_scenarios/vmware_inventory_vm_attributes.rst
        UPPERCASE_PROPS = [
            "availableField",
            "configIssue",
            "configStatus",
            "customValue",  # optional
            "datastore",
            "effectiveRole",
            "guestHeartbeatStatus",  # optional
            "layout",  # optional
            "layoutEx",  # optional
            "name",
            "network",
            "overallStatus",
            "parentVApp",  # optional
            "permission",
            "recentTask",
            "resourcePool",
            "rootSnapshot",
            "snapshot",  # optional
            "triggeredAlarmState",
            "value"
        ]
        NESTED_PROPS = [
            "capability",
            "config",
            "guest",
            "runtime",
            "storage",
            "summary",  # repeat of other properties
        ]
        ret['properties'] = UPPERCASE_PROPS + NESTED_PROPS
        ret['compose'] = {'ansible_host': 'guest.ipAddress'}  # default value
        ret['compose']['ansible_ssh_host'] = ret['compose']['ansible_host']
        # the ansible_uuid was unique every host, every import, from the script
        ret['compose']['ansible_uuid'] = '99999999 | random | to_uuid'
        for prop in UPPERCASE_PROPS:
            if prop == prop.lower():
                continue
            ret['compose'][prop.lower()] = prop
        ret['with_nested_properties'] = True
        # ret['property_name_format'] = 'lower_case'  # only dacrystal/topic/vmware-inventory-plugin-property-format

        # process custom options
        vmware_opts = dict(inventory_source.source_vars_dict.items())
        if inventory_source.instance_filters:
            vmware_opts.setdefault('host_filters', inventory_source.instance_filters)
        if inventory_source.group_by:
            vmware_opts.setdefault('groupby_patterns', inventory_source.group_by)

        alias_pattern = vmware_opts.get('alias_pattern')
        if alias_pattern:
            ret.setdefault('hostnames', [])
            for alias in alias_pattern.split(','):  # make best effort
                striped_alias = alias.replace('{', '').replace('}', '').strip()  # make best effort
                if not striped_alias:
                    continue
                ret['hostnames'].append(striped_alias)

        host_pattern = vmware_opts.get('host_pattern')  # not working in script
        if host_pattern:
            stripped_hp = host_pattern.replace('{', '').replace('}', '').strip()  # make best effort
            ret['compose']['ansible_host'] = stripped_hp
            ret['compose']['ansible_ssh_host'] = stripped_hp

        host_filters = vmware_opts.get('host_filters')
        if host_filters:
            ret.setdefault('filters', [])
            for hf in host_filters.split(','):
                striped_hf = hf.replace('{', '').replace('}', '').strip()  # make best effort
                if not striped_hf:
                    continue
                ret['filters'].append(striped_hf)
        else:
            # default behavior filters by power state
            ret['filters'] = ['runtime.powerState == "poweredOn"']

        groupby_patterns = vmware_opts.get('groupby_patterns')
        ret.setdefault('keyed_groups', [])
        if groupby_patterns:
            for pattern in groupby_patterns.split(','):
                stripped_pattern = pattern.replace('{', '').replace('}', '').strip()  # make best effort
                ret['keyed_groups'].append({
                    'prefix': '', 'separator': '',
                    'key': stripped_pattern
                })
        else:
            # default groups from script
            for entry in ('config.guestId', '"templates" if config.template else "guests"'):
                ret['keyed_groups'].append({
                    'prefix': '', 'separator': '',
                    'key': entry
                })

        return ret


class openstack(PluginFileInjector):
    plugin_name = 'openstack'
    namespace = 'openstack'
    collection = 'cloud'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        def use_host_name_for_name(a_bool_maybe):
            if not isinstance(a_bool_maybe, bool):
                # Could be specified by user via "host" or "uuid"
                return a_bool_maybe
            elif a_bool_maybe:
                return 'name'  # plugin default
            else:
                return 'uuid'

        ret = super(openstack, self).inventory_as_dict(inventory_source, private_data_dir)
        ret['fail_on_errors'] = True
        ret['expand_hostvars'] = True
        ret['inventory_hostname'] = use_host_name_for_name(False)
        # Note: mucking with defaults will break import integrity
        # For the plugin, we need to use the same defaults as the old script
        # or else imports will conflict. To find script defaults you have
        # to read source code of the script.
        #
        # Script Defaults                           Plugin Defaults
        # 'use_hostnames': False,                   'name' (True)
        # 'expand_hostvars': True,                  'no' (False)
        # 'fail_on_errors': True,                   'no' (False)
        #
        # These are, yet again, different from ansible_variables in script logic
        # but those are applied inconsistently
        source_vars = inventory_source.source_vars_dict
        for var_name in ['expand_hostvars', 'fail_on_errors']:
            if var_name in source_vars:
                ret[var_name] = source_vars[var_name]
        if 'use_hostnames' in source_vars:
            ret['inventory_hostname'] = use_host_name_for_name(source_vars['use_hostnames'])
        return ret

class rhv(PluginFileInjector):
    """ovirt uses the custom credential templating, and that is all
    """
    plugin_name = 'ovirt'
    initial_version = '2.9'
    namespace = 'ovirt'
    collection = 'ovirt'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(rhv, self).inventory_as_dict(inventory_source, private_data_dir)
        ret['ovirt_insecure'] = False  # Default changed from script
        # TODO: process strict option upstream
        ret['compose'] = {
            'ansible_host': '(devices.values() | list)[0][0] if devices else None'
        }
        ret['keyed_groups'] = []
        for key in ('cluster', 'status'):
            ret['keyed_groups'].append({'prefix': key, 'separator': '_', 'key': key})
        ret['keyed_groups'].append({'prefix': 'tag', 'separator': '_', 'key': 'tags'})
        ret['ovirt_hostname_preference'] = ['name', 'fqdn']
        source_vars = inventory_source.source_vars_dict
        for key, value in source_vars.items():
            if key == 'plugin':
                continue
            ret[key] = value
        return ret


class satellite6(PluginFileInjector):
    plugin_name = 'foreman'
    namespace = 'theforeman'
    collection = 'foreman'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(satellite6, self).inventory_as_dict(inventory_source, private_data_dir)
        ret['validate_certs'] = False

        group_patterns = '[]'
        group_prefix = 'foreman_'
        want_hostcollections = False
        want_ansible_ssh_host = False
        want_facts = True

        foreman_opts = inventory_source.source_vars_dict.copy()
        for k, v in foreman_opts.items():
            if k == 'satellite6_group_patterns' and isinstance(v, str):
                group_patterns = v
            elif k == 'satellite6_group_prefix' and isinstance(v, str):
                group_prefix = v
            elif k == 'satellite6_want_hostcollections' and isinstance(v, bool):
                want_hostcollections = v
            elif k == 'satellite6_want_ansible_ssh_host' and isinstance(v, bool):
                want_ansible_ssh_host = v
            elif k == 'satellite6_want_facts' and isinstance(v, bool):
                want_facts = v
            # add backwards support for ssl_verify
            # plugin uses new option, validate_certs, instead
            elif k == 'ssl_verify' and isinstance(v, bool):
                ret['validate_certs'] = v
            else:
                ret[k] = str(v)

        # Compatibility content
        group_by_hostvar = {
            "environment":           {"prefix": "{}environment_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['environment_name'] | lower | regex_replace(' ', '') | "
                                             "regex_replace('[^A-Za-z0-9_]', '_') | regex_replace('none', '')"},
            "location":              {"prefix": "{}location_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['location_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "organization":          {"prefix": "{}organization_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['organization_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "lifecycle_environment": {"prefix": "{}lifecycle_environment_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['content_facet_attributes']['lifecycle_environment_name'] | "
                                             "lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "content_view":          {"prefix": "{}content_view_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['content_facet_attributes']['content_view_name'] | "
                                             "lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"}
        }

        ret['legacy_hostvars'] = True  # convert hostvar structure to the form used by the script
        ret['want_params'] = True
        ret['group_prefix'] = group_prefix
        ret['want_hostcollections'] = want_hostcollections
        ret['want_facts'] = want_facts

        if want_ansible_ssh_host:
            ret['compose'] = {'ansible_ssh_host': "foreman['ip6'] | default(foreman['ip'], true)"}
        ret['keyed_groups'] = [group_by_hostvar[grouping_name] for grouping_name in group_by_hostvar]

        def form_keyed_group(group_pattern):
            """
            Converts foreman group_pattern to
            inventory plugin keyed_group

            e.g. {app_param}-{tier_param}-{dc_param}
                 becomes
                 "%s-%s-%s" | format(app_param, tier_param, dc_param)
            """
            if type(group_pattern) is not str:
                return None
            params = re.findall('{[^}]*}', group_pattern)
            if len(params) == 0:
                return None

            param_names = []
            for p in params:
                param_names.append(p[1:-1].strip())  # strip braces and space

            # form keyed_group key by
            # replacing curly braces with '%s'
            # (for use with jinja's format filter)
            key = group_pattern
            for p in params:
                key = key.replace(p, '%s', 1)

            # apply jinja filter to key
            key = '"{}" | format({})'.format(key, ', '.join(param_names))

            keyed_group = {'key': key,
                           'separator': ''}
            return keyed_group

        try:
            group_patterns = json.loads(group_patterns)

            if type(group_patterns) is list:
                for group_pattern in group_patterns:
                    keyed_group = form_keyed_group(group_pattern)
                    if keyed_group:
                        ret['keyed_groups'].append(keyed_group)
        except json.JSONDecodeError:
            logger.warning('Could not parse group_patterns. Expected JSON-formatted string, found: {}'
                           .format(group_patterns))

        return ret


class tower(PluginFileInjector):
    plugin_name = 'tower'
    namespace = 'awx'
    collection = 'awx'

    def inventory_as_dict(self, inventory_source, private_data_dir):
        ret = super(tower, self).inventory_as_dict(inventory_source, private_data_dir)
        # Credentials injected as env vars, same as script
        try:
            # plugin can take an actual int type
            identifier = int(inventory_source.instance_filters)
        except ValueError:
            # inventory_id could be a named URL
            identifier = iri_to_uri(inventory_source.instance_filters)
        ret['inventory_id'] = identifier
        ret['include_metadata'] = True  # used for license check
        return ret


for cls in PluginFileInjector.__subclasses__():
    FrozenInjectors[cls.__name__] = cls
