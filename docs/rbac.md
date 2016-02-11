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

The RBAC system defines a few new models. These models represent the underlying RBAC implemnentation and generally will be abstracted away from your daily development tasks by the implicit fields and mixins.

### `Role`

### `Resource`

### `RoleHierarchy`

### `RolePermission`

## Fields

### `ImplicitRoleField`

`ImplicitRoleField` role fields are defined on your model. They provide the definition of grantable roles for accessing your 
`Resource`. Configuring the role is done using some keyword arguments that are provided during declaration.

`resource_field` is the name of the field in your model that is a `ForeignKey` to a `Resource`. If you use the 'ResourceMixin', this field is added to your model for you and is called `resource`. This field is required for the RBAC implementation to integrate any of the role fields you declare for your model. If you did not use the `ResourceMixin` and you have manually added a `Resource` link to your model you will need to set this field accordingly.

`parent_role` is the link to any parent roles you want considered when a user is requesting access to your `Resource`. A `parent_role` can be declared as a single string, `parent.readonly`, or a list of many roles, `['parentA.readonly', 'parentB.readonly']`. It is important to note that a user does not need a parent role to access a resource if granted the role for that resource explicitly. Also a user will not have access to any parent resources by being granted a role for a child resource. We demonstrate this in the _Usage_ section of this document.

`role_name` is the display name of the role. This is useful when generating reports or looking the results of queries.

`permissions` is a dictionary of set permissions that a user with this role will gain to your `Resource`. A permission defaults to `False` if not explicitly provided. Below is a list of available permissions. The special permission `all` is a shortcut for generating a dict with all of the explicit permissions listed below set to `True`.

```python
    # Available Permissions
    {'create':True, 'read':True, 'write':True, 'update':True,
     'delete':True, 'scm_update':True, 'use':True, 'execute':True}
    # Special Permissions
    {'all':True}
    # Example: readonly
    {'read':True}
```

### `ImplicitResourceField`

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

After exploring the _Overview_ the usage of the RBAC implementation in your code should feel unobtrusive and natural.

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

Now that your model is a `Resource` and has a `Role` defined, you can begin to access the helper methods provided to you by the `ResourceMixin` for checking a users access to your resource. Here is the output of a Python REPL session.

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


