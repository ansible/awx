# AWX-UI

## Requirements
- node >= 16.13.1, npm >= 8.x make, git

## Development
The API development server will need to be running. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

```shell
# install
npm --prefix=awx/ui install

# Start the ui development server. While running, the ui will be reachable
# at https://127.0.0.1:3001 and updated automatically when code changes.
npm --prefix=awx/ui start
```

### Build for the Development Containers
If you just want to build a ui for the container-based awx development
environment and do not need to work on the ui code, use these make targets:

```shell
# The ui will be reachable at https://localhost:8043 or
# http://localhost:8013
make ui-devel 

# clean up 
make clean-ui
```

### Using an External Server
If you normally run awx on an external host/server (in this example, `awx.local`),
you'll need use the `TARGET` environment variable when starting the ui development
server:

```shell
TARGET='https://awx.local:8043' npm --prefix awx/ui start
```

## Testing
```shell
# run code formatting check
npm --prefix awx/ui run prettier-check

# run lint checks
npm --prefix awx/ui run lint

# run all unit tests
npm --prefix awx/ui run test

# run a single test (in this case the login page test):
npm --prefix awx/ui test -- src/screens/Login/Login.test.jsx

# start the test watcher and run tests on files that you've changed
npm --prefix awx/ui run test-watch

# start the tests and get the coverage report after the tests have completed
npm --prefix awx/ui run test -- --coverage
```
#### Note:
- Once the test watcher is up and running you can hit `a` to run all the tests.
- All commands are run on your host machine and not in the api development containers.


## Updating Dependencies
It is not uncommon to run the ui development tooling outside of the awx development
container. That said, dependencies should always be modified from within the
container to ensure consistency.

```shell
# make sure the awx development container is running and open a shell
docker exec -it tools_awx_1 bash

# start with a fresh install of the current dependencies
(tools_awx_1)$ make clean-ui && npm --prefix=awx/ui ci

# add an exact development dependency
(tools_awx_1)$ npm --prefix awx/ui install --save-dev --save-exact dev-package@1.2.3

# add an exact production dependency
(tools_awx_1)$ npm --prefix awx/ui install --save --save-exact prod-package@1.23

# remove a development dependency
(tools_awx_1)$ npm --prefix awx/ui uninstall --save-dev dev-package

# remove a production dependency
(tools_awx_1)$ npm --prefix awx/ui uninstall --save prod-package

# exit the container
(tools_awx_1)$ exit

# add the updated package.json and package-lock.json files to scm
git add awx/ui/package.json awx/ui/package-lock.json
```
#### Note:
- Building the ui can use up a lot of resources. If you're running docker for mac or similar
virtualization, the default memory limit may not be enough and you should increase it.

## Building for Production
```shell
# built files are placed in awx/ui/build
npm --prefix awx/ui run build
```

## CI Container

To run:

```shell
cd awx/awx/ui
docker build -t awx-ui .
docker run --name tools_ui_1 --network _sources_default --link 'tools_awx_1:awx' -e TARGET="https://awx:8043" -p '3001:3001' --rm -v $(pwd)/src:/ui/src awx-ui
```

**Note:** This is for CI, test systems, zuul, etc. For local development, see [usage](https://github.com/ansible/awx/blob/devel/awx/ui/README.md#Development)
