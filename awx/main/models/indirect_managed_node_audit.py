from django.db.models.deletion import DO_NOTHING
from django.db.models.fields import DateTimeField, CharField, PositiveIntegerField
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ForeignKey
from awx.main.models import BaseModel


class IndirectManagedNodeAudit(BaseModel):
    """
    IndirectManagedNodeAudit stores information about indirectly created or managed hosts
    """

    class Meta:
        app_label = 'main'
        unique_together = [('name', 'job')]

    created = DateTimeField(auto_now_add=True)

    job = ForeignKey(
        'Job',
        related_name='job_indirect_host_audits',
        on_delete=DO_NOTHING,
        editable=False,
    )

    organization = ForeignKey(
        'Organization',
        related_name='organization_indirect_host_audits',
        on_delete=DO_NOTHING,
    )

    inventory = ForeignKey(
        'Inventory',
        related_name='inventory_indirect_host_audits',
        null=True,
        on_delete=DO_NOTHING,
    )

    host = ForeignKey(
        'Host',
        related_name='host_indirect_host_audits',
        null=True,
        on_delete=DO_NOTHING,
    )

    name = CharField(max_length=255)

    canonical_facts = JSONField(default=dict)

    facts = JSONField(default=dict)

    events = JSONField(default=list)

    count = PositiveIntegerField(default=0)
