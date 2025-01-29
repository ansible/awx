from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from awx.main.models import BaseModel


class EventQuery(BaseModel):
    """
    Event queries are jq present in some collections and used to filter job events
    for indirectly created resources.
    """

    class Meta:
        app_label = 'main'
        unique_together = ['fqcn', 'collection_version']

    fqcn = models.CharField(max_length=255, help_text=_('Fully-qualified collection name.'))
    collection_version = models.CharField(max_length=32, help_text=_('Version of the collection this data applies to.'))
    event_query = models.JSONField(default=dict, help_text=_('The extensions/audit/event_query.yml file content scraped from the collection.'))

    def validate_unique(self, exclude=None):
        try:
            EventQuery.objects.get(fqcn=self.fqcn, collection_version=self.collection_version)
        except EventQuery.DoesNotExist:
            return

        raise ValidationError(f'an event query for collection {self.fqcn}, version {self.collection_version} already exists')
