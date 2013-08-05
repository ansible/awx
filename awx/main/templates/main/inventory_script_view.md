Generate inventory group and host data as needed for an inventory script.

Make a GET request to this resource without query parameters to retrieve a JSON
object containing groups, including the hosts, children and variables for each
group.  The response data is equivalent to that returned by passing the
`--list` argument to an inventory script.

Make a GET request to this resource with a query string similar to
`?host=HOSTNAME` to retrieve a JSON object containing host variables for the
specified host.  The response data is equivalent to that returned by passing
the `--host HOSTNAME` argument to an inventory script.
