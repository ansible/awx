import logging
from time import time

from django.db.models import F
from django.db.models import Subquery, OuterRef

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


def _migrate_unified_organization_iterator(apps, unified_cls_name, org_field_mapping):
    """Slow method to do operation
    """
    UnifiedClass = apps.get_model('main', unified_cls_name)
    ContentType = apps.get_model('contenttypes', 'ContentType')
    changed_ct = 0
    unified_ct_mapping = {}
    for cls_name in org_field_mapping:
        unified_ct_mapping[ContentType.objects.get(model=cls_name).id] = cls_name

    for cls_name, source_field in org_field_mapping.items():
        print_field = []
        if source_field:
            print_field.append(source_field)
        print_field.append('organization')
        logger.debug('Migrating {} from {} to new organization field'.format(cls_name, '__'.join(source_field)))

        rel_model = apps.get_model('main', cls_name)
        if source_field is None:
            field = rel_model._meta.get_field('organization')
            reverse_rel = field.remote_field.name
            sub_qs = rel_model.objects.filter(**{'{}_id'.format(reverse_rel): OuterRef('id')})
        else:
            field = rel_model._meta.get_field(source_field)
            rel_model = field.related_model
            reverse_rel = field.remote_field.name
            sub_qs = rel_model.objects.filter(**{'{}_id'.format(reverse_rel): OuterRef('organization_id')})

        r = UnifiedClass.objects.update(tmp_organization=Subquery(sub_qs))
        logger.info('result')
        logger.info(str(r))

    logger.info('Migrated organization field for {} {}s'.format(changed_ct, unified_cls_name))


def _migrate_unified_organization(apps, unified_cls_name, org_field_mapping):
    """Given a unified base model (either UJT or UJ)
    and a dict org_field_mapping which gives related model to get org from
    saves organization for those objects to the temporary migration
    variable tmp_organization on the unified model
    (optimized method)
    """
    UnifiedClass = apps.get_model('main', unified_cls_name)
    ContentType = apps.get_model('contenttypes', 'ContentType')
    changed_ct = 0
    unified_ct_mapping = {}
    for cls_name in org_field_mapping:
        unified_ct_mapping[ContentType.objects.get(model=cls_name).id] = cls_name

    for cls_name, source_field in org_field_mapping.items():
        print_field = []
        if source_field:
            print_field.append(source_field)
        print_field.append('organization')
        logger.debug('Migrating {} from {} to new organization field'.format(cls_name, '__'.join(print_field)))

        rel_model = apps.get_model('main', cls_name)
        if source_field is None:
            field = rel_model._meta.get_field('organization')
            reverse_rel = field.remote_field.name
            sub_qs = rel_model.objects.filter(**{'{}_id'.format(reverse_rel): OuterRef('id')})
        else:
            field = rel_model._meta.get_field(source_field)
            rel_model = field.related_model
            logger.info(rel_model)
            reverse_rel = field.remote_field.name
            sub_qs = rel_model.objects.filter(**{'{}'.format(reverse_rel): OuterRef('organization_id')})

        r = UnifiedClass.objects.update(tmp_organization=Subquery(sub_qs))
        logger.info('result')
        logger.info(str(r))


def migrate_ujt_organization(apps, schema_editor):
    '''
    Move organization from project to job template
    '''
    org_lookups = {
        # Job Templates had an implicit organization via their project
        'jobtemplate': 'project',
        # Inventory Sources had an implicit organization via their inventory
        'inventorysource': 'inventory',
        # Projects had an explicit organization in their subclass table
        'project': None,
        # Workflow JTs also had an explicit organization in their subclass table
        'workflowjobtemplate': None
    }
    _migrate_unified_organization(apps, 'UnifiedJobTemplate', org_lookups)

    job_org_lookups = {
        # Jobs inherited project from job templates as a convience field
        'job': 'project',
        # Inventory Sources had an convience field of inventory
        'inventoryupdate': 'inventory',
        # Project Updates did not have a direct organization field, obtained it from project
        'projectupdate': 'project',
        # Workflow Jobs are handled same as project updates
        # Sliced jobs are a special case, but old data is not given special treatment for simplicity
        'workflowjob': 'workflow_job_template',
        # AdHocCommands do not have a template, but still migrate them
        'adhoccommand': 'inventory'
    }
    _migrate_unified_organization(apps, 'UnifiedJob', job_org_lookups)


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
