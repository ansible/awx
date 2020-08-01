# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import contextlib
import logging
import threading
import json
import sys

# Django
from django.db import connection
from django.conf import settings
from django.db.models.signals import (
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    m2m_changed,
)
from django.dispatch import receiver
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.utils import timezone

# Django-CRUM
from crum import get_current_request, get_current_user
from crum.signals import current_user_getter


# AWX
from awx.main.models import (
    ActivityStream, Group, Host, InstanceGroup, Inventory, InventorySource,
    Job, JobHostSummary, JobTemplate, OAuth2AccessToken, Organization, Project,
    Role, SystemJob, SystemJobTemplate, UnifiedJob, UnifiedJobTemplate, User,
    UserSessionMembership, WorkflowJobTemplateNode, WorkflowApproval,
    WorkflowApprovalTemplate, ROLE_SINGLETON_SYSTEM_ADMINISTRATOR
)
from awx.main.constants import CENSOR_VALUE
from awx.main.utils import model_instance_diff, model_to_dict, camelcase_to_underscore, get_current_apps
from awx.main.utils import ignore_inventory_computed_fields, ignore_inventory_group_removal, _inventory_updates
from awx.main.tasks import update_inventory_computed_fields
from awx.main.fields import (
    is_implicit_parent,
    update_role_parentage_for_instance,
)

from awx.main import consumers

from awx.conf.utils import conf_to_dict

__all__ = []

logger = logging.getLogger('awx.main.signals')
analytics_logger = logging.getLogger('awx.analytics.activity_stream')

# Update has_active_failures for inventory/groups when a Host/Group is deleted,
# when a Host-Group or Group-Group relationship is updated, or when a Job is deleted


def get_activity_stream_class():
    if 'migrate' in sys.argv:
        return get_current_apps().get_model('main', 'ActivityStream')
    else:
        return ActivityStream


def get_current_user_or_none():
    u = get_current_user()
    if not isinstance(u, User):
        return None
    return u


def emit_update_inventory_on_created_or_deleted(sender, **kwargs):
    if getattr(_inventory_updates, 'is_updating', False):
        return
    instance = kwargs['instance']
    if ('created' in kwargs and kwargs['created']) or \
       kwargs['signal'] == post_delete:
        pass
    else:
        return
    sender_name = str(sender._meta.verbose_name)
    logger.debug("%s created or deleted, updating inventory computed fields: %r %r",
                 sender_name, sender, kwargs)
    try:
        inventory = instance.inventory
    except Inventory.DoesNotExist:
        pass
    else:
        if inventory is not None:
            connection.on_commit(
                lambda: update_inventory_computed_fields.delay(inventory.id)
            )


def rebuild_role_ancestor_list(reverse, model, instance, pk_set, action, **kwargs):
    'When a role parent is added or removed, update our role hierarchy list'
    if action == 'post_add':
        if reverse:
            model.rebuild_role_ancestor_list(list(pk_set), [])
        else:
            model.rebuild_role_ancestor_list([instance.id], [])

    if action in ['post_remove', 'post_clear']:
        if reverse:
            model.rebuild_role_ancestor_list([], list(pk_set))
        else:
            model.rebuild_role_ancestor_list([], [instance.id])


def sync_superuser_status_to_rbac(instance, **kwargs):
    'When the is_superuser flag is changed on a user, reflect that in the membership of the System Admnistrator role'
    update_fields = kwargs.get('update_fields', None)
    if update_fields and 'is_superuser' not in update_fields:
        return
    if instance.is_superuser:
        Role.singleton(ROLE_SINGLETON_SYSTEM_ADMINISTRATOR).members.add(instance)
    else:
        Role.singleton(ROLE_SINGLETON_SYSTEM_ADMINISTRATOR).members.remove(instance)


def rbac_activity_stream(instance, sender, **kwargs):
    # Only if we are associating/disassociating
    if kwargs['action'] in ['pre_add', 'pre_remove']:
        if hasattr(instance, 'content_type'):  # Duck typing, migration-independent isinstance(instance, Role)
            if instance.content_type_id is None and instance.singleton_name == ROLE_SINGLETON_SYSTEM_ADMINISTRATOR:
                # Skip entries for the system admin role because user serializer covers it
                # System auditor role is shown in the serializer, but its relationship is
                # managed separately, its value is incorrect, and a correction entry is needed
                return
            # This juggles which role to use, because could be A->B or B->A association
            if sender.__name__ == 'Role_parents':
                role = kwargs['model'].objects.filter(pk__in=kwargs['pk_set']).first()
                # don't record implicit creation / parents in activity stream
                if role is not None and is_implicit_parent(parent_role=role, child_role=instance):
                    return
            else:
                role = instance
            # If a singleton role is the instance, the singleton role is acted on
            # otherwise the related object is considered to be acted on
            if instance.content_object:
                instance = instance.content_object
        else:
            # Association with actor, like role->user
            role = kwargs['model'].objects.filter(pk__in=kwargs['pk_set']).first()

        activity_stream_associate(sender, instance, role=role, **kwargs)


def cleanup_detached_labels_on_deleted_parent(sender, instance, **kwargs):
    for label in instance.labels.all():
        if label.is_candidate_for_detach():
            label.delete()


def save_related_job_templates(sender, instance, **kwargs):
    '''save_related_job_templates loops through all of the
    job templates that use an Inventory that have had their
    Organization updated. This triggers the rebuilding of the RBAC hierarchy
    and ensures the proper access restrictions.
    '''
    if sender is not Inventory:
        raise ValueError('This signal callback is only intended for use with Project or Inventory')

    update_fields = kwargs.get('update_fields', None)
    if ((update_fields and not ('organization' in update_fields or 'organization_id' in update_fields)) or
            kwargs.get('created', False)):
        return

    if instance._prior_values_store.get('organization_id') != instance.organization_id:
        jtq = JobTemplate.objects.filter(**{sender.__name__.lower(): instance})
        for jt in jtq:
            parents_added, parents_removed = update_role_parentage_for_instance(jt)
            if parents_added or parents_removed:
                logger.info('Permissions on JT {} changed due to inventory {} organization change from {} to {}.'.format(
                    jt.pk, instance.pk, instance._prior_values_store.get('organization_id'), instance.organization_id
                ))


def connect_computed_field_signals():
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Group)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Group)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Job)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Job)


connect_computed_field_signals()

post_save.connect(save_related_job_templates, sender=Inventory)
m2m_changed.connect(rebuild_role_ancestor_list, Role.parents.through)
m2m_changed.connect(rbac_activity_stream, Role.members.through)
m2m_changed.connect(rbac_activity_stream, Role.parents.through)
post_save.connect(sync_superuser_status_to_rbac, sender=User)
pre_delete.connect(cleanup_detached_labels_on_deleted_parent, sender=UnifiedJob)
pre_delete.connect(cleanup_detached_labels_on_deleted_parent, sender=UnifiedJobTemplate)

# Migrate hosts, groups to parent group(s) whenever a group is deleted


@receiver(pre_delete, sender=Group)
def save_related_pks_before_group_delete(sender, **kwargs):
    if getattr(_inventory_updates, 'is_removing', False):
        return
    instance = kwargs['instance']
    instance._saved_inventory_pk = instance.inventory.pk
    instance._saved_parents_pks = set(instance.parents.values_list('pk', flat=True))
    instance._saved_hosts_pks = set(instance.hosts.values_list('pk', flat=True))
    instance._saved_children_pks = set(instance.children.values_list('pk', flat=True))


@receiver(post_delete, sender=Group)
def migrate_children_from_deleted_group_to_parent_groups(sender, **kwargs):
    if getattr(_inventory_updates, 'is_removing', False):
        return
    instance = kwargs['instance']
    parents_pks = getattr(instance, '_saved_parents_pks', [])
    hosts_pks = getattr(instance, '_saved_hosts_pks', [])
    children_pks = getattr(instance, '_saved_children_pks', [])
    is_updating  = getattr(_inventory_updates, 'is_updating', False)

    with ignore_inventory_group_removal():
        with ignore_inventory_computed_fields():
            if parents_pks:
                for parent_group in Group.objects.filter(pk__in=parents_pks):
                    for child_host in Host.objects.filter(pk__in=hosts_pks):
                        logger.debug('adding host %s to parent %s after group deletion',
                                     child_host, parent_group)
                        parent_group.hosts.add(child_host)
                    for child_group in Group.objects.filter(pk__in=children_pks):
                        logger.debug('adding group %s to parent %s after group deletion',
                                     child_group, parent_group)
                        parent_group.children.add(child_group)
                inventory_pk = getattr(instance, '_saved_inventory_pk', None)
                if inventory_pk and not is_updating:
                    try:
                        inventory = Inventory.objects.get(pk=inventory_pk)
                        inventory.update_computed_fields()
                    except (Inventory.DoesNotExist, Project.DoesNotExist):
                        pass


# Update host pointers to last_job and last_job_host_summary when a job is deleted


def _update_host_last_jhs(host):
    jhs_qs = JobHostSummary.objects.filter(host__pk=host.pk)
    try:
        jhs = jhs_qs.order_by('-job__pk')[0]
    except IndexError:
        jhs = None
    update_fields = []
    try:
        last_job = jhs.job if jhs else None
    except Job.DoesNotExist:
        # The job (and its summaries) have already been/are currently being
        # deleted, so there's no need to update the host w/ a reference to it
        return
    if host.last_job != last_job:
        host.last_job = last_job
        update_fields.append('last_job')
    if host.last_job_host_summary != jhs:
        host.last_job_host_summary = jhs
        update_fields.append('last_job_host_summary')
    if update_fields:
        host.save(update_fields=update_fields)


@receiver(pre_delete, sender=Job)
def save_host_pks_before_job_delete(sender, **kwargs):
    instance = kwargs['instance']
    hosts_qs = Host.objects.filter( last_job__pk=instance.pk)
    instance._saved_hosts_pks = set(hosts_qs.values_list('pk', flat=True))


@receiver(post_delete, sender=Job)
def update_host_last_job_after_job_deleted(sender, **kwargs):
    instance = kwargs['instance']
    hosts_pks = getattr(instance, '_saved_hosts_pks', [])
    for host in Host.objects.filter(pk__in=hosts_pks):
        _update_host_last_jhs(host)


# Set via ActivityStreamRegistrar to record activity stream events


class ActivityStreamEnabled(threading.local):
    def __init__(self):
        self.enabled = True

    def __bool__(self):
        return bool(self.enabled and getattr(settings, 'ACTIVITY_STREAM_ENABLED', True))


activity_stream_enabled = ActivityStreamEnabled()


@contextlib.contextmanager
def disable_activity_stream():
    '''
    Context manager to disable capturing activity stream changes.
    '''
    try:
        previous_value = activity_stream_enabled.enabled
        activity_stream_enabled.enabled = False
        yield
    finally:
        activity_stream_enabled.enabled = previous_value


@contextlib.contextmanager
def disable_computed_fields():
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=Group)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=Group)
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=Job)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=Job)
    yield
    connect_computed_field_signals()


def model_serializer_mapping():
    from awx.api import serializers
    from awx.main import models

    from awx.conf.models import Setting
    from awx.conf.serializers import SettingSerializer
    return {
        Setting: SettingSerializer,
        models.User: serializers.UserActivityStreamSerializer,
        models.Organization: serializers.OrganizationSerializer,
        models.Inventory: serializers.InventorySerializer,
        models.Host: serializers.HostSerializer,
        models.Group: serializers.GroupSerializer,
        models.InstanceGroup: serializers.InstanceGroupSerializer,
        models.InventorySource: serializers.InventorySourceSerializer,
        models.CustomInventoryScript: serializers.CustomInventoryScriptSerializer,
        models.Credential: serializers.CredentialSerializer,
        models.Team: serializers.TeamSerializer,
        models.Project: serializers.ProjectSerializer,
        models.JobTemplate: serializers.JobTemplateWithSpecSerializer,
        models.Job: serializers.JobSerializer,
        models.AdHocCommand: serializers.AdHocCommandSerializer,
        models.NotificationTemplate: serializers.NotificationTemplateSerializer,
        models.Notification: serializers.NotificationSerializer,
        models.CredentialType: serializers.CredentialTypeSerializer,
        models.Schedule: serializers.ScheduleSerializer,
        models.Label: serializers.LabelSerializer,
        models.WorkflowJobTemplate: serializers.WorkflowJobTemplateWithSpecSerializer,
        models.WorkflowJobTemplateNode: serializers.WorkflowJobTemplateNodeSerializer,
        models.WorkflowApproval: serializers.WorkflowApprovalActivityStreamSerializer,
        models.WorkflowApprovalTemplate: serializers.WorkflowApprovalTemplateSerializer,
        models.WorkflowJob: serializers.WorkflowJobSerializer,
        models.OAuth2AccessToken: serializers.OAuth2TokenSerializer,
        models.OAuth2Application: serializers.OAuth2ApplicationSerializer,
    }


def emit_activity_stream_change(instance):
    if 'migrate' in sys.argv:
        # don't emit activity stream external logs during migrations, it
        # could be really noisy
        return
    from awx.api.serializers import ActivityStreamSerializer
    actor = None
    if instance.actor:
        actor = instance.actor.username
    summary_fields = ActivityStreamSerializer(instance).get_summary_fields(instance)
    analytics_logger.info('Activity Stream update entry for %s' % str(instance.object1),
                          extra=dict(changes=instance.changes, relationship=instance.object_relationship_type,
                          actor=actor, operation=instance.operation,
                          object1=instance.object1, object2=instance.object2, summary_fields=summary_fields))


def activity_stream_create(sender, instance, created, **kwargs):
    if created and activity_stream_enabled:
        _type = type(instance)
        if getattr(_type, '_deferred', False):
            return
        object1 = camelcase_to_underscore(instance.__class__.__name__)
        changes = model_to_dict(instance, model_serializer_mapping())
        # Special case where Job survey password variables need to be hidden
        if type(instance) == Job:
            changes['credentials'] = [
                '{} ({})'.format(c.name, c.id)
                for c in instance.credentials.iterator()
            ]
            changes['labels'] = [label.name for label in instance.labels.iterator()]
            if 'extra_vars' in changes:
                changes['extra_vars'] = instance.display_extra_vars()
        if type(instance) == OAuth2AccessToken:
            changes['token'] = CENSOR_VALUE
        activity_entry = get_activity_stream_class()(
            operation='create',
            object1=object1,
            changes=json.dumps(changes),
            actor=get_current_user_or_none())
        #TODO: Weird situation where cascade SETNULL doesn't work
        #      it might actually be a good idea to remove all of these FK references since
        #      we don't really use them anyway.
        if instance._meta.model_name != 'setting':  # Is not conf.Setting instance
            activity_entry.save()
            getattr(activity_entry, object1).add(instance.pk)
        else:
            activity_entry.setting = conf_to_dict(instance)
            activity_entry.save()
        connection.on_commit(
            lambda: emit_activity_stream_change(activity_entry)
        )


def activity_stream_update(sender, instance, **kwargs):
    if instance.id is None:
        return
    if not activity_stream_enabled:
        return
    try:
        old = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        return

    new = instance
    changes = model_instance_diff(old, new, model_serializer_mapping())
    if changes is None:
        return
    _type = type(instance)
    if getattr(_type, '_deferred', False):
        return
    object1 = camelcase_to_underscore(instance.__class__.__name__)
    activity_entry = get_activity_stream_class()(
        operation='update',
        object1=object1,
        changes=json.dumps(changes),
        actor=get_current_user_or_none())
    if instance._meta.model_name != 'setting':  # Is not conf.Setting instance
        activity_entry.save()
        getattr(activity_entry, object1).add(instance.pk)
    else:
        activity_entry.setting = conf_to_dict(instance)
        activity_entry.save()
    connection.on_commit(
        lambda: emit_activity_stream_change(activity_entry)
    )


def activity_stream_delete(sender, instance, **kwargs):
    if not activity_stream_enabled:
        return
    # Inventory delete happens in the task system rather than request-response-cycle.
    # If we trigger this handler there we may fall into db-integrity-related race conditions.
    # So we add flag verification to prevent normal signal handling. This funciton will be
    # explicitly called with flag on in Inventory.schedule_deletion.
    changes = {}
    if isinstance(instance, Inventory):
        if not kwargs.get('inventory_delete_flag', False):
            return
        # Add additional data about child hosts / groups that will be deleted
        changes['coalesced_data'] = {
            'hosts_deleted': instance.hosts.count(),
            'groups_deleted': instance.groups.count()
        }
    elif isinstance(instance, (Host, Group)) and instance.inventory.pending_deletion:
        return  # accounted for by inventory entry, above
    _type = type(instance)
    if getattr(_type, '_deferred', False):
        return
    changes.update(model_to_dict(instance, model_serializer_mapping()))
    object1 = camelcase_to_underscore(instance.__class__.__name__)
    if type(instance) == OAuth2AccessToken:
        changes['token'] = CENSOR_VALUE
    activity_entry = get_activity_stream_class()(
        operation='delete',
        changes=json.dumps(changes),
        object1=object1,
        actor=get_current_user_or_none())
    activity_entry.save()
    connection.on_commit(
        lambda: emit_activity_stream_change(activity_entry)
    )


def activity_stream_associate(sender, instance, **kwargs):
    if not activity_stream_enabled:
        return
    if kwargs['action'] in ['pre_add', 'pre_remove']:
        if kwargs['action'] == 'pre_add':
            action = 'associate'
        elif kwargs['action'] == 'pre_remove':
            action = 'disassociate'
        else:
            return
        obj1 = instance
        _type = type(instance)
        if getattr(_type, '_deferred', False):
            return
        object1=camelcase_to_underscore(obj1.__class__.__name__)
        obj_rel = sender.__module__ + "." + sender.__name__

        for entity_acted in kwargs['pk_set']:
            obj2 = kwargs['model']
            obj2_id = entity_acted
            obj2_actual = obj2.objects.filter(id=obj2_id)
            if not obj2_actual.exists():
                continue
            obj2_actual = obj2_actual[0]
            _type = type(obj2_actual)
            if getattr(_type, '_deferred', False):
                return
            if isinstance(obj2_actual, Role) and obj2_actual.content_object is not None:
                obj2_actual = obj2_actual.content_object
                object2 = camelcase_to_underscore(obj2_actual.__class__.__name__)
            else:
                object2 = camelcase_to_underscore(obj2.__name__)
            # Skip recording any inventory source, or system job template changes here.
            if isinstance(obj1, InventorySource) or isinstance(obj2_actual, InventorySource):
                continue
            if isinstance(obj1, SystemJobTemplate) or isinstance(obj2_actual, SystemJobTemplate):
                continue
            if isinstance(obj1, SystemJob) or isinstance(obj2_actual, SystemJob):
                continue
            activity_entry = get_activity_stream_class()(
                changes=json.dumps(dict(object1=object1,
                                        object1_pk=obj1.pk,
                                        object2=object2,
                                        object2_pk=obj2_id,
                                        action=action,
                                        relationship=obj_rel)),
                operation=action,
                object1=object1,
                object2=object2,
                object_relationship_type=obj_rel,
                actor=get_current_user_or_none())
            activity_entry.save()
            getattr(activity_entry, object1).add(obj1.pk)
            getattr(activity_entry, object2).add(obj2_actual.pk)

            # Record the role for RBAC changes
            if 'role' in kwargs:
                role = kwargs['role']
                if role.content_object is not None:
                    obj_rel = '.'.join([role.content_object.__module__,
                                        role.content_object.__class__.__name__,
                                        role.role_field])

                # If the m2m is from the User side we need to
                # set the content_object of the Role for our entry.
                if type(instance) == User and role.content_object is not None:
                    getattr(activity_entry, role.content_type.name.replace(' ', '_')).add(role.content_object)

                activity_entry.role.add(role)
                activity_entry.object_relationship_type = obj_rel
                activity_entry.save()
            connection.on_commit(
                lambda: emit_activity_stream_change(activity_entry)
            )


@receiver(current_user_getter)
def get_current_user_from_drf_request(sender, **kwargs):
    '''
    Provider a signal handler to return the current user from the current
    request when using Django REST Framework. Requires that the APIView set
    drf_request on the underlying Django Request object.
    '''
    request = get_current_request()
    drf_request_user = getattr(request, 'drf_request_user', False)
    return (drf_request_user, 0)


@receiver(pre_delete, sender=Organization)
def delete_inventory_for_org(sender, instance, **kwargs):
    inventories = Inventory.objects.filter(organization__pk=instance.pk)
    user = get_current_user_or_none()
    for inventory in inventories:
        try:
            inventory.schedule_deletion(user_id=getattr(user, 'id', None))
        except RuntimeError as e:
            logger.debug(e)


@receiver(pre_delete, sender=WorkflowJobTemplateNode)
def delete_approval_templates(sender, instance, **kwargs):
    if type(instance.unified_job_template) is WorkflowApprovalTemplate:
        instance.unified_job_template.delete()


@receiver(pre_save, sender=WorkflowJobTemplateNode)
def delete_approval_node_type_change(sender, instance, **kwargs):
    try:
        old = WorkflowJobTemplateNode.objects.get(id=instance.id)
    except sender.DoesNotExist:
        return
    if old.unified_job_template == instance.unified_job_template:
        return
    if type(old.unified_job_template) is WorkflowApprovalTemplate:
        old.unified_job_template.delete()


@receiver(pre_delete, sender=WorkflowApprovalTemplate)
def deny_orphaned_approvals(sender, instance, **kwargs):
    for approval in WorkflowApproval.objects.filter(workflow_approval_template=instance, status='pending'):
        approval.deny()


@receiver(post_save, sender=Session)
def save_user_session_membership(sender, **kwargs):
    session = kwargs.get('instance', None)
    if not session:
        return
    user_id = session.get_decoded().get(SESSION_KEY, None)
    if not user_id:
        return
    if UserSessionMembership.objects.filter(user=user_id, session=session).exists():
        return
    # check if user_id from session has an id match in User before saving
    if User.objects.filter(id=int(user_id)).exists():
        UserSessionMembership(user_id=user_id, session=session, created=timezone.now()).save()
        expired = UserSessionMembership.get_memberships_over_limit(user_id)
        for membership in expired:
            Session.objects.filter(session_key__in=[membership.session_id]).delete()
            membership.delete()
        if len(expired):
            consumers.emit_channel_notification(
                'control-limit_reached_{}'.format(user_id),
                dict(group_name='control', reason='limit_reached')
            )


@receiver(post_save, sender=OAuth2AccessToken)
def create_access_token_user_if_missing(sender, **kwargs):
    obj = kwargs['instance']
    if obj.application and obj.application.user:
        obj.user = obj.application.user
        post_save.disconnect(create_access_token_user_if_missing, sender=OAuth2AccessToken)
        obj.save()
        post_save.connect(create_access_token_user_if_missing, sender=OAuth2AccessToken)


# Connect the Instance Group to Activity Stream receivers.
post_save.connect(activity_stream_create, sender=InstanceGroup, dispatch_uid=str(InstanceGroup) + "_create")
pre_save.connect(activity_stream_update, sender=InstanceGroup, dispatch_uid=str(InstanceGroup) + "_update")
pre_delete.connect(activity_stream_delete, sender=InstanceGroup, dispatch_uid=str(InstanceGroup) + "_delete")
