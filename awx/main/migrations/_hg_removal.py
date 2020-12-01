import logging

logger = logging.getLogger('awx.main.migrations')


def delete_hg_scm(apps, schema_editor):
    set_current_apps(apps)
    Project = apps.get_model('main', 'Project')
    ProjectUpdate = apps.get_model('main', 'ProjectUpdate')

    ProjectUpdate.objects.filter(project__scm_type='hg').delete()
    Project.objects.filter(scm_type='hg').delete()
