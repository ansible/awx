# How to use the logstash container

#### Modify the docker-compose.yml

You can run the logstash container by adding another compose file to the docker-compose target.

```
COMPOSE_OPTS="-f tools/docker-compose/logstash-override.yaml" COMPOSE_TAG=devel make docker-compose
```

POST the following content to `/api/v2/settings/logging/` (this uses
authentication set up inside of the logstash configuration file).

```
{
    "LOG_AGGREGATOR_HOST": "http://logstash",
    "LOG_AGGREGATOR_PORT": 8085,
    "LOG_AGGREGATOR_TYPE": "logstash",
    "LOG_AGGREGATOR_USERNAME": "awx_logger",
    "LOG_AGGREGATOR_PASSWORD": "workflows",
    "LOG_AGGREGATOR_LOGGERS": [
        "awx",
        "activity_stream",
        "job_events",
        "system_tracking",
        "job_lifecycle"
    ],
    "LOG_AGGREGATOR_INDIVIDUAL_FACTS": false,
    "LOG_AGGREGATOR_TOWER_UUID": "991ac7e9-6d68-48c8-bbde-7ca1096653c6",
    "LOG_AGGREGATOR_ENABLED": true
}
```

> Note: HTTP must be specified in the `LOG_AGGREGATOR_HOST` if you are using the docker development environment.  

An example of how to view the most recent logs from the container:

```
docker exec -i -t $(docker ps -aqf "name=tools_logstash_1") tail -n 50 /logstash.log
```

#### How to add logstash plugins

Add any plugins you need in `tools/elastic/logstash/Dockerfile` before running the container.  
