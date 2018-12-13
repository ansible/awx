# Migrating Data Between AWX Installations

## Introduction

Upgrades using Django migrations are not expected to work in AWX.  As a result, to upgrade to a new version, it is necessary to export resources from the old AWX node and import them into a freshly-installed node with the new version.  The recommended way to do this is to use the tower-cli send/receive feature.

This tool does __not__ support export/import of the following:
* Logs/history
* Credential passwords
* LDAP/AWX config

### Install & Configure Tower-CLI

In terminal, pip install tower-cli (if you do not have pip already, install [here](https://pip.pypa.io/en/stable/installing/)):
```
$ pip install --upgrade ansible-tower-cli
```

The AWX host URL, user, and password must be set for the AWX instance to be exported:
```
$ tower-cli config host http://<old-awx-host.example.com>
$ tower-cli config username <user>
$ tower-cli config password <pass>
```

For more information on installing tower-cli look [here](http://tower-cli.readthedocs.io/en/latest/quickstart.html).


### Export Resources

Export all objects

```$ tower-cli receive --all > assets.json```



### Teardown Old AWX

Clean up remnants of the old AWX install:

```docker rm -f $(docker ps -aq)```     # remove all old awx containers

```make clean-ui```              # clean up ui artifacts


### Install New AWX version

If you are installing AWX as a dev container, pull down the latest code or version you want from GitHub, build
the image locally, then start the container

```
git pull                                        # retrieve latest AWX changes from repository
make docker-compose-build                       # build AWX image
make docker-compose                             # run container
```
For other install methods, refer to the [Install.md](https://github.com/ansible/awx/blob/devel/INSTALL.md). 
 

### Import Resources


Configure tower-cli for your new AWX host as shown earlier.  Import from a JSON file named assets.json

```
$ tower-cli config host http://<new-awx-host.example.com>
$ tower-cli config username <user>
$ tower-cli config password <pass>
$ tower-cli send assets.json
```

--------------------------------------------------------------------------------

## Additional Info

If you have two running AWX hosts, it is possible to copy all assets from one instance to another

```$ tower-cli receive --tower-host old-awx-host.example.com --all | tower-cli send --tower-host new-awx-host.example.com```



#### More Granular Exports:

Export all credentials

```$ tower-cli receive --credential all > credentials.json```
> Note: This exports the credentials with blank strings for passwords and secrets

Export a credential named "My Credential"

```$ tower-cli receive --credential "My Credential"```

#### More Granular Imports:


You could import anything except an organization defined in a JSON file named assets.json

```$ tower-cli send --prevent organization assets.json```
