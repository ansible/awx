# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from awx.main.fields import JSONBField

__all__ = ('Fact',)

logger = logging.getLogger('awx.main.models.fact')


class Fact(models.Model):
    """A model representing a fact returned from Ansible.
    Facts are stored as JSON dictionaries.
    """
    host = models.ForeignKey(
        'Host',
        related_name='facts',
        db_index=True,
        on_delete=models.CASCADE,
        help_text=_('Host for the facts that the fact scan captured.'),
    )
    timestamp = models.DateTimeField(
        default=None,
        editable=False,
        help_text=_('Date and time of the corresponding fact scan gathering time.')
    )
    module = models.CharField(max_length=128)
    facts = JSONBField(blank=True, default={}, help_text=_('Arbitrary JSON structure of module facts captured at timestamp for a single host.'))

    class Meta:
        app_label = 'main'
        index_together = [
            ["timestamp", "module", "host"],
        ]

    @staticmethod
    def get_host_fact(host_id, module, timestamp):
        qs = Fact.objects.filter(host__id=host_id, module=module, timestamp__lte=timestamp).order_by('-timestamp')
        if qs:
            return qs[0]
        else:
            return None

    @staticmethod
    def get_timeline(host_id, module=None, ts_from=None, ts_to=None):
        kwargs = {
            'host__id': host_id,
        }
        if module:
            kwargs['module'] = module
        if ts_from and ts_to and ts_from == ts_to:
            kwargs['timestamp'] = ts_from
        else:
            if ts_from:
                kwargs['timestamp__gt'] = ts_from
            if ts_to:
                kwargs['timestamp__lte'] = ts_to
        return Fact.objects.filter(**kwargs).order_by('-timestamp').only('timestamp', 'module').order_by('-timestamp', 'module')

    @staticmethod
    def add_fact(host_id, module, timestamp, facts):
        fact_obj = Fact.objects.create(host_id=host_id, module=module, timestamp=timestamp, facts=facts)
        fact_obj.save()
        return fact_obj

