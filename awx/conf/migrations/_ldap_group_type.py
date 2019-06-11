
import inspect

from django.conf import settings
from django.utils.timezone import now


def fill_ldap_group_type_params(apps, schema_editor):
    group_type = settings.AUTH_LDAP_GROUP_TYPE
    Setting = apps.get_model('conf', 'Setting')

    group_type_params = {'name_attr': 'cn', 'member_attr': 'member'}
    qs = Setting.objects.filter(key='AUTH_LDAP_GROUP_TYPE_PARAMS')
    entry = None
    if qs.exists():
        entry = qs[0]
        group_type_params = entry.value
    else:
        entry = Setting(key='AUTH_LDAP_GROUP_TYPE_PARAMS',
                        value=group_type_params,
                        created=now(),
                        modified=now())

    init_attrs = set(inspect.getargspec(group_type.__init__).args[1:])
    for k in list(group_type_params.keys()):
        if k not in init_attrs:
            del group_type_params[k]

    entry.value = group_type_params
    entry.save()
