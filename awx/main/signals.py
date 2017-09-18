# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import contextlib
import logging
import threading
import json

# Django
from django.conf import settings
from django.db.models.signals import post_save, pre_delete, post_delete, m2m_changed
from django.dispatch import receiver

# Django-CRUM
from crum import get_current_request, get_current_user
from crum.signals import current_user_getter

# AWX
from awx.main.models import * # noqa
from awx.api.serializers import * # noqa
from awx.main.utils import model_instance_diff, model_to_dict, camelcase_to_underscore
from awx.main.utils import ignore_inventory_computed_fields, ignore_inventory_group_removal, _inventory_updates
from awx.main.tasks import update_inventory_computed_fields
from awx.main.fields import is_implicit_parent

from awx.main.consumers import emit_channel_notification

__all__ = []

logger = logging.getLogger('awx.main.signals')

# Update has_active_failures for inventory/groups when a Host/Group is deleted,
# when a Host-Group or Group-Group relationship is updated, or when a Job is deleted


def get_current_user_or_none():
    u = get_current_user()
    if not isinstance(u, User):
        return None
    return u


def emit_job_event_detail(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs['created']
    if created:
        event_serialized = JobEventSerializer(instance).data
        event_serialized['id'] = instance.id
        event_serialized["created"] = event_serialized["created"].isoformat()
        event_serialized["modified"] = event_serialized["modified"].isoformat()
        event_serialized["event_name"] = instance.event
        event_serialized["group_name"] = "job_events"
        emit_channel_notification('job_events-' + str(instance.job.id), event_serialized)


def emit_ad_hoc_command_event_detail(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs['created']
    if created:
        event_serialized = AdHocCommandEventSerializer(instance).data
        event_serialized['id'] = instance.id
        event_serialized["created"] = event_serialized["created"].isoformat()
        event_serialized["modified"] = event_serialized["modified"].isoformat()
        event_serialized["event_name"] = instance.event
        event_serialized["group_name"] = "ad_hoc_command_events"
        emit_channel_notification('ad_hoc_command_events-' + str(instance.ad_hoc_command_id), event_serialized)


def emit_update_inventory_computed_fields(sender, **kwargs):
    logger.debug("In update inventory computed fields")
    if getattr(_inventory_updates, 'is_updating', False):
        return
    instance = kwargs['instance']
    if sender == Group.hosts.through:
        sender_name = 'group.hosts'
    elif sender == Group.parents.through:
        sender_name = 'group.parents'
    elif sender == Host.inventory_sources.through:
        sender_name = 'host.inventory_sources'
    elif sender == Group.inventory_sources.through:
        sender_name = 'group.inventory_sources'
    else:
        sender_name = unicode(sender._meta.verbose_name)
    if kwargs['signal'] == post_save:
        if sender == Job:
            return
        sender_action = 'saved'
    elif kwargs['signal'] == post_delete:
        sender_action = 'deleted'
    elif kwargs['signal'] == m2m_changed and kwargs['action'] in ('post_add', 'post_remove', 'post_clear'):
        sender_action = 'changed'
    else:
        return
    logger.debug('%s %s, updating inventory computed fields: %r %r',
                 sender_name, sender_action, sender, kwargs)
    try:
        inventory = instance.inventory
    except Inventory.DoesNotExist:
        pass
    else:
        update_inventory_computed_fields.delay(inventory.id, True)


def emit_update_inventory_on_created_or_deleted(sender, **kwargs):
    if getattr(_inventory_updates, 'is_updating', False):
        return
    instance = kwargs['instance']
    if ('created' in kwargs and kwargs['created']) or \
       kwargs['signal'] == post_delete:
        pass
    else:
        return
    sender_name = unicode(sender._meta.verbose_name)
    logger.debug("%s created or deleted, updating inventory computed fields: %r %r",
                 sender_name, sender, kwargs)
    try:
        inventory = instance.inventory
    except Inventory.DoesNotExist:
        pass
    else:
        if inventory is not None:
            update_inventory_computed_fields.delay(inventory.id, True)


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


def create_user_role(instance, **kwargs):
    if not kwargs.get('created', True):
        return
    try:
        Role.objects.get(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            role_field='admin_role'
        )
    except Role.DoesNotExist:
        role = Role.objects.create(
            role_field='admin_role',
            content_object = instance,
        )
        role.members.add(instance)


def org_admin_edit_members(instance, action, model, reverse, pk_set, **kwargs):
    content_type = ContentType.objects.get_for_model(Organization)

    if reverse:
        return
    else:
        if instance.content_type == content_type and \
           instance.content_object.member_role.id == instance.id:
            items = model.objects.filter(pk__in=pk_set).all()
            for user in items:
                if action == 'post_add':
                    instance.content_object.admin_role.children.add(user.admin_role)
                if action == 'pre_remove':
                    instance.content_object.admin_role.children.remove(user.admin_role)


def rbac_activity_stream(instance, sender, **kwargs):
    user_type = ContentType.objects.get_for_model(User)
    # Only if we are associating/disassociating
    if kwargs['action'] in ['pre_add', 'pre_remove']:
        # Only if this isn't for the User.admin_role
        if hasattr(instance, 'content_type'):
            if instance.content_type in [None, user_type]:
                return
            elif sender.__name__ == 'Role_parents':
                role = kwargs['model'].objects.filter(pk__in=kwargs['pk_set']).first()
                # don't record implicit creation / parents in activity stream
                if role is not None and is_implicit_parent(parent_role=role, child_role=instance):
                    return
            else:
                role = instance
            instance = instance.content_object
        else:
            role = kwargs['model'].objects.filter(pk__in=kwargs['pk_set']).first()

        activity_stream_associate(sender, instance, role=role, **kwargs)


def cleanup_detached_labels_on_deleted_parent(sender, instance, **kwargs):
    for l in instance.labels.all():
        if l.is_candidate_for_detach():
            l.delete()


def connect_computed_field_signals():
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Host)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Group)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Group)
    m2m_changed.connect(emit_update_inventory_computed_fields, sender=Group.hosts.through)
    m2m_changed.connect(emit_update_inventory_computed_fields, sender=Group.parents.through)
    m2m_changed.connect(emit_update_inventory_computed_fields, sender=Host.inventory_sources.through)
    m2m_changed.connect(emit_update_inventory_computed_fields, sender=Group.inventory_sources.through)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_save.connect(emit_update_inventory_on_created_or_deleted, sender=Job)
    post_delete.connect(emit_update_inventory_on_created_or_deleted, sender=Job)


connect_computed_field_signals()


post_save.connect(emit_job_event_detail, sender=JobEvent)
post_save.connect(emit_ad_hoc_command_event_detail, sender=AdHocCommandEvent)
m2m_changed.connect(rebuild_role_ancestor_list, Role.parents.through)
m2m_changed.connect(org_admin_edit_members, Role.members.through)
m2m_changed.connect(rbac_activity_stream, Role.members.through)
m2m_changed.connect(rbac_activity_stream, Role.parents.through)
post_save.connect(sync_superuser_status_to_rbac, sender=User)
post_save.connect(create_user_role, sender=User)
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
    last_job = jhs.job if jhs else None
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

    def __nonzero__(self):
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
    m2m_changed.disconnect(emit_update_inventory_computed_fields, sender=Group.hosts.through)
    m2m_changed.disconnect(emit_update_inventory_computed_fields, sender=Group.parents.through)
    m2m_changed.disconnect(emit_update_inventory_computed_fields, sender=Host.inventory_sources.through)
    m2m_changed.disconnect(emit_update_inventory_computed_fields, sender=Group.inventory_sources.through)
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=InventorySource)
    post_save.disconnect(emit_update_inventory_on_created_or_deleted, sender=Job)
    post_delete.disconnect(emit_update_inventory_on_created_or_deleted, sender=Job)
    yield
    connect_computed_field_signals()


model_serializer_mapping = {
    Organization: OrganizationSerializer,
    Inventory: InventorySerializer,
    Host: HostSerializer,
    Group: GroupSerializer,
    InventorySource: InventorySourceSerializer,
    CustomInventoryScript: CustomInventoryScriptSerializer,
    Credential: CredentialSerializer,
    Team: TeamSerializer,
    Project: ProjectSerializer,
    JobTemplate: JobTemplateSerializer,
    Job: JobSerializer,
    AdHocCommand: AdHocCommandSerializer,
    NotificationTemplate: NotificationTemplateSerializer,
    Notification: NotificationSerializer,
}


def activity_stream_create(sender, instance, created, **kwargs):
    if created and activity_stream_enabled:
        # TODO: remove deprecated_group conditional in 3.3
        # Skip recording any inventory source directly associated with a group.
        if isinstance(instance, InventorySource) and instance.deprecated_group:
            return
        _type = type(instance)
        if getattr(_type, '_deferred', False):
            return
        object1 = camelcase_to_underscore(instance.__class__.__name__)
        changes = model_to_dict(instance, model_serializer_mapping)
        # Special case where Job survey password variables need to be hidden
        if type(instance) == Job:
            if 'extra_vars' in changes:
                changes['extra_vars'] = instance.display_extra_vars()
        activity_entry = ActivityStream(
            operation='create',
            object1=object1,
            changes=json.dumps(changes),
            actor=get_current_user_or_none())
        activity_entry.save()
        #TODO: Weird situation where cascade SETNULL doesn't work
        #      it might actually be a good idea to remove all of these FK references since
        #      we don't really use them anyway.
        if instance._meta.model_name != 'setting':  # Is not conf.Setting instance
            getattr(activity_entry, object1).add(instance)


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
    changes = model_instance_diff(old, new, model_serializer_mapping)
    if changes is None:
        return
    _type = type(instance)
    if getattr(_type, '_deferred', False):
        return
    object1 = camelcase_to_underscore(instance.__class__.__name__)
    activity_entry = ActivityStream(
        operation='update',
        object1=object1,
        changes=json.dumps(changes),
        actor=get_current_user_or_none())
    activity_entry.save()
    if instance._meta.model_name != 'setting':  # Is not conf.Setting instance
        getattr(activity_entry, object1).add(instance)


def activity_stream_delete(sender, instance, **kwargs):
    if not activity_stream_enabled:
        return
    # TODO: remove deprecated_group conditional in 3.3
    # Skip recording any inventory source directly associated with a group.
    if isinstance(instance, InventorySource) and instance.deprecated_group:
        return
    # Inventory delete happens in the task system rather than request-response-cycle.
    # If we trigger this handler there we may fall into db-integrity-related race conditions.
    # So we add flag verification to prevent normal signal handling. This funciton will be
    # explicitly called with flag on in Inventory.schedule_deletion.
    if isinstance(instance, Inventory) and not kwargs.get('inventory_delete_flag', False):
        return
    _type = type(instance)
    if getattr(_type, '_deferred', False):
        return
    changes = model_to_dict(instance)
    object1 = camelcase_to_underscore(instance.__class__.__name__)
    activity_entry = ActivityStream(
        operation='delete',
        changes=json.dumps(changes),
        object1=object1,
        actor=get_current_user_or_none())
    activity_entry.save()


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
            activity_entry = ActivityStream(
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
            getattr(activity_entry, object1).add(obj1)
            getattr(activity_entry, object2).add(obj2_actual)

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


@receiver(current_user_getter)
def get_current_user_from_drf_request(sender, **kwargs):
    '''
    Provider a signal handler to return the current user from the current
    request when using Django REST Framework. Requires that the APIView set
    drf_request on the underlying Django Request object.
    '''
    request = get_current_request()
    drf_request = getattr(request, 'drf_request', None)
    return (getattr(drf_request, 'user', False), 0)


@receiver(pre_delete, sender=Organization)
def delete_inventory_for_org(sender, instance, **kwargs):
    inventories = Inventory.objects.filter(organization__pk=instance.pk)
    user = get_current_user_or_none()
    for inventory in inventories:
        try:
            inventory.schedule_deletion(user_id=getattr(user, 'id', None))
        except RuntimeError, e:
            logger.debug(e)
