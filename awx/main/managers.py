# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import sys
import logging
import os

from django.db import models
from django.conf import settings

from awx.main.utils.filters import SmartFilter
from awx.main.utils.pglock import advisory_lock

___all__ = ['HostManager', 'InstanceManager', 'InstanceGroupManager']

logger = logging.getLogger('awx.main.managers')


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
        return self.order_by().exclude(inventory_sources__source='tower').values('name').distinct().count()

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
        return self.order_by().exclude(
            inventory_sources__source='tower'
        ).filter(inventory__organization=org_id).values('name').distinct().count()

    def get_queryset(self):
        """When the parent instance of the host query set has a `kind=smart` and a `host_filter`
        set. Use the `host_filter` to generate the queryset for the hosts.
        """
        qs = super(HostManager, self).get_queryset().defer(
            'last_job__extra_vars',
            'last_job_host_summary__job__extra_vars',
            'last_job__artifacts',
            'last_job_host_summary__job__artifacts',
        )

        if (hasattr(self, 'instance') and
           hasattr(self.instance, 'host_filter') and
           hasattr(self.instance, 'kind')):
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
            return self.model(id=1,
                              hostname='localhost',
                              uuid='00000000-0000-0000-0000-000000000000')

        node = self.filter(hostname=settings.CLUSTER_HOST_ID)
        if node.exists():
            return node[0]
        raise RuntimeError("No instance found with the current cluster host id")

    def register(self, uuid=None, hostname=None, ip_address=None):
        if not uuid:
            uuid = settings.SYSTEM_UUID
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

            instance = self.filter(hostname=hostname)
            if instance.exists():
                instance = instance.get()
                if instance.ip_address != ip_address:
                    instance.ip_address = ip_address
                    instance.save(update_fields=['ip_address'])
                    return (True, instance)
                else:
                    return (False, instance)
            instance = self.create(uuid=uuid,
                                   hostname=hostname,
                                   ip_address=ip_address,
                                   capacity=0)
        return (True, instance)

    def get_or_register(self):
        if settings.AWX_AUTO_DEPROVISION_INSTANCES:
            from awx.main.management.commands.register_queue import RegisterQueue
            pod_ip = os.environ.get('MY_POD_IP')
            registered = self.register(ip_address=pod_ip)
            RegisterQueue('tower', None, 100, 0, []).register()
            return registered
        else:
            return (False, self.me())

    def active_count(self):
        """Return count of active Tower nodes for licensing."""
        return self.all().count()

    def my_role(self):
        # NOTE: TODO: Likely to repurpose this once standalone ramparts are a thing
        return "tower"

    def all_non_isolated(self):
        return self.exclude(rampart_groups__controller__isnull=False)


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
            ig_instance_mapping[group.name] = set(
                instance.hostname for instance in group.instances.all() if
                instance.capacity != 0
            )
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
            tasks = self.model.unifiedjob_set.related.related_model.objects.filter(
                status__in=('running', 'waiting'))

        if graph is None:
            graph = {group.name: {} for group in qs}
        for group_name in graph:
            self.zero_out_group(graph, group_name, breakdown)
        for t in tasks:
            # TODO: dock capacity for isolated job management tasks running in queue
            impact = t.task_impact
            if t.status == 'waiting' or not t.execution_node:
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
                    if breakdown:
                        graph[group_name]['committed_capacity'] += impact
            elif t.status == 'running':
                # Subtract capacity from all groups that contain the instance
                if t.execution_node not in instance_ig_mapping:
                    if not t.is_containerized:
                        logger.warning('Detected %s running inside lost instance, '
                                       'may still be waiting for reaper.', t.log_format)
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
                    if breakdown:
                        graph[group_name]['running_capacity'] += impact
            else:
                logger.error('Programming error, %s not in ["running", "waiting"]', t.log_format)
        return graph
