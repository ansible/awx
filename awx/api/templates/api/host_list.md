{% include "api/list_api_view.md" %}

`host_filter` is available on this endpoint. The filter supports: relational queries, `AND` `OR` boolean logic, as well as expression grouping via `()`.

    ?host_filter=name=my_host
    ?host_filter=name="my host" OR name=my_host
    ?host_filter=groups__name="my group"
    ?host_filter=name=my_host AND groups__name="my group"
    ?host_filter=name=my_host AND groups__name="my group"
    ?host_filter=(name=my_host AND groups__name="my group") OR (name=my_host2 AND groups__name=my_group2)

`host_filter` can also be used to query JSON data in the related `ansible_facts`. `__` may be used to traverse JSON dictionaries. `[]` may be used to traverse JSON arrays.

    ?host_filter=ansible_facts__ansible_processor_vcpus=8
    ?host_filter=ansible_facts__ansible_processor_vcpus=8 AND name="my_host" AND ansible_facts__ansible_lo__ipv6[]__scope=host
