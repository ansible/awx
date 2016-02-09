# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from django.db import models
from jsonbfield.fields import JSONField

from awx.main.models import Host

__all__ = ('Fact', )

class Fact(models.Model):
    """A model representing a fact returned from Ansible.
    Facts are stored as JSON dictionaries.
    """
    host = models.ForeignKey(
        Host,
        related_name='facts',
        db_index=True,
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=None, editable=False)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    modified = models.DateTimeField(editable=False, auto_now=True)
    module = models.CharField(max_length=128)
    facts = JSONField(blank=True, default={})

    class Meta:
        app_label = 'main'
        index_together = [
            ["timestamp", "module", "host"],
        ]

