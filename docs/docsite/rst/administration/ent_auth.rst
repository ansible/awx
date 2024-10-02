.. _ag_ent_auth:

Setting up Enterprise Authentication
==================================================


.. index::
    single: enterprise authentication
    single: authentication

This section describes setting up authentication for the following enterprise systems:

.. contents::
    :local:

- Enterprise users can only be created via the first successful login attempt from remote authentication backend.
- Enterprise users cannot be created/authenticated if non-enterprise users with the same name has already been created in AWX.
- AWX passwords of enterprise users should always be empty and cannot be set by any user if there are enterprise backend-enabled.
- If enterprise backends are disabled, an enterprise user can be converted to a normal AWX user by setting the password field. However, this operation is irreversible, as the converted AWX user can no longer be treated as enterprise user.
