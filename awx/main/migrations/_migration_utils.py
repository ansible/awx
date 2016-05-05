from awx.main.utils import set_current_apps


def set_current_apps_for_migrations(apps, schema_editor):
    '''
    This is necessary for migrations which do explicit saves on any model that
    has an ImplicitRoleFIeld (which generally means anything that has
    some RBAC bindings associated with it). This sets the current 'apps' that
    the ImplicitRoleFIeld should be using when creating new roles.
    '''
    set_current_apps(apps)
