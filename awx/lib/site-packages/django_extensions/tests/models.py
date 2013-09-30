from django.db import models


class Secret(models.Model):
    name = models.CharField(blank=True, max_length=255, null=True)
    text = models.TextField(blank=True, null=True)


class Name(models.Model):
    name = models.CharField(max_length=50)


class Note(models.Model):
    note = models.TextField()


class Person(models.Model):
    name = models.ForeignKey(Name)
    age = models.PositiveIntegerField()
    children = models.ManyToManyField('self')
    notes = models.ManyToManyField(Note)
