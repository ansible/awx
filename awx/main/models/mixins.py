# Django
from django.db import models
from django.db.models.aggregates import Max
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models.rbac import Resource
from awx.main.fields import ImplicitResourceField


__all__ = ['ResourceMixin']

class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    resource = ImplicitResourceField()

    @classmethod
    def accessible_objects(cls, user, permissions):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:

        MyModel.accessible_objects(user, {'read': True}).filter(name__istartswith='bar');

        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''

        qs = Resource.objects.filter(
            content_type=ContentType.objects.get_for_model(cls),
            permissions__role__ancestors__members=user
        )
        for perm in permissions:
            qs = qs.annotate(**{'max_' + perm: Max('permissions__' + perm)})
            qs = qs.filter(**{'max_' + perm: int(permissions[perm])})

        return cls.objects.filter(resource__in=qs)


    def get_permissions(self, user):
        return self.resource.get_permissions(user)

    def accessible_by(self, user, permissions):
        '''
        Returns true if the user has all of the specified permissions
        '''

        perms = self.get_permissions(user)
        if perms is None:
            return False
        for k in permissions:
            if k not in perms or perms[k] < permissions[k]:
                return False
        return True
