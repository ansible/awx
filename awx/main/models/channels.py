from django.db import models


class ChannelGroup(models.Model):
    group = models.CharField(max_length=200, unique=True)
    channels = models.TextField()
