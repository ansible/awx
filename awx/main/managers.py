# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import sys
from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.db.models import Sum
from django.conf import settings

from awx.main.utils.filters import SmartFilter

___all__ = ['HostManager', 'InstanceManager']


class HostManager(models.Manager):
    """Custom manager class for Hosts model."""

    def active_count(self):
        """Return count of active, unique hosts for licensing."""
        try:
            return self.order_by('name').distinct('name').count()
        except NotImplementedError: # For unit tests only, SQLite doesn't support distinct('name')
            return len(set(self.values_list('name', flat=True)))

    def get_queryset(self):
        """When the parent instance of the host query set has a `kind=smart` and a `host_filter`
        set. Use the `host_filter` to generate the queryset for the hosts.
        """
        qs = super(HostManager, self).get_queryset()
        if (hasattr(self, 'instance') and
           hasattr(self.instance, 'host_filter') and
           hasattr(self.instance, 'kind')):
            if self.instance.kind == 'smart' and self.instance.host_filter is not None:
                    q = SmartFilter.query_from_string(self.instance.host_filter)
                    # If we are using host_filters, disable the core_filters, this allows
                    # us to access all of the available Host entries, not just the ones associated
                    # with a specific FK/relation.
                    #
                    # If we don't disable this, a filter of {'inventory': self.instance} gets automatically
                    # injected by the related object mapper.
                    self.core_filters = {}
                    qs = qs & q
                    return qs.order_by('pk').distinct('name')
        return qs


class InstanceManager(models.Manager):
    """A custom manager class for the Instance model.

    Provides "table-level" methods including getting the currently active
    instance or role.
    """
    def me(self):
        """Return the currently active instance."""
        # If we are running unit tests, return a stub record.
        if settings.IS_TESTING(sys.argv):
            return self.model(id=1,
                              hostname='localhost',
                              uuid='00000000-0000-0000-0000-000000000000')

        node = self.filter(hostname=settings.CLUSTER_HOST_ID)
        if node.exists():
            return node[0]
        raise RuntimeError("No instance found with the current cluster host id")

    def active_count(self):
        """Return count of active Tower nodes for licensing."""
        return self.all().count()

    def total_capacity(self):
        sumval = self.filter(modified__gte=now() - timedelta(seconds=settings.AWX_ACTIVE_NODE_TIME)) \
                     .aggregate(total_capacity=Sum('capacity'))['total_capacity']
        return max(50, sumval)

    def my_role(self):
        # NOTE: TODO: Likely to repurpose this once standalone ramparts are a thing
        return "tower"
