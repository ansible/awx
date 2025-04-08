from django.db.models.deletion import DO_NOTHING
from django.db.models.fields import DateTimeField, CharField, PositiveIntegerField
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ForeignKey
from django.utils.translation import gettext_lazy as _

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
        help_text=_('Data saved in this record only applies to this specified job.'),
    )

    organization = ForeignKey(
        'Organization',
        related_name='organization_indirect_host_audits',
        on_delete=DO_NOTHING,
        help_text=_('Applicable organization, inferred from the related job.'),
    )

    inventory = ForeignKey(
        'Inventory',
        related_name='inventory_indirect_host_audits',
        null=True,
        on_delete=DO_NOTHING,
        help_text=_('The inventory the related job ran against, and which the related host is in.'),
    )

    host = ForeignKey('Host', related_name='host_indirect_host_audits', null=True, on_delete=DO_NOTHING, help_text=_('The host this audit record is for.'))

    name = CharField(max_length=255, help_text=_('The Ansible name of the host that this audit record is for.'))

    canonical_facts = JSONField(default=dict, help_text=_('Facts about the host that will be used for managed node deduplication.'))

    facts = JSONField(default=dict, help_text=_('Non canonical facts having additional info about the managed node.'))

    events = JSONField(default=list, help_text=_('List of fully-qualified names of modules that ran against the host in the job.'))

    count = PositiveIntegerField(default=0, help_text=_('Counter of how many times registered modules were invoked on the host.'))
