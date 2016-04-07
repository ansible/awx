# List Roles for this User:

Make a GET request to this resource to retrieve a list of roles associated with the selected user.

{% include "api/_list_common.md" %}

# Associate Roles with this User:

Make a POST request to this resource to add or remove a role from this user. The following fields may be modified:

   * `id`: Required. The Role ID to add to the user. 
   * `disassociate`: Optional. Provide if you want to remove the role.
