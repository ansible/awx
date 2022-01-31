# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import sys
import logging
import os
from django.db import models
from django.conf import settings

from awx.main.utils.filters import SmartFilter
from awx.main.utils.pglock import advisory_lock
from awx.main.utils.common import get_capacity_type
from awx.main.constants import RECEPTOR_PENDING

___all__ = ['HostManager', 'InstanceManager', 'InstanceGroupManager', 'DeferJobCreatedManager', 'UUID_DEFAULT']

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
        return self.order_by().exclude(inventory_sources__source='controller').values('name').distinct().count()

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
        # If we are running unit tests, return a stub record.
        if settings.IS_TESTING(sys.argv) or hasattr(sys, '_called_from_test'):
            return self.model(id=1, hostname=settings.CLUSTER_HOST_ID, uuid=UUID_DEFAULT)

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

            # Return existing instance
            if instance.exists():
                instance = instance.first()  # in the unusual occasion that there is more than one, only get one
                update_fields = []
                # if instance was retrieved by uuid and hostname has changed, update hostname
                if instance.hostname != hostname:
                    logger.warning("passed in hostname {0} is different from the original hostname {1}, updating to {0}".format(hostname, instance.hostname))
                    instance.hostname = hostname
                    update_fields.append('hostname')
                # if any other fields are to be updated
                if instance.ip_address != ip_address:
                    instance.ip_address = ip_address
                if instance.node_type != node_type:
                    instance.node_type = node_type
                    update_fields.append('node_type')
                if update_fields:
                    instance.save(update_fields=update_fields)
                    return (True, instance)
                else:
                    return (False, instance)

            # Create new instance, and fill in default values
            create_defaults = dict(capacity=0)
            if defaults is not None:
                create_defaults.update(defaults)
            uuid_option = {}
            if uuid is not None:
                uuid_option = dict(uuid=uuid)
            if node_type == 'execution' and 'version' not in create_defaults:
                create_defaults['version'] = RECEPTOR_PENDING
            instance = self.create(hostname=hostname, ip_address=ip_address, node_type=node_type, **create_defaults, **uuid_option)
        return (True, instance)

    def get_or_register(self):
        if settings.AWX_AUTO_DEPROVISION_INSTANCES:
            from awx.main.management.commands.register_queue import RegisterQueue

            pod_ip = os.environ.get('MY_POD_IP')
            if settings.IS_K8S:
                registered = self.register(ip_address=pod_ip, node_type='control', uuid=settings.SYSTEM_UUID)
            else:
                registered = self.register(ip_address=pod_ip, uuid=settings.SYSTEM_UUID)
            RegisterQueue(settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME, 100, 0, [], is_container_group=False).register()
            RegisterQueue(
                settings.DEFAULT_EXECUTION_QUEUE_NAME, 100, 0, [], is_container_group=True, pod_spec_override=settings.DEFAULT_EXECUTION_QUEUE_POD_SPEC_OVERRIDE
            ).register()
            return registered
        else:
            return (False, self.me())


class InstanceGroupManager(models.Manager):
    """A custom manager class for the Instance model.

    Used for global capacity calculations
    """

    def capacity_mapping(self, qs=None):
        """
        Another entry-point to Instance manager method by same name
        """
        if qs is None:
            qs = self.all().prefetch_related('instances')
        instance_ig_mapping = {}
        ig_instance_mapping = {}
        # Create dictionaries that represent basic m2m memberships
        for group in qs:
            ig_instance_mapping[group.name] = set(instance.hostname for instance in group.instances.all() if instance.capacity != 0)
            for inst in group.instances.all():
                if inst.capacity == 0:
                    continue
                instance_ig_mapping.setdefault(inst.hostname, set())
                instance_ig_mapping[inst.hostname].add(group.name)
        # Get IG capacity overlap mapping
        ig_ig_mapping = get_ig_ig_mapping(ig_instance_mapping, instance_ig_mapping)

        return instance_ig_mapping, ig_ig_mapping

    @staticmethod
    def zero_out_group(graph, name, breakdown):
        if name not in graph:
            graph[name] = {}
        graph[name]['consumed_capacity'] = 0
        for capacity_type in ('execution', 'control'):
            graph[name][f'consumed_{capacity_type}_capacity'] = 0
        if breakdown:
            graph[name]['committed_capacity'] = 0
            graph[name]['running_capacity'] = 0

    def capacity_values(self, qs=None, tasks=None, breakdown=False, graph=None):
        """
        Returns a dictionary of capacity values for all IGs
        """
        if qs is None:  # Optionally BYOQS - bring your own queryset
            qs = self.all().prefetch_related('instances')
        instance_ig_mapping, ig_ig_mapping = self.capacity_mapping(qs=qs)

        if tasks is None:
            tasks = self.model.unifiedjob_set.related.related_model.objects.filter(status__in=('running', 'waiting'))

        if graph is None:
            graph = {group.name: {} for group in qs}
        for group_name in graph:
            self.zero_out_group(graph, group_name, breakdown)
        for t in tasks:
            # TODO: dock capacity for isolated job management tasks running in queue
            impact = t.task_impact
            control_groups = []
            if t.controller_node:
                control_groups = instance_ig_mapping.get(t.controller_node, [])
                if not control_groups:
                    logger.warning(f"No instance group found for {t.controller_node}, capacity consumed may be innaccurate.")

            if t.status == 'waiting' or (not t.execution_node and not t.is_container_group_task):
                # Subtract capacity from any peer groups that share instances
                if not t.instance_group:
                    impacted_groups = []
                elif t.instance_group.name not in ig_ig_mapping:
                    # Waiting job in group with 0 capacity has no collateral impact
                    impacted_groups = [t.instance_group.name]
                else:
                    impacted_groups = ig_ig_mapping[t.instance_group.name]
                for group_name in impacted_groups:
                    if group_name not in graph:
                        self.zero_out_group(graph, group_name, breakdown)
                    graph[group_name]['consumed_capacity'] += impact
                    capacity_type = get_capacity_type(t)
                    graph[group_name][f'consumed_{capacity_type}_capacity'] += impact
                    if breakdown:
                        graph[group_name]['committed_capacity'] += impact
                for group_name in control_groups:
                    if group_name not in graph:
                        self.zero_out_group(graph, group_name, breakdown)
                    graph[group_name][f'consumed_control_capacity'] += settings.AWX_CONTROL_NODE_TASK_IMPACT
                    if breakdown:
                        graph[group_name]['committed_capacity'] += settings.AWX_CONTROL_NODE_TASK_IMPACT
            elif t.status == 'running':
                # Subtract capacity from all groups that contain the instance
                if t.execution_node not in instance_ig_mapping:
                    if not t.is_container_group_task:
                        logger.warning('Detected %s running inside lost instance, ' 'may still be waiting for reaper.', t.log_format)
                    if t.instance_group:
                        impacted_groups = [t.instance_group.name]
                    else:
                        impacted_groups = []
                else:
                    impacted_groups = instance_ig_mapping[t.execution_node]

                for group_name in impacted_groups:
                    if group_name not in graph:
                        self.zero_out_group(graph, group_name, breakdown)
                    graph[group_name]['consumed_capacity'] += impact
                    capacity_type = get_capacity_type(t)
                    graph[group_name][f'consumed_{capacity_type}_capacity'] += impact
                    if breakdown:
                        graph[group_name]['running_capacity'] += impact
                for group_name in control_groups:
                    if group_name not in graph:
                        self.zero_out_group(graph, group_name, breakdown)
                    graph[group_name][f'consumed_control_capacity'] += settings.AWX_CONTROL_NODE_TASK_IMPACT
                    if breakdown:
                        graph[group_name]['running_capacity'] += settings.AWX_CONTROL_NODE_TASK_IMPACT
            else:
                logger.error('Programming error, %s not in ["running", "waiting"]', t.log_format)
        return graph
