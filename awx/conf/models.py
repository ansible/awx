# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import json

# Django
from django.db import models

# Tower
from awx.main.models.base import CreatedModifiedModel, prevent_search
from awx.main.fields import JSONField
from awx.main.utils import encrypt_field
from awx.conf import settings_registry

__all__ = ['Setting']


class Setting(CreatedModifiedModel):

    key = models.CharField(
        max_length=255,
    )
    value = JSONField(
        null=True,
    )
    user = prevent_search(models.ForeignKey(
        'auth.User',
        related_name='settings',
        default=None,
        null=True,
        editable=False,
        on_delete=models.CASCADE,
    ))

    def __str__(self):
        try:
            json_value = json.dumps(self.value)
        except ValueError:
            # In the rare case the DB value is invalid JSON.
            json_value = u'<Invalid JSON>'
        if self.user:
            return u'{} ({}) = {}'.format(self.key, self.user, json_value)
        else:
            return u'{} = {}'.format(self.key, json_value)

    def save(self, *args, **kwargs):
        encrypted = settings_registry.is_setting_encrypted(self.key)
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # When first saving to the database, don't store any encrypted field
        # value, but instead save it until after the instance is created.
        # Otherwise, store encrypted value to the database.
        if encrypted:
            if new_instance:
                self._saved_value = self.value
                self.value = ''
            else:
                self.value = encrypt_field(self, 'value')
                if 'value' not in update_fields:
                    update_fields.append('value')
        super(Setting, self).save(*args, **kwargs)
        # After saving a new instance for the first time, set the encrypted
        # field and save again.
        if encrypted and new_instance:
            from awx.main.signals import disable_activity_stream
            with disable_activity_stream():
                self.value = self._saved_value
                self.save(update_fields=['value'])

    @classmethod
    def get_cache_key(self, key):
        return key

    @classmethod
    def get_cache_id_key(self, key):
        return '{}_ID'.format(key)


import awx.conf.signals  # noqa

from awx.main.registrar import activity_stream_registrar  # noqa
activity_stream_registrar.connect(Setting)

import awx.conf.access  # noqa
