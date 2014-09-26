# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from django.db import models


class Instance(models.Model):
    """A model representing an Ansible Tower instance, primary or secondary,
    running against this database.
    """
    uuid = models.CharField(max_length=40)
    primary = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'main'

