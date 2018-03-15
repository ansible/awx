from django.db import models


class Device(models.Model):

    device_id = models.AutoField(primary_key=True,)
    topology = models.ForeignKey('Topology',)
    name = models.CharField(max_length=200, blank=True)
    x = models.IntegerField()
    y = models.IntegerField()
    id = models.IntegerField()
    device_type = models.CharField(max_length=200, blank=True)
    interface_id_seq = models.IntegerField(default=0,)
    host_id = models.IntegerField(default=0,)

    def __unicode__(self):
        return self.name


class Link(models.Model):

    link_id = models.AutoField(primary_key=True,)
    from_device = models.ForeignKey('Device', related_name='from_link',)
    to_device = models.ForeignKey('Device', related_name='to_link',)
    from_interface = models.ForeignKey('Interface', related_name='from_link',)
    to_interface = models.ForeignKey('Interface', related_name='to_link',)
    id = models.IntegerField()
    name = models.CharField(max_length=200, blank=True)


class Topology(models.Model):

    topology_id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=200, blank=True)
    scale = models.FloatField()
    panX = models.FloatField()
    panY = models.FloatField()
    device_id_seq = models.IntegerField(default=0,)
    link_id_seq = models.IntegerField(default=0,)

    def __unicode__(self):
        return self.name


class Client(models.Model):

    client_id = models.AutoField(primary_key=True,)


class Interface(models.Model):

    interface_id = models.AutoField(primary_key=True,)
    device = models.ForeignKey('Device',)
    name = models.CharField(max_length=200, blank=True)
    id = models.IntegerField()

    def __unicode__(self):
        return self.name


class TopologyInventory(models.Model):

    topology_inventory_id = models.AutoField(primary_key=True,)
    topology = models.ForeignKey('Topology',)
    inventory_id = models.IntegerField()
