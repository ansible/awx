# Docker ELK / Elastic Stack Development Tools

These are tools to run a containerized version of ELK stack, comprising
of Logstash, Elastic Search, and Kibana. There are also cases where
only a subset of these are needed to run.

A copy of the license is in `docs/licenses/docker-elk.txt`

## Instructions

Due to complex requirements from the elastic search container upstream, there
is a prerequisite to get the containers running. The docker _host_ machine
must have the `max_map_count` variable increased. For a developer using
docker-machine with something like VirtualBox of VMWare, this can be
done by getting bash in the running Docker machine. Example:

```bash
$ docker-machine ssh default
docker@default:~$ sudo sysctl -w vm.max_map_count=262144
vm.max_map_count = 262144
```

After this, the containers can be started up with commands like:

```bash
make docker-compose-elk
```

```bash
make docker-compose-cluster-elk
```

These are ran from the root folder of the ansible-tower repository.

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

