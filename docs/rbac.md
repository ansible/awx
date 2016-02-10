# Role-Based Access Control (RBAC)

This document describes the RBAC implementation of the Ansible Tower Software.
The intended audience of this document is the Ansible Tower developer.

## Overview

The RBAC system allows you to create and layer roles for controlling access to resources. Any `django.Model` can
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

This would provide anyone with the ResourceA.AdminRole or ResourceB.AdminRole access to ResourceB.

## Models

`Role`

`RoleHierarchy`

`Resource`

`RolePermission`

## Fields

`ImplicitRoleField`

`ImplicitResourceField`

## Mixins

`ResourceMixin`

Usage
-----

