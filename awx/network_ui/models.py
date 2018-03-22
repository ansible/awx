from django.db import models


class Device(models.Model):

    id = models.AutoField(primary_key=True,)
    topology = models.ForeignKey('Topology',)
    name = models.CharField(max_length=200, blank=True)
    x = models.IntegerField()
    y = models.IntegerField()
    cid = models.IntegerField()
    device_type = models.CharField(max_length=200, blank=True)
    interface_id_seq = models.IntegerField(default=0,)
    host = models.ForeignKey('main.Host', default=None, null=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.name


class Link(models.Model):

    id = models.AutoField(primary_key=True,)
    from_device = models.ForeignKey('Device', related_name='from_link',)
    to_device = models.ForeignKey('Device', related_name='to_link',)
    from_interface = models.ForeignKey('Interface', related_name='from_link',)
    to_interface = models.ForeignKey('Interface', related_name='to_link',)
    cid = models.IntegerField()
    name = models.CharField(max_length=200, blank=True)


class Topology(models.Model):

    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=200, blank=True)
    scale = models.FloatField()
    panX = models.FloatField()
    panY = models.FloatField()
    device_id_seq = models.IntegerField(default=0,)
    link_id_seq = models.IntegerField(default=0,)

    def __unicode__(self):
        return self.name


class Client(models.Model):

    id = models.AutoField(primary_key=True,)


class Interface(models.Model):

    id = models.AutoField(primary_key=True,)
    device = models.ForeignKey('Device',)
    name = models.CharField(max_length=200, blank=True)
    cid = models.IntegerField()

    def __unicode__(self):
        return self.name


class TopologyInventory(models.Model):

    id = models.AutoField(primary_key=True,)
    topology = models.ForeignKey('Topology',)
    inventory = models.ForeignKey('main.Inventory')
