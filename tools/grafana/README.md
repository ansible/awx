### Prometheus and Grafana
Prometheus is a metrics collecting tool, and we support prometheus formatted data at the`api/v2/metrics` endpoint.

Prometheus is configured to poll targets on some interval and can use various authentication methods.
We configure prometheus to use basic auth and poll AWX every 5 seconds by default. This configuration is created using the `docker-compose/ansible/roles/sources/templates/prometheus.yml.j2` template. To change the values, modify the template or set the ansible variables used in that template (see use of `EXTRA_SOURCES_ANSIBLE_OPTS` in the next section).

Grafana provides dashboards to visualize this data as well as alerting features.

We use the "provisioning files" functionality in Grafana to be able to deploy alert and dashboard configs from file.

These config files are located in directories that are mounted into the container in `tools/grafana`.

### How to run docker-compose with Grafana and Prometheus

To run the development environment (see [docs](https://github.com/ansible/awx/blob/devel/tools/docker-compose/README.md)) with Prometheus and Grafana enabled, set the following variables:

```
$ PROMETHEUS=yes GRAFANA=yes make docker-compose
```

If we want to pass additional ansible vars used in the deployment process, we can pass `EXTRA_SOURCES_ANSIBLE_OPTS`:

```
GRAFANA=true PROMETHEUS=true EXTRA_SOURCES_ANSIBLE_OPTS="-e scrape_interval=1 admin_password=foobar" make docker-compose
```

### Where to view grafana and prometheus

1. navigate to Prometheus at `http://localhost:9090/targets` and check that the metrics endpoint State is Up.
2. Click the Graph tab, start typing a metric name, or use the Open metrics explorer button to find a metric to display (next to `Execute` button)
3. Navigate to Grafana at `http://localhost:3001`. Sign in, using `admin` for both username and password.
4. In the left navigation menu go to Dashboards->Browse, find the "awx-demo" and click. These should have graphs.
5. Now you can modify these and add panels for whichever metrics you like.

### Alerts in Grafana

We are configuring alerts in grafana using the provisioning files method. This feature is new in Grafana as of August, 2022. Documentation can be found: https://grafana.com/docs/grafana/latest/administration/provisioning/#alerting however it does not fully show all parameters to the config.

One way to understand how to build rules is to build them in the UI and use chrometools to inspect the payload as you save the rules. It appears that the "data" portion of the payload for each rule is the same syntax as needed in the provisioning file config. To reload the alerts without restarting the container, from within the container you can send a POST with `curl -X POST http://admin:admin@localhost:3000/api/admin/provisioning/alerting/reload`. Keep in mind the grafana container does not contain `curl`. You can install it with the command `apk add curl`.

Another way to export rules is explore the api.
1. Get all the folders:  `GET` to `/api/folders`
2. Get the rules `GET` to `/api/ruler/grafana/api/v1/rules/{{ Folder }}`

