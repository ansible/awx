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


def migrate_ujt_organization(apps, schema_editor):
    '''
    Move organization from project to job template
    '''
    updated_ujt = 0
    UnifiedJobTemplate = apps.get_model('main', 'UnifiedJobTemplate')
    MIGRATE_TEMPLATE_FIELD = (
        # Job Templates had an implicit organization via their project
        ('jobtemplate', 'project'),
        # Inventory Sources had an implicit organization via their inventory
        ('inventorysource', 'inventory'),
        # Projects had an explicit organization in their subclass table
        ('project', None),
        # Workflow JTs also had an explicit organization in their subclass table
        ('workflowjobtemplate', None),
    )
    for ujt in UnifiedJobTemplate.objects.iterator():
        logger.info(ujt.__dict__)
        logger.info(ujt._meta.__dict__)
        model_name = ujt._meta.model_name
        for cls_name, source_field in MIGRATE_TEMPLATE_FIELD:
            rel_obj = getattr(ujt, cls_name)
            if rel_obj is None:
                logger.debug('no sub type {}-{}'.format(cls_name, ujt.pk))
                continue
            logger.debug('rel obj')
            print(rel_obj.__dict__)
            if source_field is not None:
                logger.debug('No {} for {}-{}'.format(source_field, cls_name, ujt.pk))
                rel_obj = getattr(ujt, source_field)
            if rel_obj is None or rel_obj.organization_id is None:
                logger.debug('No organization for {}-{}'.format(cls_name, ujt.pk))
                break
            ujt.organization_id = rel_obj.organization_id
            ujt.save(update_fields=['organization_id'])
            updated_ujt += 1
            logger.debug('Migrated {}-{} organization field for {}'.format(
                cls_name, ujt.pk, ujt.organization_id
            ))
            break
        else:
            # no migration needed for system jobs
            if model_name != 'systemjobtemplate':
                logger.info(ujt.__dict__)
                logger.info('model name {}-{}'.format(model_name, ujt.pk))
                raise Exception('unexpected type')
    logger.info('Migrated organization field for {} UJTs'.format(updated_ujt))
    # MIGRATE_TEMPLATE_FIELD = (
    #     # Job Templates had an implicit organization via their project
    #     ('JobTemplate', 'projects__jobtemplates'),
    #     # Inventory Sources had an implicit organization via their inventory
    #     ('InventorySource', 'inventories__inventory_sources'),
    #     # Projects had an explicit organization in their subclass table
    #     ('Project', 'projects'),
    #     # Workflow JTs also had an explicit organization in their subclass table
    #     ('WorkflowJobTemplate', 'workflows'),
    # )
    # # Both the implicit organizations and the explicit organizations are moved
    # # all the way up to the base model, UnifiedJobTemplate first
    # UnifiedJobTemplate = apps.get_model('main', 'UnifiedJobTemplate')
    # # for cls_name, source_field in MIGRATE_TEMPLATE_FIELD:
    # for cls_name, reverse_ref in MIGRATE_TEMPLATE_FIELD:
    #     cls = apps.get_model('main', cls_name)
    #     name = cls._meta.model_name
    #     logger.debug('Migrating {} from {} to new organization field'.format(cls_name, reverse_ref))
    #     # sub_qs = cls.objects.filter(
    #     #     id=OuterRef(name)
    #     # ).values('{}_id'.format(source_field))[:1]
    #     sub_qs = Organization.objects.filter(
    #         **{reverse_ref: OuterRef(name)}
    #     ).values('id')
    #     # sub_qs = Project.objects.filter(
    #     #     jobtemplates=OuterRef(name)
    #     # ).values('organization_id')[:1]
    #     r = UnifiedJobTemplate.objects.filter(**{'{}__isnull'.format(name): False}).update(
    #         tmp_organization=Subquery(sub_qs)
    #     )
    #     logger.info('result')
    #     logger.info(str(r))
    # # Job Templates had an implicit organization via their project
    # InventorySource = apps.get_model('main', 'InventorySource')
    # r = UnifiedJobTemplate.objects.filter(inventorysource__isnull=False).update(organization=F('jobtemplate.project.organization'))
    # logger.info(str(r))
    # # Job Templates had an implicit organization via their project
    # Project = apps.get_model('main', 'Project')
    # r = UnifiedJobTemplate.objects.filter(project__isnull=False).update(organization=F('jobtemplate.project.organization'))
    # logger.info(str(r))
    # # Job Templates had an implicit organization via their project
    # WorkflowJobTemplate = apps.get_model('main', 'WorkflowJobTemplate')
    # r = UnifiedJobTemplate.objects.filter(workflowjobtemplate__isnull=False).update(organization=F('jobtemplate.project.organization'))
    # logger.info(str(r))

    MIGRATE_JOB_FIELD = (
        # Jobs inherited project from job templates as a convience field
        ('Job', 'project'),
        # Inventory Sources had an convience field of inventory
        ('InventoryUpdate', 'inventory'),
        # Project Updates did not have a direct organization field, obtained it from project
        ('ProjectUpdate', 'project'),
        # Workflow Jobs are handled same as project updates
        # Sliced jobs are a special case, but old data is not given special treatment for simplicity
        ('WorkflowJob', 'workflow_job_template'),
    )
    # UnifiedJob organization field migrated here
    UnifiedJob = apps.get_model('main', 'UnifiedJob')
    updated_uj = 0
    for uj in UnifiedJob.objects.iterator():
        model_name = uj._meta.model_name
        for cls_name, source_field in MIGRATE_JOB_FIELD:
            if model_name == cls_name:
                rel_obj = uj
                if source_field is not None:
                    rel_obj = getattr(uj, source_field)
                if rel_obj is None or rel_obj.organization_id is None:
                    logger.debug('No organization for {}-{}'.format(model_name, uj.pk))
                    break
                uj.organization_id = rel_obj.organization_id
                uj.save(update_fields=['organization_id'])
                updated_uj += 1
                logger.debug('Migrated {}-{} organization field for {}'.format(
                    model_name, uj.pk, uj.organization_id
                ))
                break
        else:
            # no migration needed for system jobs
            if model_name != 'systemjob':
                raise Exception('unexpected type')
    logger.info('Migrated organization field for {} UJs'.format(updated_uj))

    # for cls_name, source_field in MIGRATE_JOB_FIELD:
    #     cls = apps.get_model('main', cls_name)
    #     name = cls._meta.model_name
    #     logger.debug('Migrating {} from {} to new organization field'.format(cls_name, source_field))
    #     sub_qs = cls.objects.filter(
    #         id=OuterRef('{}_id'.format(name))
    #     ).values(source_field)[:1]
    #     r = UnifiedJob.objects.filter(**{'{}__isnull'.format(name): False}).update(
    #         tmp_organization=Subquery(sub_qs)
    #     )
    #     logger.info('result')
    #     logger.info(str(r))

    # updated_ct = 0
    # for jt in JobTemplate.objects.iterator():
    #     if not jt.project:
    #         continue
    #     project = jt.project
    #     if not project.organization:
    #         continue
    #     jt.organization = project.organization
    #     jt.save(update_fields=['organization'])
    #     updated_ct += 1
    # logger.info('Migrated project to JT field for {} JTs'.format(updated_ct))
    # return


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
