import logging

from django.db.models import Count


logger = logging.getLogger(__name__)


def _rename_duplicates(cls):
    field = cls._meta.get_field('name')
    max_len = field.max_length
    for organization_id in cls.objects.order_by().values_list('organization_id', flat=True).distinct():
        duplicate_data = cls.objects.values('name').filter(organization_id=organization_id).annotate(count=Count('name')).order_by().filter(count__gt=1)
        for data in duplicate_data:
            name = data['name']
            for idx, ujt in enumerate(cls.objects.filter(name=name, organization_id=organization_id).order_by('created')):
                if idx > 0:
                    suffix = f'_dup{idx}'
                    max_chars = max_len - len(suffix)
                    if len(ujt.name) >= max_chars:
                        ujt.name = ujt.name[:max_chars] + suffix
                    else:
                        ujt.name = ujt.name + suffix
                    logger.info(f'Renaming duplicate {cls._meta.model_name} to `{ujt.name}` because of duplicate name entry')
                    ujt.save(update_fields=['name'])
