# Prometheus Support

## Development
AWX comes with an example prometheus container and make target.  To use it:

1.  Edit `tools/prometheus/prometheus.yml` and update the `basic_auth` section
    to specify a valid user/password for an AWX user you've created.
    Alternatively, you can provide an OAuth2 token (which can be generated at
    `/api/v2/users/N/personal_tokens/`).
2.  Start the Prometheus container:
    `make prometheus`
