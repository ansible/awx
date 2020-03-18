# Docker Compose for Dev container

## How to start the Dev container

In the root directory of your awx clone, run the following to build your docker image:

```
make docker-compose-build
```

Copy over your local settings 

```
cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py
```

Build the UI

```
make ui-devel
```

Run the container 

```
make docker-compose
```

The app should now be accessible in your browser at `https://localhost:8043/#/home`


## How to use the logstash container

#### Modify the docker-compose.yml

Uncomment the following lines in the `docker-compose.yml`

```
#- logstash
...

#logstash:
#  build:
#    context: ./docker-compose
#    dockerfile: Dockerfile-logstash
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
        "system_tracking"
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
