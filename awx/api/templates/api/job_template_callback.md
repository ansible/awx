The job template callback allows for ephemeral hosts to launch a new job.

Configure a host to POST to this resource, passing the `host_config_key`
parameter, to start a new job limited to only the requesting host.  In the
examples below, replace the `N` parameter with the `id` of the job template
and the `HOST_CONFIG_KEY` with the `host_config_key` associated with the
job template.

For example, using curl:

    curl --data-urlencode host_config_key=HOST_CONFIG_KEY http://server/api/v1/job_templates/N/callback/

Or using wget:

    wget -O /dev/null --post-data="host_config_key=HOST_CONFIG_KEY" http://server/api/v1/job_templates/N/callback/
    
The response will return status 202 if the request is valid, 403 for an
invalid host config key, or 400 if the host cannot be determined from the
address making the request.

_(New in Ansible Tower 2.0.0)_ By default, the host must already be present in
inventory for the callback to succeed.  The `refresh_inventory` parameter can
be passed to the callback to trigger an inventory sync prior to searching for
the host and running the job.  The associated inventory must have the
`update_on_launch` flag set and will only refresh if the `update_cache_timeout`
has expired.

For example, using curl:

    curl --data-urlencode "host_config_key=HOST_CONFIG_KEY&refresh_inventory=1" http://server/api/v1/job_templates/N/callback/

A GET request may be used to verify that the correct host will be selected.
This request must authenticate as a valid user with permission to edit the
job template.  For example:

    curl http://user:password@server/api/v1/job_templates/N/callback/

The response will include the host config key as well as the host name(s)
that would match the request:

    {
        "host_config_key": "HOST_CONFIG_KEY",
        "matching_hosts": ["hostname"]
    }
