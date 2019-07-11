import logging
from time import time

from awx.main.fields import update_role_parentage_for_instance
from awx.main.models.rbac import Role, batch_role_ancestor_rebuilding

logger = logging.getLogger('rbac_migrations')


def create_roles(apps, schema_editor):
    '''
    Implicit role creation happens in our post_save hook for all of our
    resources. Here we iterate through all of our resource types and call
    .save() to ensure all that happens for every object in the system.

    This can be used whenever new roles are introduced in a migration to
    create those roles for pre-existing objects that did not previously
    have them created via signals.
    '''

    models = [
        apps.get_model('main', m) for m in [
            'Organization',
            'Team',
            'Inventory',
            'Project',
            'Credential',
            'CustomInventoryScript',
            'JobTemplate',
        ]
    ]

    with batch_role_ancestor_rebuilding():
        for model in models:
            for obj in model.objects.iterator():
                obj.save()


def delete_all_user_roles(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', "ContentType")
    Role = apps.get_model('main', "Role")
    User = apps.get_model('auth', "User")
    user_content_type = ContentType.objects.get_for_model(User)
    for role in Role.objects.filter(content_type=user_content_type).iterator():
        role.delete()


def migrate_jt_organization(apps, schema_editor):
    '''
    Move organization from project to job template
    '''
    JobTemplate = apps.get_model('main', 'JobTemplate')
    updated_ct = 0
    for jt in JobTemplate.objects.iterator():
        if not jt.project:
            continue
        project = jt.project
        if not project.organization:
            continue
        jt.organization = project.organization
        jt.save(update_fields=['organization'])
        updated_ct += 1
    logger.info('Migrated project to JT field for {} JTs'.format(updated_ct))
    return


def rebuild_role_hierarchy(apps, schema_editor):
    '''
    This should be called in any migration when ownerships are changed.
    Ex. I remove a user from the admin_role of a credential.
    Ancestors are cached from parents for performance, this re-computes ancestors.
    '''
    logger.info('Computing role roots..')
    start = time()
    roots = Role.objects \
                .all() \
                .values_list('id', flat=True)
    stop = time()
    logger.info('Found %d roots in %f seconds, rebuilding ancestry map' % (len(roots), stop - start))
    start = time()
    Role.rebuild_role_ancestor_list(roots, [])
    stop = time()
    logger.info('Rebuild completed in %f seconds' % (stop - start))
    logger.info('Done.')


def rebuild_role_parentage(apps, schema_editor):
    '''
    This should be called in any migration when any parent_role entry
    is modified so that the cached parent fields will be updated. Ex:
        foo_role = ImplicitRoleField(
            parent_role=['bar_role']  # change to parent_role=['admin_role']
        )

    This is like rebuild_role_hierarchy, but that method updates ancestors,
    whereas this method updates parents.
    '''
    seen_models = set()
    updated_ct = 0
    model_ct = 0
    Role = apps.get_model('main', "Role")
    for role in Role.objects.iterator():
        if not role.object_id:
            logger.debug('Skipping singleton or orphaned role {}'.format(role.pk))
            continue
        model_tuple = (role.content_type_id, role.object_id)
        if model_tuple in seen_models:
            continue
        seen_models.add(model_tuple)

        # The GenericForeignKey does not work right in migrations
        # with the usage as role.content_object
        # so we do the lookup ourselves with current migration models
        ct = role.content_type
        app = ct.app_label
        ct_model = apps.get_model(app, ct.model)
        content_object = ct_model.objects.get(pk=role.object_id)

        updated = update_role_parentage_for_instance(content_object)
        if updated:
            model_ct += 1
            logger.debug('Updated parents of {} roles of {}'.format(updated, content_object))
        else:
            logger.debug('No changes to role parents of {}'.format(content_object))
        updated_ct += updated

    if updated_ct:
        logger.info('Updated parentage for {} roles of {} resources'.format(updated_ct, model_ct))
        rebuild_role_hierarchy(apps, schema_editor)
