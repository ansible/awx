{% ifmeth GET %}
# Health Check Data

Health checks are used to obtain important data about an instance.
Instance fields affected by the health check are shown in this view.
Fundamentally, health checks require running code on the machine in question.

 - For instances with `node_type` of "control" or "hybrid", health checks are
performed as part of a periodic task that runs in the background.
 - For instances with `node_type` of "execution", health checks are done by submitting
a work unit through the receptor mesh.

If ran through the receptor mesh, the invoked command is:

```
ansible-runner worker --worker-info
```

For execution nodes, these checks are _not_ performed on a regular basis.
Health checks against functional nodes will be ran when the node is first discovered.
Health checks against nodes with errors will be repeated at a reduced frequency.

{% endifmeth %}

{% ifmeth POST %}
# Manually Initiate a Health Check
For purposes of error remediation or debugging, a health check can be
manually initiated by making a POST request to this endpoint.

This will submit the work unit to the target node through the receptor mesh and wait for it to finish.
The model will be updated with the result.
Up-to-date values of the fields will be returned in the response data.
{% endifmeth %}
