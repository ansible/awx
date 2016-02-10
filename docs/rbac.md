# Role-Based Access Control (RBAC)

This document describes the RBAC implementation of the Ansible Tower Software.
The intended audience of this document is the Ansible Tower developer.

## Overview

The RBAC system allows you to create and layer roles for controlling access to resources. Any django Model can
be made into a `Resource` in the RBAC system by using the `ResourceMixin`. Once a model is accessible as a resource you can
extend the model definition to have specific roles using the `ImplicitRoleField`. This role field allows you to
configure the name of a role, any parents a role may have, and the permissions having this role will grant you to the resource.

### Roles

Roles are defined for a resource. If a role has any parents, these parents will be considered when determing
what roles are checked when accessing a resource.

    ResourceA
     |-- AdminRole

    ResourceB
     | -- AdminRole
           |-- parent = ResourceA.AdminRole

When a user attempts to access ResourceB we will check for their access using the set of all unique roles, include the parents.

    set: ResourceA.AdminRole, ResourceB.AdminRole

This would provide anyone with the above roles access to ResourceB.

## Models

The RBAC system defines a few new models. These models represent the underlying RBAC implemnentation and generally will be abstracted away from your daily development tasks by the implicict fields and mixins.

### `Role`

### `Resource`

### `RoleHierarchy`

### `RolePermission`

## Fields

`ImplicitRoleField`

`ImplicitResourceField`

## Mixins

### `ResourceMixin`

By mixing in the `ResourceMixin` to your model, you are turning your model in to a `Resource` in the eyes of the RBAC implementation. What this means simply is that your model will now have an `ImplicitResourceField` named resource. Your model will also gain some methods that aid in the checking the access a users roles provides them to a resource.

#### `accessible_objects(cls, user, permissions)`

`accessible_objects` is a class method to use instead of `Model.objects`. This method will restrict the query of objects to only the objects that a user has the passed in permissions for. This is useful when you want to only filter and display a `Resource` that a users role grants them the `permissions` to. Note that any permission fields that are left blank will default to `False`. `accessible_objects` will only filter out resources where the expected permission was `True` but was returned as `False`.

```python
    objects = Model.accessible_objects(user, {'write':True})
    objects.filter(name__istartswith='december')
```

#### `get_permissions(self, user)`

`get_permissions` is an instance method that will give you the permission dictionary for a given user. This permission dictionary will take in to account any parent roles the user is apart of.

```python
    >>> instance.get_permissions(admin)
    {'create':True, 'read':True, 'write':True, 'update':True,
     'delete':True, 'scm_update':True, 'execute':True, 'use':True}
```


#### `accessible_by(self, user, permissions)`

`accessible_by` is an instance method that wraps the `get_permissions` method. Given a user and a dictionary of permissions this method will return True or False if a users roles give them a set of permissions that match the provided permissions dict. Not that any permission fields left blank will default to `False`. `accessible_by` will only return `False` in a case where the passed in permission is expected to be `True` but was returned as `False`.

```python
    >>> instance.accessible_by(admin, {'use':True, 'read':True})
    True
```
## Usage

After exploring the _Overview_ the usage of the RBAC implementation in your code should feel unintrisive and natural.

```python
    # make your model a Resource
    class Document(Model, ResourceMixin):
       ...
    # declare your new role
    readonly_role = ImplicitRoleField(
        role_name="readonly",
        resource_field="resource",
        permissions={'read':True},
    )
```

Now that your model is a `Resource` and has a `Role` defined, you can be get to access the helper methods provided to you by the `ResourceMixin` for checking access to your resource. Here is the output of a Python REPL session.

```python
    # we've created some documents and a user
    >>> document = Document.objects.filter(pk=1)
    >>> user = User.objects.first()
    >>> document.accessible_by(user, {'read': True})
    False  # not accessible by default
    >>> document.readonly_role.memebers.add(user)
    >>> document.accessible_by(user, {'read':True})
    True   # now it is accessible
    >>> document.accessible_by(user, {'read':True, 'write':True})
    False  # my role does not have write permission
```


