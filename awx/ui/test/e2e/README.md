## AWX E2E
#### Introduction
This is an automated functional test suite for the front end.

#### Technology
The tests are written in Node.js and use the [Nightwatch](https://github.com/nightwatchjs/nightwatch) test runner.

#### Requirements
- node.js 8.x LTS
- npm 5.x LTS

#### Installation
A successful invocation of `make ui-devel` will prepare your environment with the software
dependencies required to run these tests.

#### Configuration
Three inputs are required:

*AWX_E2E_URL*

> A valid url for a running AWX instance that is reachable by your machine. This can be your local
development instance or other awx instance. Defaults to *https://localhost:8043*.

*AWX_E2E_USERNAME*

> A valid admin username for the target awx instance. Defaults to *awx-e2e*.

*AWX_E2E_PASSWORD*

> A valid password for the admin. Defaults to *password*.

These inputs can be provided as environment variables or defined as default values in [settings](settings.js).
The settings file also contains all other configurable input values to this test suite.

#### Usage
```shell
# run all of the tests with a live browser
npm --prefix awx/ui run e2e

# run a subset of the tests
npm --prefix awx/ui run e2e -- --filter="test-credentials*"
```
**Note:**
- Use `npm --prefix awx/ui run e2e -- --help` to see additional usage information for the test runner.
- All example commands in this document assume that you are working from the root directory of the awx project.

#### File Overview
All nightwatch.js tests are present in the `tests` directory. When writing 
these tests, you may import needed functions from [fixtures.js](fixtures.js), which provides a convenient way to create resources needed for tests 
via API, which might include organizations, users, and job templates.

The `commands` directory provides extra functions for the client object in 
nightwatch.js tests. These functions are automatically made available for use by the
client object. For more information on these functions and how to 
create your own, refer to the [nightwatch.js documentation on custom commands]
(http://nightwatchjs.org/guide/#writing-custom-commands).

#### CI Container Debugging
To reproduce test runs in the ci container locally, you'll want to use the provided `docker-compose.yml` file as well as some override files
to link the containers to your development environment.

```shell
# docker-compose.yml - the default configuration for ci
# docker-compose.devel-override.yml - link ci container to development containers
# docker-compose.debug-override.hml - make chrome and firefox nodes accessible over vnc
docker-compose \
  -f awx/ui/test/e2e/cluster/docker-compose.yml \
  -f awx/ui/test/e2e/cluster/docker-compose.devel-override.yml \
  -f awx/ui/test/e2e/cluster/docker-compose.debug-override.yml \
  run -e AWX_E2E_URL=https://awx:8043 -e AWX_E2E_USERNAME=awx -e AWX_E2E_PASSWORD=password e2e '--filter=*smoke*'
```

Once running, you can connect to nodes over vnc at `vnc://localhost:5900` and `vnc://localhost:5901`.

**Note:**
- On macOS, safari has a built-in vnc client and you should be able to use these urls directly.
- On linux, you'll need to have your favorite vnc client ready (like `tigervnc`). Depending on the vnc client you use, you may need to visit `localhost:5900` and input the password `secret` separately.
- For the chrome and firefox nodes, the development container instance of awx is mapped to hostname `awx` (https://awx:8043)

#### Known Issues
- ```2019-07-30 13:35:47.883 chromedriver[66032:1305791] pid(66032)/euid(501) is calling TIS/TSM in non-main thread environment, ERROR : This is NOT allowed. Please call TIS/TSM in main thread!!!```
 Specific to MacOS High Sierra. More here: https://github.com/processing/processing/issues/5462
