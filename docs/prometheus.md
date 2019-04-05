# Prometheus Support

## Development

Starting a Prometheus container.

    docker run --net=tools_default --link=tools_awx_1:awxweb --volume ./prometheus.yml:/prometheus.yml --name prometheus -d  -p 127.0.0.1:9090:9090 prom/prometheus --web.enable-lifecycle --config.file=/prometheus.yml

Example Prometheus config.

    # my global config
    global:
    scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
    evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
    # scrape_timeout is set to the global default (10s).
    # Alertmanager configuration
    alerting:
    alertmanagers:
    - static_configs:
        - targets:
        # - alertmanager:9093
    # Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
    rule_files:
    # - "first_rules.yml"
    # - "second_rules.yml"
    # A scrape configuration containing exactly one endpoint to scrape:
    # Here it's Prometheus itself.
    scrape_configs:
    # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
    - job_name: 'prometheus'
        # metrics_path defaults to '/metrics'
        # scheme defaults to 'http'.
        static_configs:
        - targets: ['localhost:9090']
    - job_name: 'awx'
        tls_config:
            insecure_skip_verify: True
        metrics_path: /api/v2/metrics
        scrape_interval: 5s
        scheme: https
        params:
            format: ['txt']
        basic_auth:
        username: root
        password: reverse
        # bearer_token: <token_value>
        static_configs:
                - targets: 
                    - awxweb:8043
