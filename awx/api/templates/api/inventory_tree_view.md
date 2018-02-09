# Group Tree for {{ model_verbose_name|title|anora }}:

Make a GET request to this resource to retrieve a hierarchical view of groups
associated with the selected {{ model_verbose_name }}.

The resulting data structure contains a list of root groups, with each group
also containing a list of its children.

## Results

Each group data structure includes the following fields:

{% include "api/_result_fields_common.md" %}
