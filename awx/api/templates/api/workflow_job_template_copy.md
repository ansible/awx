Copy a Workflow Job Template:

Make a GET request to this resource to determine if the current user has
permission to copy the {{model_verbose_name}} and whether any linked
templates or prompted fields will be ignored due to permissions problems.
The response will include the following fields:

* `can_copy`: Flag indicating whether the active user has permission to make
  a copy of this {{model_verbose_name}}, provides same content as the
  {{model_verbose_name}} detail view summary_fields.user_capabilities.copy
  (boolean, read-only)
* `can_copy_without_user_input`: Flag indicating if the user should be
  prompted for confirmation before the copy is executed (boolean, read-only)
* `templates_unable_to_copy`: List of node ids of nodes that have a related
  job template, project, or inventory that the current user lacks permission
  to use and will be missing in workflow nodes of the copy (array, read-only)
* `inventories_unable_to_copy`: List of node ids of nodes that have a related
  prompted inventory that the current user lacks permission
  to use and will be missing in workflow nodes of the copy (array, read-only)
* `credentials_unable_to_copy`: List of node ids of nodes that have a related
  prompted credential that the current user lacks permission
  to use and will be missing in workflow nodes of the copy (array, read-only)

Make a POST request to this endpoint to save a copy of this
{{model_verbose_name}}. No POST data is accepted for this action.

If successful, the response status code will be 201. The response body will
contain serialized data about the new {{model_verbose_name}}, which will be
similar to the original {{model_verbose_name}}, but with an additional `@`
and a timestamp in the name.

All workflow nodes and connections in the original will also exist in the
copy. The nodes will be missing related resources if the user did not have
access to use them.
