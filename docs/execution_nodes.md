# Adding execution nodes to AWX

Stand-alone execution nodes can be added to run alongside the Kubernetes deployment of AWX. These machines will not be a part of the AWX Kubernetes cluster. The control nodes running in the cluster will connect and submit work to these machines via Receptor. The machines be registered in AWX as type "execution" instances, meaning they will only be used to run AWX Jobs (i.e. they will not dispatch work or handle web requests as control nodes do).

Hop nodes can be added to sit between the control plane of AWX and stand alone execution nodes. These machines will not be a part of the AWX Kubernetes cluster. The machines will be registered in AWX as node type "hop", meaning they will only handle inbound / outbound traffic for otherwise unreachable nodes in a different or more strict network. 

Below is an example of an AWX Task pod with two excution nodes. Traffic to execution node 2 flows through a hop node that is setup between it and the control plane.

```
                                                     AWX TASK POD
                                                   ┌──────────────┐
                                                   │              │
                                                   │ ┌──────────┐ │
┌─────────────────┐   ┌─────────────────┐          │ │ awx-task │ │
│execution node 2 ├──►│     hop node    │◄────┐    │ ├──────────┤ │
└─────────────────┘   ├─────────────────┤     ├────┼─┤ awx-ee   │ │
                      │ execution node 1│◄────┘    │ └──────────┘ │
                      └─────────────────┘ Receptor │              | 
                                            TCP    └──────────────┘
                                           Peers                 
                                                   
```

## Overview
Adding an execution instance involves a handful of steps:

1. [Start a machine that is accessible from the k8s cluster (Red Hat family of operating systems are supported)](#start-machine)
2. [Create a new AWX Instance with `hostname` being the IP or DNS name of your remote machine.](#create-instance-in-awx)
3. [Download the install bundle for this newly created instance.](#download-the-install-bundle)
4. [Run the install bundle playbook against your remote machine.](#run-the-install-bundle-playbook)
5. [Wait for the instance to report a Ready state. Now jobs can run on that instance.](#wait-for-instance-to-be-ready)


### Start machine

Bring a machine online with a compatible Red Hat family OS (e.g. RHEL 8 and 9). This machines needs a static IP, or a resolvable DNS hostname that the AWX cluster can access. If the listerner_port is defined, the machine will also need an available open port to establish inbound TCP connections on (e.g. 27199).

In general the more CPU cores and memory the machine has, the more jobs that can be scheduled to run on that machine at once. See https://docs.ansible.com/automation-controller/4.2.1/html/userguide/jobs.html#at-capacity-determination-and-job-impact for more information on capacity.


### Create instance in AWX

Use the Instance page or `api/v2/instances` endpoint to add a new instance.
- `hostname` ("Name" in UI) is the IP address or DNS name of your machine.
- `node_type` is "execution" or "hop"
- `node_state` is "installed"
- `listener_port` is an open port on the remote machine used to establish inbound TCP connections. Defaults to null.
- `peers` is a list of instance hostnames to connect outbound to.
- `peers_from_control_nodes` boolean, if True, control plane nodes will automatically peer to this instance.

Below is a table of configuartions for the [diagram](#adding-execution-nodes-to-awx) above.

| instance name    | listener_port | peers_from_control_nodes | peers       |
|------------------|---------------|-------------------------|--------------|
| execution node 1 | 27199         | true                    | []           |
| hop node         | 27199         | true                    | []           |
| execution node 2 | null          | false                   | ["hop node"] |

Listener port needs to be set if peers_from_control_nodes is enabled or the instance is a peer.


### Download the install bundle

On the Instance Details page, click Install Bundle and save the tar.gz file to your local computer and extract contents. Alternatively, make a GET request to `api/v2/instances/{id}/install_bundle` and save the binary output to a tar.gz file.


### Run the install bundle playbook

In order for AWX to make proper TCP connections to the remote machine, a few files need to in place. These include TLS certificates and keys, a certificate authority, and a proper Receptor configuration file. To facilitate that these files will be in the right location on the remote machine, the install bundle includes an install_receptor.yml playbook.

The playbook requires the Receptor collection which can be obtained via

`ansible-galaxy collection install -r requirements.yml`

Modify `inventory.yml`. Set the `ansible_user` and any other ansible variables that may be needed to run playbooks against the remote machine.

`ansible-playbook -i inventory.yml install_receptor.yml` to start installing Receptor on the remote machine.

Note, the playbook will enable the [Copr ansible-awx/receptor repository](https://copr.fedorainfracloud.org/coprs/ansible-awx/receptor/) so that Receptor can be installed.


### Wait for instance to be Ready

Wait a few minutes for the periodic AWX task to do a health check against the new instance. The instances endpoint or page should report "Ready" status for the instance. If so, jobs are now ready to run on this machine!


## Removing instances

You can remove an instance by clicking "Remove" in the Instances page, or by setting the instance `node_state` to "deprovisioning" via the API.

## Troubleshooting

### Fact cache not working

Make sure the system timezone on the execution node matches `settings.TIME_ZONE` (default is 'UTC') on AWX.
Fact caching relies on comparing modified times of artifact files, and these modified times are not timezone-aware. Therefore, it is critical that the timezones of the execution nodes match AWX's timezone setting.

To set the system timezone to UTC

`ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime`

### Permission denied errors

Jobs may fail with the following error
```
"msg":"exec container process `/usr/local/bin/entrypoint`: Permission denied"
```
or similar

For RHEL based machines, this could due to SELinux that is enabled on the system.

You can pass these `extra_settings` container options to override SELinux protections.

`DEFAULT_CONTAINER_RUN_OPTIONS = ['--network', 'slirp4netns:enable_ipv6=true', '--security-opt', 'label=disable']`