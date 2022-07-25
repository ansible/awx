# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import logging
from django.db import models
from django.conf import settings
from django.db.models.functions import Lower
from awx.main.utils.filters import SmartFilter
from awx.main.utils.pglock import advisory_lock
from awx.main.constants import RECEPTOR_PENDING

___all__ = ['HostManager', 'InstanceManager', 'DeferJobCreatedManager', 'UUID_DEFAULT']

logger = logging.getLogger('awx.main.managers')
UUID_DEFAULT = '00000000-0000-0000-0000-000000000000'


class DeferJobCreatedManager(models.Manager):
    def get_queryset(self):
        return super(DeferJobCreatedManager, self).get_queryset().defer('job_created')


class HostManager(models.Manager):
    """Custom manager class for Hosts model."""

    def active_count(self):
        """Return count of active, unique hosts for licensing.
        Construction of query involves:
         - remove any ordering specified in model's Meta
         - Exclude hosts sourced from another Tower
         - Restrict the query to only return the name column
         - Only consider results that are unique
         - Return the count of this query
        """
        return self.order_by().exclude(inventory_sources__source='controller').values(name_lower=Lower('name')).distinct().count()

    def org_active_count(self, org_id):
        """Return count of active, unique hosts used by an organization.
        Construction of query involves:
         - remove any ordering specified in model's Meta
         - Exclude hosts sourced from another Tower
         - Consider only hosts where the canonical inventory is owned by the organization
         - Restrict the query to only return the name column
         - Only consider results that are unique
         - Return the count of this query
        """
        return self.order_by().exclude(inventory_sources__source='controller').filter(inventory__organization=org_id).values('name').distinct().count()

    def get_queryset(self):
        """When the parent instance of the host query set has a `kind=smart` and a `host_filter`
        set. Use the `host_filter` to generate the queryset for the hosts.
        """
        qs = (
            super(HostManager, self)
            .get_queryset()
            .defer(
                'last_job__extra_vars',
                'last_job_host_summary__job__extra_vars',
                'last_job__artifacts',
                'last_job_host_summary__job__artifacts',
            )
        )

        if hasattr(self, 'instance') and hasattr(self.instance, 'host_filter') and hasattr(self.instance, 'kind'):
            if self.instance.kind == 'smart' and self.instance.host_filter is not None:
                q = SmartFilter.query_from_string(self.instance.host_filter)
                if self.instance.organization_id:
                    q = q.filter(inventory__organization=self.instance.organization_id)
                # If we are using host_filters, disable the core_filters, this allows
                # us to access all of the available Host entries, not just the ones associated
                # with a specific FK/relation.
                #
                # If we don't disable this, a filter of {'inventory': self.instance} gets automatically
                # injected by the related object mapper.
                self.core_filters = {}

                qs = qs & q
                return qs.order_by('name', 'pk').distinct('name')
        return qs


def get_ig_ig_mapping(ig_instance_mapping, instance_ig_mapping):
    # Create IG mapping by union of all groups their instances are members of
    ig_ig_mapping = {}
    for group_name in ig_instance_mapping.keys():
        ig_ig_set = set()
        for instance_hostname in ig_instance_mapping[group_name]:
            ig_ig_set |= instance_ig_mapping[instance_hostname]
        else:
            ig_ig_set.add(group_name)  # Group contains no instances, return self
        ig_ig_mapping[group_name] = ig_ig_set
    return ig_ig_mapping


class InstanceManager(models.Manager):
    """A custom manager class for the Instance model.

    Provides "table-level" methods including getting the currently active
    instance or role.
    """

    def me(self):
        """Return the currently active instance."""
        node = self.filter(hostname=settings.CLUSTER_HOST_ID)
        if node.exists():
            return node[0]
        raise RuntimeError("No instance found with the current cluster host id")

    def register(self, uuid=None, hostname=None, ip_address=None, node_type='hybrid', defaults=None):
        if not hostname:
            hostname = settings.CLUSTER_HOST_ID

        with advisory_lock('instance_registration_%s' % hostname):
            if settings.AWX_AUTO_DEPROVISION_INSTANCES:
                # detect any instances with the same IP address.
                # if one exists, set it to None
                inst_conflicting_ip = self.filter(ip_address=ip_address).exclude(hostname=hostname)
                if inst_conflicting_ip.exists():
                    for other_inst in inst_conflicting_ip:
                        other_hostname = other_inst.hostname
                        other_inst.ip_address = None
                        other_inst.save(update_fields=['ip_address'])
                        logger.warning("IP address {0} conflict detected, ip address unset for host {1}.".format(ip_address, other_hostname))

            # Return existing instance that matches hostname or UUID (default to UUID)
            if uuid is not None and uuid != UUID_DEFAULT and self.filter(uuid=uuid).exists():
                instance = self.filter(uuid=uuid)
            else:
                # if instance was not retrieved by uuid and hostname was, use the hostname
                instance = self.filter(hostname=hostname)

            from awx.main.models import Instance

            # Return existing instance
            if instance.exists():
                instance = instance.first()  # in the unusual occasion that there is more than one, only get one
                instance.node_state = Instance.States.INSTALLED  # Wait for it to show up on the mesh
                update_fields = ['node_state']
                # if instance was retrieved by uuid and hostname has changed, update hostname
                if instance.hostname != hostname:
                    logger.warning("passed in hostname {0} is different from the original hostname {1}, updating to {0}".format(hostname, instance.hostname))
                    instance.hostname = hostname
                    update_fields.append('hostname')
                # if any other fields are to be updated
                if instance.ip_address != ip_address:
                    instance.ip_address = ip_address
                    update_fields.append('ip_address')
                if instance.node_type != node_type:
                    instance.node_type = node_type
                    update_fields.append('node_type')
                if update_fields:
                    instance.save(update_fields=update_fields)
                    return (True, instance)
                else:
                    return (False, instance)

            # Create new instance, and fill in default values
            create_defaults = {'node_state': Instance.States.INSTALLED, 'capacity': 0}
            if defaults is not None:
                create_defaults.update(defaults)
            uuid_option = {}
            if uuid is not None:
                uuid_option = {'uuid': uuid}
            if node_type == 'execution' and 'version' not in create_defaults:
                create_defaults['version'] = RECEPTOR_PENDING
            instance = self.create(hostname=hostname, ip_address=ip_address, node_type=node_type, **create_defaults, **uuid_option)
        return (True, instance)
