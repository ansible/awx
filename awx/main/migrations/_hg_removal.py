import logging

from awx.main.utils.common import set_current_apps

logger = logging.getLogger('awx.main.migrations')


def delete_hg_scm(apps, schema_editor):
    set_current_apps(apps)
    Project = apps.get_model('main', 'Project')
    ProjectUpdate = apps.get_model('main', 'ProjectUpdate')

    ProjectUpdate.objects.filter(project__scm_type='hg').update(scm_type='')
    update_ct = Project.objects.filter(scm_type='hg').update(scm_type='')

    if update_ct:
        logger.warning('Changed {} mercurial projects to manual, deprecation period ended'.format(update_ct))
