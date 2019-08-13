import logging
from time import time

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


UNIFIED_ORG_LOOKUPS = {
    # Job Templates had an implicit organization via their project
    'jobtemplate': 'project',
    # Inventory Sources had an implicit organization via their inventory
    'inventorysource': 'inventory',
    # Projects had an explicit organization in their subclass table
    'project': None,
    # Workflow JTs also had an explicit organization in their subclass table
    'workflowjobtemplate': None,
    # Jobs inherited project from job templates as a convenience field
    'job': 'project',
    # Inventory Sources had an convenience field of inventory
    'inventoryupdate': 'inventory',
    # Project Updates did not have a direct organization field, obtained it from project
    'projectupdate': 'project',
    # Workflow Jobs are handled same as project updates
    # Sliced jobs are a special case, but old data is not given special treatment for simplicity
    'workflowjob': 'workflow_job_template',
    # AdHocCommands do not have a template, but still migrate them
    'adhoccommand': 'inventory'
}


def implicit_org_subquery(UnifiedClass, cls, backward=False):
    """Returns a subquery that returns the so-called organization for objects
    in the class in question, before migration to the explicit unified org field.
    In some cases, this can still be applied post-migration.
    """
    if cls._meta.model_name not in UNIFIED_ORG_LOOKUPS:
        return None
    cls_name = cls._meta.model_name
    source_field = UNIFIED_ORG_LOOKUPS[cls_name]

    unified_field = UnifiedClass._meta.get_field(cls_name)
    unified_ptr = unified_field.remote_field.name
    if backward:
        qs = UnifiedClass.objects.filter(**{cls_name: OuterRef('id')}).order_by().values_list('tmp_organization')[:1]
    elif source_field is None:
        qs = cls.objects.filter(**{unified_ptr: OuterRef('id')}).order_by().values_list('organization')[:1]
    else:
        intermediary_field = cls._meta.get_field(source_field)
        intermediary_model = intermediary_field.related_model
        intermediary_reverse_rel = intermediary_field.remote_field.name
        qs = intermediary_model.objects.filter(**{
            # this filter leverages the fact that the Unified models have same pk as subclasses.
            # For instance... filters projects used in job template, where that job template
            # has same id same as UJT from the outer reference (which it does)
            intermediary_reverse_rel: OuterRef('id')}
        ).order_by().values_list('organization')[:1]
    return Subquery(qs)


def _migrate_unified_organization(apps, unified_cls_name, backward=False):
    """Given a unified base model (either UJT or UJ)
    and a dict org_field_mapping which gives related model to get org from
    saves organization for those objects to the temporary migration
    variable tmp_organization on the unified model
    (optimized method)
    """
    start = time()
    UnifiedClass = apps.get_model('main', unified_cls_name)
    ContentType = apps.get_model('contenttypes', 'ContentType')

    for cls in UnifiedClass.__subclasses__():
        cls_name = cls._meta.model_name
        if backward and UNIFIED_ORG_LOOKUPS.get(cls_name, 'not-found') is not None:
            logger.debug('Not reverse migrating {}, existing data should remain valid'.format(cls_name))
            continue
        logger.debug('Migrating {} to new organization field'.format(cls_name))

        sub_qs = implicit_org_subquery(UnifiedClass, cls, backward=backward)
        if sub_qs is None:
            logger.debug('Class {} has no organization migration'.format(cls_name))
            continue

        this_ct = ContentType.objects.get_for_model(cls)
        if backward:
            r = cls.objects.order_by().update(organization=sub_qs)
        else:
            r = UnifiedClass.objects.order_by().filter(polymorphic_ctype=this_ct).update(tmp_organization=sub_qs)
        if r:
            logger.info('Organization migration on {} affected {} rows.'.format(cls_name, r))
    logger.info('Unified organization migration completed in %f seconds' % (time() - start))


def migrate_ujt_organization(apps, schema_editor):
    '''Move organization field to UJT and UJ models'''
    _migrate_unified_organization(apps, 'UnifiedJobTemplate')
    _migrate_unified_organization(apps, 'UnifiedJob')


def migrate_ujt_organization_backward(apps, schema_editor):
    '''Move organization field from UJT and UJ models back to their original places'''
    _migrate_unified_organization(apps, 'UnifiedJobTemplate', backward=True)
    _migrate_unified_organization(apps, 'UnifiedJob', backward=True)


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
    logger.info('Rebuild ancestors completed in %f seconds' % (stop - start))
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
    start = time()
    seen_models = set()
    updated_ct = 0
    model_ct = 0
    noop_ct = 0
    Role = apps.get_model('main', "Role")
    for role in Role.objects.iterator():
        if not role.object_id:
            noop_ct += 1
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
            noop_ct += 1
        updated_ct += updated

    logger.debug('No changes to role parents for {} roles'.format(noop_ct))
    if updated_ct:
        logger.info('Updated parentage for {} roles of {} resources'.format(updated_ct, model_ct))

    logger.info('Rebuild parentage completed in %f seconds' % (time() - start))

    if updated_ct:
        rebuild_role_hierarchy(apps, schema_editor)
