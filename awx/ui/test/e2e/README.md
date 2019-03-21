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
