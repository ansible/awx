from django.core.exceptions import ValidationError
from django.db import models

from awx.main.models import BaseModel


class EventQuery(BaseModel):
    """
    Event queries are jq present in some collections and used to filter job events
    for indirectly created resources.
    """

    class Meta:
        app_label = 'main'
        unique_together = ['fqcn', 'collection_version']

    fqcn = models.CharField(max_length=255)
    collection_version = models.CharField(max_length=32)
    event_query = models.JSONField(default=dict)

    def validate_unique(self, exclude=None):
        try:
            EventQuery.objects.get(fqcn=self.fqcn, collection_version=self.collection_version)
        except EventQuery.DoesNotExist:
            return

        raise ValidationError(f'an event query for collection {self.fqcn}, version {self.collection_version} already exists')
