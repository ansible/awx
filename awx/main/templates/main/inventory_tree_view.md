# Group Tree for this {{ model_verbose_name|title }}:

Make a GET request to this resource to retrieve a hierarchical view of groups
associated with the selected {{ model_verbose_name }}.

The resulting data structure contains a list of root groups, with each group
also containing a list of its children.

## Results

Each group data structure includes the following fields:

{% include "main/_result_fields_common.md" %}

{% include "main/_new_in_awx.md" %}
