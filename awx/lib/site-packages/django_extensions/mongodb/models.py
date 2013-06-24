"""
Django Extensions abstract base mongoengine Document classes.
"""
import datetime
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, DateTimeField
from mongoengine.queryset import QuerySetManager
from django.utils.translation import ugettext_lazy as _
from django_extensions.mongodb.fields import ModificationDateTimeField, CreationDateTimeField, AutoSlugField


class TimeStampedModel(Document):
    """ TimeStampedModel
    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

    class Meta:
        abstract = True


class TitleSlugDescriptionModel(Document):
    """ TitleSlugDescriptionModel
    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.
    """
    title = StringField(_('title'), max_length=255)
    slug = AutoSlugField(_('slug'), populate_from='title')
    description = StringField(_('description'), blank=True, null=True)

    class Meta:
        abstract = True


class ActivatorModelManager(QuerySetManager):
    """ ActivatorModelManager
    Manager to return instances of ActivatorModel: SomeModel.objects.active() / .inactive()
    """
    def active(self):
        """ Returns active instances of ActivatorModel: SomeModel.objects.active() """
        return super(ActivatorModelManager, self).get_query_set().filter(status=1)

    def inactive(self):
        """ Returns inactive instances of ActivatorModel: SomeModel.objects.inactive() """
        return super(ActivatorModelManager, self).get_query_set().filter(status=0)


class ActivatorModel(Document):
    """ ActivatorModel
    An abstract base class model that provides activate and deactivate fields.
    """
    STATUS_CHOICES = (
        (0, _('Inactive')),
        (1, _('Active')),
    )
    status = IntField(_('status'), choices=STATUS_CHOICES, default=1)
    activate_date = DateTimeField(blank=True, null=True, help_text=_('keep empty for an immediate activation'))
    deactivate_date = DateTimeField(blank=True, null=True, help_text=_('keep empty for indefinite activation'))
    objects = ActivatorModelManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.activate_date:
            self.activate_date = datetime.datetime.now()
        super(ActivatorModel, self).save(*args, **kwargs)
