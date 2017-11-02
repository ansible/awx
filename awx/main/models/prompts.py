# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models.base import (
    BaseModel,
    JOB_TYPE_CHOICES, VERBOSITY_CHOICES,
    prevent_search
)
from awx.main.fields import JSONField


__all__ = [
    'PromptedFields', 'AskPromptedFields', 'LaunchTimeConfig',
    'ask_mapping'
]


promptable_fields = dict(
    extra_vars = prevent_search(models.TextField(
        blank=True,
        default='',
    )),
    diff_mode = models.BooleanField(
        default=False,
        help_text=_("If enabled, textual changes made to any templated files on the host are shown in the standard output"),
    ),
    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
        default='run',
    ),
    inventory = models.ForeignKey(
        'Inventory',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    ),
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    ),
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    ),
    verbosity = models.PositiveIntegerField(
        choices=VERBOSITY_CHOICES,
        blank=True,
        default=0,
    ),
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    ),
    skip_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
)


ask_mapping = {}

for field_name, field in promptable_fields.items():
    ask_mapping[field_name] = 'ask_{}_on_launch'.format(field_name)

# Special cases
ask_mapping['job_tags'] = 'ask_tags_on_launch'
ask_mapping['extra_vars'] = 'ask_variables_on_launch'
ask_mapping['vault_credential'] = 'ask_credential_on_launch'
ask_mapping['extra_credentials'] = 'ask_credential_on_launch'


# Derive fields for templates that configure prompting with `ask_` fields
ask_fields = {}
for field_name in set(ask_mapping.values()):
    ask_fields[field_name] = models.BooleanField(
        blank=True,
        default=False,
    )


# Derive fields for saved launch configurations
class extracted_field(object):
    """
    Interface for psuedo-property stored in `char_prompts` dict
    """
    def __init__(self, field_name):
        self.field_name = field_name

    def __get__(self, instance, type=None):
        return instance.char_prompts.get(self.field_name, None)

    def __set__(self, instance, value):
        instance.char_prompts[self.field_name] = value


config_fields = {}
for field_name, field in promptable_fields.items():
    if isinstance(field, models.ForeignKey):
        config_fields[field_name] = field
    else:
        config_fields[field_name] = extracted_field(field_name)

config_fields['char_prompts'] = JSONField(
    blank=True,
    default={}
)


def apply_meta_fields(data):
    data['Meta'] = type('Meta', (), {'abstract': True})
    data['__module__'] = __name__


apply_meta_fields(promptable_fields)
apply_meta_fields(ask_fields)
apply_meta_fields(config_fields)


PromptedFields = type('PromptedFields', (BaseModel,), promptable_fields)


AskPromptedFields = type('AskPromptedFields', (BaseModel,), ask_fields)


LaunchTimeConfig = type('LaunchTimeConfig', (BaseModel,), config_fields)
