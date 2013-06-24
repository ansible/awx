"""
Django Extensions abstract base model classes.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField, AutoSlugField)

try:
    from django.utils.timezone import now as datetime_now
    assert datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now


class TimeStampedModel(models.Model):
    """ TimeStampedModel
    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)
        abstract = True


class TitleSlugDescriptionModel(models.Model):
    """ TitleSlugDescriptionModel
    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.
    """
    title = models.CharField(_('title'), max_length=255)
    slug = AutoSlugField(_('slug'), populate_from='title')
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        abstract = True


class ActivatorModelManager(models.Manager):
    """ ActivatorModelManager
    Manager to return instances of ActivatorModel: SomeModel.objects.active() / .inactive()
    """
    def active(self):
        """ Returns active instances of ActivatorModel: SomeModel.objects.active() """
        return self.get_query_set().filter(status=ActivatorModel.ACTIVE_STATUS)

    def inactive(self):
        """ Returns inactive instances of ActivatorModel: SomeModel.objects.inactive() """
        return self.get_query_set().filter(status=ActivatorModel.INACTIVE_STATUS)


class ActivatorModel(models.Model):
    """ ActivatorModel
    An abstract base class model that provides activate and deactivate fields.
    """
    INACTIVE_STATUS, ACTIVE_STATUS = range(2)
    STATUS_CHOICES = (
        (INACTIVE_STATUS, _('Inactive')),
        (ACTIVE_STATUS, _('Active')),
    )
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=ACTIVE_STATUS)
    activate_date = models.DateTimeField(blank=True, null=True, help_text=_('keep empty for an immediate activation'))
    deactivate_date = models.DateTimeField(blank=True, null=True, help_text=_('keep empty for indefinite activation'))
    objects = ActivatorModelManager()

    class Meta:
        ordering = ('status', '-activate_date',)
        abstract = True

    def save(self, *args, **kwargs):
        if not self.activate_date:
            self.activate_date = datetime_now()
        super(ActivatorModel, self).save(*args, **kwargs)
