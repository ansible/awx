# Integration With Third-Party Log Aggregators

This feature builds in the capability to send detailed logs to several kinds
of third party external log aggregation services. Services connected to this
data feed should be useful in order to gain insights into Tower usage
or technical trends. The data is intended to be
sent in JSON format via three ways: over an HTTP connection, a direct TCP
connection, or a direct UDP connection. It uses minimal service-specific
tweaks engineered in a custom handler or via an imported library.


## Loggers

This feature introduces several new loggers which are intended to
deliver a large amount of information in a predictable and structured format,
following the same structure as one would expect if obtaining the data
from the API. These data loggers are the following:

 - `awx.analytics.job_events` - Data returned from the Ansible callback module
 - `awx.analytics.activity_stream` - Record of changes to the objects within the Ansible Tower app
 - `awx.analytics.system_tracking` - Data gathered by Ansible scan modules ran by scan job templates

These loggers only use log-level of `INFO`. Additionally, the standard Tower logs are deliverable through this
same mechanism. It should be obvious to the user how to enable or disable
each of these five sources of data without manipulating a complex dictionary
in their local settings file, as well as adjust the log level consumed
from the standard Tower logs.


## Supported Services

Committed to support:

 - Splunk
 - Elastic Stack / ELK Stack / Elastic Cloud

Have tested:

 - Sumologic
 - Loggly

Considered, but have not tested:

 - Datadog
 - Red Hat Common Logging via Logstash connector


### Elastic Search Instructions

In the development environment, the server can be started up with the
log aggregation services attached via the Makefile targets. This starts
up the three associated services of Logstash, Elastic Search, and Kibana
as their own separate containers.

In addition to running these services, it establishes connections to the
`tower_tools` containers as needed. This is derived from the [`docker-elk`
project](https://github.com/deviantony/docker-elk):

```bash
# Start a single server with links
make docker-compose-elk
# Start the HA cluster with links
make docker-compose-cluster-elk
```

For more instructions on getting started with the environment that this example spins
up, also refer to instructions in [`/tools/elastic/README.md`](https://github.com/ansible/awx/blob/devel/tools/elastic/README.md).

If you were to start from scratch, standing up your own version of the Elastic
Stack, then the only change you should need is to add the following lines
to the Logstash `logstash.conf` file:

```
filter {
	json {
		source => "message"
	}
}
```


#### Debugging and Pitfalls

Backward-incompatible changes were introduced with Elastic 5.0.0, and
customers may need different configurations depending on what
versions they are using.


# Log Message Schema

Common schema for all loggers:

| Field | Information |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cluster_host_id` | (string) Unique identifier of the host within the Tower cluster |
| `level` | (choice of `DEBUG`, `INFO`, `WARNING`, `ERROR`, etc.) Standard python log level, roughly reflecting the significance of the event; all of the data loggers (as a part of this feature) use `INFO` level, but the other Tower logs will use different levels as appropriate |
| `logger_name` | (string) Name of the logger we use in the settings, *e.g.*, "`awx.analytics.activity_stream`" |
| `@timestamp` | (datetime) Time of log |
| `path` | (string) File path in code where the log was generated |


## Activity Stream Schema

| Field             | Information                                                                                                             |
|-------------------|-------------------------------------------------------------------------------------------------------------------------|
| (common)          | This uses all the fields common to all loggers listed above                                                             |
| actor             | (string) Username of the user who took the action documented in the log |
| changes           | (string) Unique identifier of the host within the Tower cluster                                                         |
| operation         | (choice of several options) The basic category of the change logged in the Activity Stream, for instance, "associate". |
| object1           | (string) Information about the primary object being operated on, consistent with what we show in the Activity Stream    |
| object2           | (string) If applicable, the second object involved in the action                                                        |


## Job Event Schema

This logger echoes the data being saved into Job Events, except when they
would otherwise conflict with expected standard fields from the logger (in which case the fields are named differently).
Notably, the field `host` on the `job_event` model is given as `event_host`.
There is also a sub-dictionary field `event_data` within the payload,
which will contain different fields depending on the specifics of the
Ansible event.

This logger also includes the common fields.


## Scan / Fact / System Tracking Data Schema

These contain a detailed dictionary-type field for either services,
packages, or files.

| Field        | Information                                                                                                                                                                                                       |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| (common)     | This uses all the fields common to all loggers listed above                                                                                                                                                       |
| services     | (dict, optional) For services scans, this field is included and has keys based on the name of the service. **NOTE:** Periods are disallowed by Elastic Search in names, and are replaced with `"_"` by our log formatter |
| packages     | (dict, optional) Included for log messages from package scans                                                                                                                                                     |
| files        | (dict, optional) Included for log messages from file scans                                                                                                                                                        |
| host         | (str) Name of host that the scan applies to                                                                                                                                                                                |
| inventory_id | (int) Inventory ID host is inside of  


## Job Status Changes

This is a intended to be a lower-volume source of information about
changes in job states compared to Job Events, and also intended to
capture changes to types of Unified Jobs other than Job Template-based
jobs.

In addition to common fields, these logs include fields present on
the job model.


## Tower Logs

In addition to the common fields, this will contain a `msg` field with
the log message. Errors contain a separate `traceback` field.
These logs can be enabled or disabled in CTiT by adding or removing
it to the setting `LOG_AGGREGATOR_LOGGERS`.


# Configuring Inside of Tower

Parameters needed in order to configure the connection to the log
aggregation service will include most of the following for all
supported services:

 - Host
 - Port
 - The type of service, allowing service-specific customizations
 - Optional username for the connection, used by certain services
 - Some kind of token or password
 - A flag to indicate how system tracking records will be sent
 - Selecting which loggers to send
 - Enabling sending logs
 - Connection type (HTTPS, TCP, or UDP)
 - Timeout value if connection type is based on TCP protocol (HTTPS and TCP)

Some settings for the log handler will not be exposed to the user via
this mechanism. For example, threading (enabled).

Parameters for the items listed above should be configurable through
the Configure-Tower-in-Tower interface.

One note on configuring Host and Port: When entering URL it is customary to
include port number, like `https://localhost:4399/foo/bar`. So for the convenience
of users, when connection type is HTTPS, we allow entering hostname as a URL
with port number and thus ignore Port field. In other words, Port field is
optional in this case. On the other hand, TCP and UDP connections are determined
by `<hostname, port number>` tuple rather than URL. So in the case of TCP/UDP
connection, Port field is supposed to be provided and Host field is supposed to
contain hostname only. If instead a URL is entered in Host field, its hostname
portion will be extracted as the actual hostname.


# Acceptance Criteria Notes

**Connection:** Testers need to replicate the documented steps for setting up
and connecting with a destination log aggregation service, if that is
an officially supported service. That will involve 1) configuring the
settings, as documented, 2) taking some action in Tower that causes a log
message from each type of data logger to be sent and 3) verifying that
the content is present in the log aggregation service.

**Schema:** After the connection steps are completed, a tester will need to create
an index. We need to confirm that no errors are thrown in this process.
It also needs to be confirmed that the schema is consistent with the
documentation. In the case of Splunk, we need basic confirmation that
the data is compatible with the existing app schema.

**Tower logs:** Formatting of Traceback message is a known issue in several
open-source log handlers, so we should confirm that server errors result
in the log aggregator receiving a well-formatted multi-line string
with the traceback message.

Log messages should be sent outside of the
request-response cycle. For example, Loggly examples use
rsyslog, which handles these messages without interfering with other
operations. A timeout on the part of the log aggregation service should
not cause Tower operations to hang.
