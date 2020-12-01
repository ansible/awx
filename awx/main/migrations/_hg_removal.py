import logging

from awx.main.utils.common import set_current_apps

logger = logging.getLogger('awx.main.migrations')


def delete_hg_scm(apps, schema_editor):
    set_current_apps(apps)
    Project = apps.get_model('main', 'Project')
    ProjectUpdate = apps.get_model('main', 'ProjectUpdate')

    ProjectUpdate.objects.filter(project__scm_type='hg').delete()
    deleted_ct, deletion_summary = Project.objects.filter(scm_type='hg').delete()

    if deleted_ct:
        logger.warn('Removed {} mercurial projects, deprecation period ended'.format(
            deletion_summary.get('main.Project', '')
        ))
