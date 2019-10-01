# TACACS+
[Terminal Access Controller Access-Control System Plus (TACACS+)](https://en.wikipedia.org/wiki/TACACS) is a protocol developed by Cisco to handle remote authentication and related services for networked access control through a centralized server. In specific, TACACS+ provides authentication, authorization and accounting (AAA) services. Ansible Tower currently utilizes its authentication service.

TACACS+ is configured by Tower configuration and is available under `/api/v2/settings/tacacsplus/`. Here is a typical configuration with every configurable field included:
```
{
    "TACACSPLUS_HOST": "127.0.0.1",
    "TACACSPLUS_PORT": 49,
    "TACACSPLUS_SECRET": "secret",
    "TACACSPLUS_SESSION_TIMEOUT": 5,
    "TACACSPLUS_AUTH_PROTOCOL": "ascii"
}
```
Each field is explained below:

| Field Name                   | Field Value Type    | Field Value Default | Description                                                        |
|------------------------------|---------------------|---------------------|--------------------------------------------------------------------|
| `TACACSPLUS_HOST`            | String              | '' (empty string)   | Hostname of TACACS+ server. Empty string disables TACACS+ service. |
| `TACACSPLUS_PORT`            | Integer             | 49                  | Port number of TACACS+ server.                                     |
| `TACACSPLUS_SECRET`          | String              | '' (empty string)   | Shared secret for authenticating to TACACS+ server.                |
| `TACACSPLUS_SESSION_TIMEOUT` | Integer             | 5                   | TACACS+ session timeout value in seconds.                          |
| `TACACSPLUS_AUTH_PROTOCOL`   | String with choices | 'ascii'             | The authentication protocol used by TACACS+ client (choices are `ascii` and `pap`).                |

Under the hood, Tower uses [open-source TACACS+ python client](https://github.com/ansible/tacacs_plus) to communicate with the remote TACACS+ server. During authentication, Tower passes username and password to TACACS+ client, which packs up auth information and sends it to the TACACS+ server. Based on what the server returns, Tower will invalidate login attempt if authentication fails. If authentication passes, Tower will create a user if she does not exist in database, and log the user in.

## Test Environment Setup

The suggested TACACS+ server for testing is [shrubbery TACACS+ daemon](http://www.shrubbery.net/tac_plus/). It is supposed to run on a CentOS machine. A verified candidate is CentOS 6.3 AMI in AWS EC2 Community AMIs (search for `CentOS 6.3 x86_64 HVM - Minimal with cloud-init aws-cfn-bootstrap and ec2-api-tools`). Note that it is required to keep TCP port 49 open, since it's the default port used by the TACACS+ daemon.

We provide [a playbook](https://github.com/jangsutsr/ansible-role-tacacs) to install a working TACACS+ server. Here is a typical test setup using the provided playbook:

1. In AWS EC2, spawn the CentOS 6 machine.
2. In Tower, create a test project using the stand-alone playbook inventory.
3. In Tower, create a test inventory with the only host to be the spawned CentOS machine.
4. In Tower, create and run a job template using the created project and inventory with parameters setup as below:

![Example tacacs+ setup jt parameters](../img/auth_tacacsplus_1.png?raw=true)

The playbook creates a user named 'tower' with ascii password default to 'login' and modifiable by `extra_var` `ascii_password` and pap password default to 'papme' and modifiable by `extra_var` `pap_password`. In order to configure TACACS+ server to meet custom test needs, we need to modify server-side file `/etc/tac_plus.conf` and `sudo service tac_plus restart` to restart the daemon. Details on how to modify config file can be found [here](http://manpages.ubuntu.com/manpages/xenial/man5/tac_plus.conf.5.html).


## Acceptance Criteria

* All specified Tower configuration fields should be shown and configurable as documented.
* A user defined by the TACACS+ server should be able to log into Tower.
* User not defined by TACACS+ server should not be able to log into Tower via TACACS+.
* A user existing in TACACS+ server but not in Tower should be created after the first successful log in.
* TACACS+ backend should stop an authentication attempt after configured timeout and should not block the authentication pipeline in any case.
* If exceptions occur on TACACS+ server side, the exception details should be logged in Tower, and Tower should not authenticate that user via TACACS+.
