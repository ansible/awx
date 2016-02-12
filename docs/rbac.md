# Role-Based Access Control (RBAC)

This document describes the RBAC implementation of the Ansible Tower Software.
The intended audience of this document is the Ansible Tower developer.

## Overview

### Role Based Access Control System Basics

With Role Based Access Control Systems there are four main concepts to be
familiar with, Roles, Resources, Users, and Permissions. Users can be members
of a role, which gives them access to any permissions bestowed upon that Role.
In order to access a Resource, a Permission must be granted to a Role enabling
all members of that Role to access the Resource.

For example, if I have an organization named "MyCompany" and I want to allow
two people, "Alice", and "Bob", access to manage all the settings associated
with that organization, I'd create a role (maybe called "MyCompany
Administrator"), create a Permission to edit the organization "MyCompany" and
assign it to the "MyCompany Administrator" role. I'd also add the two users
"Alice" and "Bob" as members of the Role.

It is often the case that you have many Roles in a system, and you want some
roles to include all of the permissions of other roles. For example, you may
want a System Administrator to have access to everything that an Organization
Administrator has access to, who has everything that a Project Administrator
has access to, and so on. We refer to this concept as the 'Role Hierarchy', and
is represented by allowing Roles to have "Parent Roles". Any permission that a
Role has is implicitly granted to any parent roles (or parents of those
parents, and so on). Of course Roles can have more than one parent, and
permissions are implicitly granted to all parents. (Technically speaking, this
forms a directional graph instead of a hierarchy, but the concept should remain
intuitive.)

![Example RBAC hierarchy](img/rbac_example.png?raw=true)


### Implementation Overview

The RBAC system allows you to create and layer roles for controlling access to resources. Any Django Model can
be made into a `Resource` in the RBAC system by using the `ResourceMixin`. Once a model is accessible as a resource you can
extend the model definition to have specific roles using the `ImplicitRoleField`. This role field allows you to
configure the name of a role, any parents a role may have, and the permissions this role will grant to members.

### Roles

Roles are defined for a resource. If a role has any parents, these parents will be considered when determining
what roles are checked when accessing a resource.

    ResourceA
     |-- AdminRole

    ResourceB
     | -- AdminRole
           |-- parent = ResourceA.AdminRole

When a user attempts to access ResourceB we will check for their access using the set of all unique roles, including the parents.

    ResourceA.AdminRole, ResourceB.AdminRole

This would provide any members of the above roles with access to ResourceB.

#### Singleton Role

There is a special case _Singleton Role_ that you can create. This type of role is for system wide roles.

### Models

The RBAC system defines a few new models. These models represent the underlying RBAC implementation and generally will be abstracted away from your daily development tasks by the implicit fields and mixins.

#### `Role`

`Role` defines a single role within the RBAC implementation. It encapsulates the `ancestors`, `parents`, and `members` for a role. This model is intentionally kept dumb and it has no explicit knowledge of a `Resource`. The `Role` model (get it?), defines some methods that aid in the granting and creation of roles.

##### `grant(self, resource, permissions)`

The `grant` instance method takes a resource and a set of permissions (see below) and creates an entry in the `RolePermission` table (described below). The result of this being that any member of this role will now have those permissions to the resource. The `grant` method considers a resource to be anything that is explicitly of type `Resource` or any model that has a `resource` field of type `Resource`.

##### `singleton(name)`

The `singleton` static method is a helper method on the `Role` model that helps in the creation of singleton roles. It will return the role by name if it already exists or create and return the new role in the case it does not.

##### `rebuild_role_ancestor_list(self)`

`rebuild_role_ancestor_list` will rebuild the current role ancestory that is stored in the `ancestors` field of a `Role`. This is called for you by `save` and different Django signals.

#### `Resource`

`Resource` is simply a method to associate many different objects (that may share PK/unique names) with a single type. The `Resource` type ensure the objunique with respect to the RBAC implementation. Any Django model can be a resource in the RBAC implementation by adding a `resource` field of type `Resource`, but in most cases it is recommended to use the `ResourceMixin` which handles this for you.

#### `RolePermission`

`RolePermission` holds a `role` and a `resource` and the permissions for that unique set. You interact with this model indirectly when declaring `ImplicitRoleField` fields and also when you use the `Role.grant` method. Generally you will not directly use this model unless you are extending the RBAC implementation itself.

### Fields

#### `ImplicitRoleField`

`ImplicitRoleField` fields are declared on your model. They provide the definition of grantable roles for accessing your
`Resource`. Configuring the role is done using some keyword arguments that are provided during declaration.

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

#### `ImplicitResourceField`

The `ImplicitResourceField` is used by the `ResourceMixin` to give your model a `ForeignKey` to a `Resource`. If you use the mixin you will never need to declare this field explicitly for your model.

### Mixins

#### `ResourceMixin`

By mixing in the `ResourceMixin` to your model, you are turning your model in to a `Resource` in the eyes of the RBAC implementation. What this means simply is that your model will now have an `ImplicitResourceField` named resource. Your model will also gain some methods that aid in the checking the access a users roles provides them to a resource.

##### `accessible_objects(cls, user, permissions)`

`accessible_objects` is a class method to use instead of `Model.objects`. This method will restrict the query of objects to only the objects that a user has the passed in permissions for. This is useful when you want to only filter and display a `Resource` that a users role grants them the `permissions` to. Note that any permission fields that are left blank will default to `False`. `accessible_objects` will only filter out resources where the expected permission was `True` but was returned as `False`.

```python
    objects = Model.accessible_objects(user, {'write':True})
    objects.filter(name__istartswith='december')
```

##### `get_permissions(self, user)`

`get_permissions` is an instance method that will give you the permission dictionary for a given user. This permission dictionary will take in to account any parent roles the user is apart of.

```python
    >>> instance.get_permissions(admin)
    {'create':True, 'read':True, 'write':True, 'update':True,
     'delete':True, 'scm_update':True, 'execute':True, 'use':True}
```


##### `accessible_by(self, user, permissions)`

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
