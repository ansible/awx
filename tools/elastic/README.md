# Docker ELK / Elastic Stack Development Tools

These are tools to run a containerized version of ELK stack, comprising
of Logstash, Elastic Search, and Kibana.

A copy of the license is in `docs/licenses/docker-elk.txt`

## Instructions

Due to complex requirements from the elastic search container upstream, there
is a prerequisite to get the containers running. The docker _host_ machine
must have the `max_map_count` variable increased. For a developer using
docker-machine with something like VirtualBox of VMWare, this can be
done by getting via bash in the running Docker machine. Example:

```bash
docker-machine ssh default sudo sysctl -w vm.max_map_count=262144
```
> Note: If you are running docker natively on linux, you need only run `sysctl -w vm.max_map_count=262144`

After this, the containers can be started up with commands like:

```bash
make docker-compose-elk
```

```bash
make docker-compose-cluster-elk
```

These are ran from the root folder of the ansible-tower repository.

Kibana is the visualization service, and it can be accessed in a web browser
by going to `{server address}:5601`.


### Authentication

The default HTTPS logstash configuration makes use of basic auth, so a username
and password is needed in HTTPS configuration, in addition to the other
parameters. The following settings are supported:

```
{
    "LOG_AGGREGATOR_HOST": "logstash",
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
    "LOG_AGGREGATOR_ENABLED": true,
    "LOG_AGGREGATOR_PROTOCOL": "https",
    "LOG_AGGREGATOR_TCP_TIMEOUT": 5
}
```
and
```
{
    "LOG_AGGREGATOR_HOST": "logstash",
    "LOG_AGGREGATOR_PORT": 8086,
    "LOG_AGGREGATOR_TYPE": "logstash",
    "LOG_AGGREGATOR_LOGGERS": [
        "awx",
        "activity_stream",
        "job_events",
        "system_tracking"
    ],
    "LOG_AGGREGATOR_INDIVIDUAL_FACTS": false,
    "LOG_AGGREGATOR_ENABLED": true,
    "LOG_AGGREGATOR_PROTOCOL": "udp",
    "LOG_AGGREGATOR_TCP_TIMEOUT": 5
}
```
and
```
{
    "LOG_AGGREGATOR_HOST": "logstash",
    "LOG_AGGREGATOR_PORT": 8087,
    "LOG_AGGREGATOR_TYPE": "logstash",
    "LOG_AGGREGATOR_LOGGERS": [
        "awx",
        "activity_stream",
        "job_events",
        "system_tracking"
    ],
    "LOG_AGGREGATOR_INDIVIDUAL_FACTS": false,
    "LOG_AGGREGATOR_ENABLED": true,
    "LOG_AGGREGATOR_PROTOCOL": "tcp",
    "LOG_AGGREGATOR_TCP_TIMEOUT": 5
}
```
These can be entered via Configure-Tower-in-Tower by making a POST to
`/api/v2/settings/logging/`.

### Connecting Logstash to 3rd Party Receivers

In order to send these logs to an external consumer of logstash format
messages, replace the output variables in the logstash.conf file.

```
output {
	elasticsearch {
		hosts => "elasticsearch:9200"
	}
}
```

## Changelog

Current branch point `a776151221182dcfaec7df727459e208c895d25b`
Nov 18, 2016


 - Original branch point `b5a4deee142b152d4f9232ebac5bbabb2d2cef3c`
   Sep 25, 2016, before X-Pack support
