# Prometheus Container

## Development
AWX comes with an example Prometheus container and `make` target.  To use it:

1.  Edit `tools/prometheus/prometheus.yml` and update the `basic_auth` section
    to specify a valid user/password for an AWX user you've created.
    Alternatively, you can provide an OAuth2 token (which can be generated at
    `/api/v2/users/N/personal_tokens/`).  

    > Note: By default, the config assumes a user with username=admin and password=password.

2.  Start the Prometheus container:
    `make prometheus`
3.  The Prometheus UI will now be accessible at `http://localhost:9090/graph`.

There should be no extra setup needed.  You can try executing this query in the
UI to get back the number of active sessions: `awx_sessions_total`
