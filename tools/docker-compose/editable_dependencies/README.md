# Editable dependencies in AWX Docker Compose Development Environment

This folder contains the symlink to editable dependencies for AWX

During the bootstrap of awx development environment we will try to crawl through the symlinks and mount (the source of the symlink) to `tools_awx_` containers and `init_awx` containers than install all the dependencies in editable mode

## How to enable/disable editable dependnecies

### Enable

Set `EDITABLE_DEPENDENCIES=true` either as an Environment Variable with before invoking `make docker-compose`

```bash
export EDITABLE_DEPENDENCIES=true
```

or during invocation of `make docker-compose`

```bash

EDITABLE_DEPENDENCIES=true make docker-compose
```

will cause the `make docker-compose-source` to template out docker-compose file with editable dependencies.

### Disable

To disable editable dependency simply `unset EDITABLE_DEPENDENCIES`

## How to add editable dependencies

Adding symlink to the directory that contains the source of the editable dependencies will cause the dependency to be mounted and installed in the docker-compose development environment.

Both relative path or absolute path will work

### Examples

I have `awx` checked out at `~/projects/src/github.com/TheRealHaoLiu/awx`
I have `django-ansible-base` checked out at `~/projects/src/github.com/TheRealHaoLiu/ansible-runner`

From root of AWX project `~/projects/src/github.com/TheRealHaoLiu/awx`

I can either do

```bash
ln -s ~/projects/src/github.com/TheRealHaoLiu/ansible-runner tools/docker-compose/editable_dependencies/
```

or

```bash
ln -s ../ansible-runner tools/docker-compose/editable_dependencies/
```

## How to remove editable dependencies

Simply removing the symlink will probably cause problem and the volume `tools_awx_var_lib` need to be deleted with

```bash
docker volume rm tools_awx_var_lib
```

TODO(TheRealHaoLiu): bear proof this? maybe just always delete tools_awx_var_lib?
