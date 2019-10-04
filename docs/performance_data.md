Performance Data
================

AWX has the ability to collect performance data on job runs.

The following data is collected periodically (with a default interval of every 0.25 seconds):
* CPU usage
* Memory usage
* PID count

The data is stored under `/var/log/tower/playbook_profiling`. A new folder is created for each job run. The folder's name is set to the job's ID.

Performance data collection is not enabled by default. To enable performance data collection on all jobs, set AWX_RESOURCE_PROFILING_ENABLED to true.

The frequency with which data is collected can be set using:
* AWX_RESOURCE_PROFILING_CPU_POLL_INTERVAL
* AWX_RESOURCE_PROFILING_MEMORY_POLL_INTERVAL
* AWX_RESOURCE_PROFILING_PID_POLL_INTERVAL
