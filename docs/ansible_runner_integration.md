## Ansible Runner Integration Overview

Much of the code in AWX around ansible and ansible-playbook invocation interacting has been removed and put into the project ansible-runner. AWX now calls out to ansible-runner to invoke ansible and ansible-playbook.

### Lifecycle

In AWX, a task of a certain job type is kicked off (i.e. RunJob, RunProjectUpdate, RunInventoryUpdate, etc) in tasks.py. A temp directory is build to house ansible-runner parameters (i.e. envvars, cmdline, extravars, etc.). The temp directory is filled with the various concepts in AWX (i.e. ssh keys, extra varsk, etc.). The code then builds a set of parameters to be passed to the ansible-runner python module interface, `ansible-runner.interface.run()`. This is where AWX passes control to ansible-runner. Feedback is gathered by AWX via callbacks and handlers passed in.

The callbacks and handlers are:
* event_handler: Called each time a new event is created in ansible runner. AWX will disptach the event to rabbitmq to be processed on the other end by the callback receiver.
* cancel_callback: Called periodically by ansible runner. This is so that AWX can inform ansible runner if the job should be canceled or not. 
* finished_callback: Called once by ansible-runner to denote that the process that was asked to run is finished. AWX will construct the special control event, `EOF`, with an associated total number of events that it observed.
* status_handler: Called by ansible-runner as the process transitions state internally. AWX uses the `starting` status to know that ansible-runner has made all of its decisions around the process that it will launch. AWX gathers and associates these decisions with the Job for historical observation.

### Debugging

If you want to debug ansible-runner then set `AWX_CLEANUP_PATHS=False`, run a job, observe the job's `AWX_PRIVATE_DATA_DIR` property, and go the node where the job was executed and inspect that directory.

If you want to debug the process that ansible-runner invoked (i.e. ansible or ansible-playbook) then observe the job's job_env, job_cwd, and job_args parameters. 
