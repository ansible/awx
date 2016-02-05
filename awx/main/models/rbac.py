# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models.base import * # noqa

__all__ = ['Role', 'RolePermission', 'Resource', 'RoleHierarchy', 'ResourceHierarchy']

logger = logging.getLogger('awx.main.models.rbac')


class Role(CommonModelNameNotUnique):
    '''
    Role model
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('roles')
        db_table = 'main_rbac_roles'

    singleton_name = models.TextField(null=True, default=None, db_index=True, unique=True)
    parents = models.ManyToManyField('Role', related_name='children')
    members = models.ManyToManyField('auth.User', related_name='roles')

    def save(self, *args, **kwargs):
        super(Role, self).save(*args, **kwargs)
        self.rebuild_role_hierarchy_cache()

    def rebuild_role_hierarchy_cache(self):
        'Rebuilds the associated entries in the RoleHierarchy model'

        # Compute what our hierarchy should be. (Note: this depends on our
        # parent's cached hierarchy being correct)
        parent_ids = set([parent.id for parent in self.parents.all()])
        actual_ancestors = set([r.ancestor.id for r in RoleHierarchy.objects.filter(role__id__in=parent_ids)])
        actual_ancestors.add(self.id)

        # Compute what we have stored
        stored_ancestors = set([r.ancestor.id for r in RoleHierarchy.objects.filter(role__id=self.id)])

        # If it differs, update, and then update all of our children
        if actual_ancestors != stored_ancestors:
            RoleHierarchy.objects.filter(role__id=self.id).delete()
            for id in actual_ancestors:
                rh = RoleHierarchy(role=self, ancestor=Role.objects.get(id=id))
                rh.save()
            for child in self.children.all():
                child.rebuild_role_hierarchy_cache()

    def grant(self, resource, permissions):
        # take either the raw Resource or something that includes the ResourceMixin
        resource = resource if type(resource) is Resource else resource.resource

        if 'all' in permissions and permissions['all']:
            del permissions['all']
            permissions['create']     = True
            permissions['read']       = True
            permissions['write']      = True
            permissions['update']     = True
            permissions['delete']     = True
            permissions['scm_update'] = True
            permissions['use']        = True
            permissions['execute']    = True

        permission = RolePermission(role=self, resource=resource)
        for k in permissions:
            setattr(permission, k, int(permissions[k]))
        permission.save()

    @staticmethod
    def singleton(name):
        try:
            return Role.objects.get(singleton_name=name)
        except Role.DoesNotExist:
            ret = Role(singleton_name=name)
            ret.save()
            return ret

    def is_ancestor_of(self, role):
        return RoleHierarchy.objects.filter(role_id=role.id, ancestor_id=self.id).count() > 0



class RoleHierarchy(CreatedModifiedModel):
    '''
    Stores a flattened relation map of all roles in the system for easy joining
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('role_ancestors')
        db_table = 'main_rbac_role_hierarchy'

    role = models.ForeignKey('Role', related_name='+', on_delete=models.CASCADE)
    ancestor = models.ForeignKey('Role', related_name='+', on_delete=models.CASCADE)


class Resource(CommonModelNameNotUnique):
    '''
    Role model
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('resources')
        db_table = 'main_rbac_resources'

    parent = models.ForeignKey('Resource', related_name='children', null=True, default=None)

    def save(self, *args, **kwargs):
        super(Resource, self).save(*args, **kwargs)
        self.rebuild_resource_hierarchy_cache()

    def rebuild_resource_hierarchy_cache(self):
        'Rebuilds the associated entries in the ResourceHierarchy model'

        # Compute what our hierarchy should be. (Note: this depends on our
        # parent's cached hierarchy being correct)
        actual_ancestors = set()
        if self.parent:
            actual_ancestors = set([r.ancestor.id for r in ResourceHierarchy.objects.filter(resource__id=self.parent.id)])
        actual_ancestors.add(self.id)

        # Compute what we have stored
        stored_ancestors = set([r.ancestor.id for r in ResourceHierarchy.objects.filter(resource__id=self.id)])

        # If it differs, update, and then update all of our children
        if actual_ancestors != stored_ancestors:
            ResourceHierarchy.objects.filter(resource__id=self.id).delete()
            for id in actual_ancestors:
                rh = ResourceHierarchy(resource=self, ancestor=Resource.objects.get(id=id))
                rh.save()
            for child in self.children.all():
                child.rebuild_resource_hierarchy_cache()



class ResourceHierarchy(CreatedModifiedModel):
    '''
    Stores a flattened relation map of all resources in the system for easy joining
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('resource_ancestors')
        db_table = 'main_rbac_resource_hierarchy'

    resource = models.ForeignKey('Resource', related_name='+', on_delete=models.CASCADE)
    ancestor = models.ForeignKey('Resource', related_name='+', on_delete=models.CASCADE)


class RolePermission(CreatedModifiedModel):
    '''
    Defines the permissions a role has
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('permissions')
        db_table = 'main_rbac_permissions'

    role = models.ForeignKey(
        Role,
        null=False,
        on_delete=models.CASCADE,
        related_name='permissions',
    )
    resource = models.ForeignKey(
        Resource,
        null=False,
        on_delete=models.CASCADE,
        related_name='permissions',
    )
    create     = models.IntegerField(default = 0)
    read       = models.IntegerField(default = 0)
    write      = models.IntegerField(default = 0)
    update     = models.IntegerField(default = 0)
    delete     = models.IntegerField(default = 0)
    execute    = models.IntegerField(default = 0)
    scm_update = models.IntegerField(default = 0)
    use        = models.IntegerField(default = 0)

