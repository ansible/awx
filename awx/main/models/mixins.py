# Django
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User # noqa

# AWX
from awx.main.models.rbac import (
    Role, get_roles_on_resource
)


__all__ = ['ResourceMixin']

class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def accessible_objects(cls, accessor, role_name):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:

        MyModel.accessible_objects(user, {'read': True}).filter(name__istartswith='bar');

        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''
        return ResourceMixin._accessible_objects(cls, accessor, role_name)

    @staticmethod
    def _accessible_objects(cls, accessor, role_name):
        if type(cls()) == User:
            cls_type = ContentType.objects.get_for_model(cls)
            roles = Role.objects.filter(content_type__pk=cls_type.id)

            if type(accessor) == User:
                roles = roles.filter(ancestors__members = accessor)
            elif type(accessor) == Role:
                roles = roles.filter(ancestors = accessor)
            else:
                accessor_type = ContentType.objects.get_for_model(accessor)
                accessor_roles = Role.objects.filter(content_type__pk=accessor_type.id,
                                                     object_id=accessor.id)
                roles = roles.filter(ancestors__in=accessor_roles)

            kwargs = {'id__in':roles.values_list('object_id', flat=True)}
            return cls.objects.filter(**kwargs).distinct()

        if type(accessor) == User:
            kwargs = {}
            kwargs[role_name + '__ancestors__members'] = accessor
            qs = cls.objects.filter(**kwargs)
        elif type(accessor) == Role:
            kwargs = {}
            kwargs[role_name + '__ancestors'] = accessor
            qs = cls.objects.filter(**kwargs)
        else:
            accessor_type = ContentType.objects.get_for_model(accessor)
            roles = Role.objects.filter(content_type__pk=accessor_type.id,
                                        object_id=accessor.id)
            kwargs = {}
            kwargs[role_name + '__ancestors__in'] = roles
            qs = cls.objects.filter(**kwargs)

        return qs.distinct()


    def get_permissions(self, accessor):
        '''
        Returns a dict (or None) of the roles a accessor has for a given resource.
        An accessor can be either a User, Role, or an arbitrary resource that
        contains one or more Roles associated with it.
        '''

        return get_roles_on_resource(self, accessor)

