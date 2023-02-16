import inspect

from django.conf import settings

import logging


logger = logging.getLogger('awx.conf.migrations')


def fill_ldap_group_type_params(apps, schema_editor):
    group_type = getattr(settings, 'AUTH_LDAP_GROUP_TYPE', None)
    Setting = apps.get_model('conf', 'Setting')

    group_type_params = {'name_attr': 'cn', 'member_attr': 'member'}
    qs = Setting.objects.filter(key='AUTH_LDAP_GROUP_TYPE_PARAMS')
    entry = None
    if qs.exists():
        entry = qs[0]
        group_type_params = entry.value
    else:
        return  # for new installs we prefer to use the default value

    init_attrs = set(inspect.getfullargspec(group_type.__init__).args[1:])
    for k in list(group_type_params.keys()):
        if k not in init_attrs:
            del group_type_params[k]

    entry.value = group_type_params
    logger.warning(f'Migration updating AUTH_LDAP_GROUP_TYPE_PARAMS with value {entry.value}')
    entry.save()
