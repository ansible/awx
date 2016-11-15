# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import json

# Django
from django.db import models

# Tower
from awx.main.models.base import CreatedModifiedModel
from awx.main.fields import JSONField

__all__ = ['Setting']


class Setting(CreatedModifiedModel):

    key = models.CharField(
        max_length=255,
    )
    value = JSONField(
        null=True,
    )
    user = models.ForeignKey(
        'auth.User',
        related_name='settings',
        default=None,
        null=True,
        editable=False,
        on_delete=models.CASCADE,
    )

    def __unicode__(self):
        try:
            json_value = json.dumps(self.value)
        except ValueError:
            # In the rare case the DB value is invalid JSON.
            json_value = u'<Invalid JSON>'
        if self.user:
            return u'{} ({}) = {}'.format(self.key, self.user, json_value)
        else:
            return u'{} = {}'.format(self.key, json_value)

    @classmethod
    def get_cache_key(self, key):
        return key


import awx.conf.signals  # noqa

from awx.main.registrar import activity_stream_registrar  # noqa
activity_stream_registrar.connect(Setting)

import awx.conf.access  # noqa
