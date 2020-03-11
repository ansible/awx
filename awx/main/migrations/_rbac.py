import logging
from time import time

from django.db.models import Subquery, OuterRef, F

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
        logger.debug('{}Migrating {} to new organization field'.format('Reverse ' if backward else '', cls_name))

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
    logger.info('Unified organization migration completed in {:.4f} seconds'.format(time() - start))


def migrate_ujt_organization(apps, schema_editor):
    '''Move organization field to UJT and UJ models'''
    _migrate_unified_organization(apps, 'UnifiedJobTemplate')
    _migrate_unified_organization(apps, 'UnifiedJob')


def migrate_ujt_organization_backward(apps, schema_editor):
    '''Move organization field from UJT and UJ models back to their original places'''
    _migrate_unified_organization(apps, 'UnifiedJobTemplate', backward=True)
    _migrate_unified_organization(apps, 'UnifiedJob', backward=True)


def _restore_inventory_admins(apps, schema_editor, backward=False):
    """With the JT.organization changes, admins of organizations connected to
    job templates via inventory will have their permissions demoted.
    This maintains current permissions over the migration by granting the
    permissions they used to have explicitly on the JT itself.
    """
    start = time()
    JobTemplate = apps.get_model('main', 'JobTemplate')
    User = apps.get_model('auth', 'User')
    changed_ct = 0
    jt_qs = JobTemplate.objects.filter(inventory__isnull=False)
    jt_qs = jt_qs.exclude(inventory__organization=F('project__organization'))
    jt_qs = jt_qs.only('id', 'admin_role_id', 'execute_role_id', 'inventory_id')
    for jt in jt_qs.iterator():
        org = jt.inventory.organization
        for jt_role, org_roles in (
                ('admin_role', ('admin_role', 'job_template_admin_role',)),
                ('execute_role', ('execute_role',))
            ):
            role_id = getattr(jt, '{}_id'.format(jt_role))

            user_qs = User.objects
            if not backward:
                # In this specific case, the name for the org role and JT roles were the same
                org_role_ids = [getattr(org, '{}_id'.format(role_name)) for role_name in org_roles]
                user_qs = user_qs.filter(roles__in=org_role_ids)
                # bizarre migration behavior - ancestors / descendents of
                # migration version of Role model is reversed, using current model briefly
                ancestor_ids = list(
                    Role.objects.filter(descendents=role_id).values_list('id', flat=True)
                )
                # same as Role.__contains__, filter for "user in jt.admin_role"
                user_qs = user_qs.exclude(roles__in=ancestor_ids)
            else:
                # use the database to filter intersection of users without access
                # to the JT role and either organization role
                user_qs = user_qs.filter(roles__in=[org.admin_role_id, org.execute_role_id])
                # in reverse, intersection of users who have both
                user_qs = user_qs.filter(roles=role_id)

            user_ids = list(user_qs.values_list('id', flat=True))
            if not user_ids:
                continue

            role = getattr(jt, jt_role)
            logger.debug('{} {} on jt {} for users {} via inventory.organization {}'.format(
                'Removing' if backward else 'Setting',
                jt_role, jt.pk, user_ids, org.pk
            ))
            if not backward:
                # in reverse, explit role becomes redundant
                role.members.add(*user_ids)
            else:
                role.members.remove(*user_ids)
            changed_ct += len(user_ids)

    if changed_ct:
        logger.info('{} explicit JT permission for {} users in {:.4f} seconds'.format(
            'Removed' if backward else 'Added',
            changed_ct, time() - start
        ))


def restore_inventory_admins(apps, schema_editor):
    _restore_inventory_admins(apps, schema_editor)


def restore_inventory_admins_backward(apps, schema_editor):
    _restore_inventory_admins(apps, schema_editor, backward=True)


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


def rebuild_role_parentage(apps, schema_editor, models=None):
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
    model_ct = 0
    noop_ct = 0
    ContentType = apps.get_model('contenttypes', "ContentType")
    additions = set()
    removals = set()

    role_qs = Role.objects
    if models:
        # update_role_parentage_for_instance is expensive
        # if the models have been downselected, ignore those which are not in the list
        ct_ids = list(ContentType.objects.filter(
            model__in=[name.lower() for name in models]
        ).values_list('id', flat=True))
        role_qs = role_qs.filter(content_type__in=ct_ids)

    for role in role_qs.iterator():
        if not role.object_id:
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

        parents_added, parents_removed = update_role_parentage_for_instance(content_object)
        additions.update(parents_added)
        removals.update(parents_removed)
        if parents_added:
            model_ct += 1
            logger.debug('Added to parents of roles {} of {}'.format(parents_added, content_object))
        if parents_removed:
            model_ct += 1
            logger.debug('Removed from parents of roles {} of {}'.format(parents_removed, content_object))
        else:
            noop_ct += 1

    logger.debug('No changes to role parents for {} resources'.format(noop_ct))
    logger.debug('Added parents to {} roles'.format(len(additions)))
    logger.debug('Removed parents from {} roles'.format(len(removals)))
    if model_ct:
        logger.info('Updated implicit parents of {} resources'.format(model_ct))

    logger.info('Rebuild parentage completed in %f seconds' % (time() - start))

    # this is ran because the ordinary signals for
    # Role.parents.add and Role.parents.remove not called in migration
    Role.rebuild_role_ancestor_list(list(additions), list(removals))
