{% ifmeth GET %}
# List Roles for a Team:

Make a GET request to this resource to retrieve a list of roles associated with the selected team.

{% include "api/_list_common.md" %}
{% endifmeth %}

{% ifmeth POST %}
# Associate Roles with this Team:

Make a POST request to this resource to add or remove a role from this team. The following fields may be modified:

   * `id`: The Role ID to add to the team. (int, required)
   * `disassociate`: Provide if you want to remove the role. (any value, optional)
{% endifmeth %}
