# AWX-PF

## Requirements
- node 10.x LTS, npm 6.x LTS, make, git

## Development
The API development server will need to be running. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

```shell
# install
npm --prefix=awx/ui_next install

# Start the ui development server. While running, the ui will be reachable
# at https://127.0.0.1:3001 and updated automatically when code changes.
npm --prefix=awx/ui_next start
```

### Using an External Server
If you normally run awx on an external host/server (in this example, `awx.local`),
you'll need use the `TARGET` environment variable when starting the ui development
server:

```shell
TARGET='https://awx.local:8043' npm --prefix awx/ui_next start
```

## Testing
```shell
# run code formatting check
npm --prefix awx/ui_next run prettier-check

# run lint checks
npm --prefix awx/ui_next run lint

# run all unit tests
npm --prefix awx/ui_next run test

# run a single test (in this case the login page test):
npm --prefix awx/ui_next test -- src/screens/Login/Login.test.jsx

# start the test watcher and run tests on files that you've changed
npm --prefix awx/ui_next run test-watch
```
#### Note:
- Once the test watcher is up and running you can hit `a` to run all the tests.
- All commands are run on your host machine and not in the api development containers.


## Adding Dependencies
```shell
# add an exact development or build dependency
npm --prefix awx/ui_next install --save-dev --save-exact dev-package@1.2.3

# add an exact production dependency
npm --prefix awx/ui_next install --save --save-exact prod-package@1.23

# add the updated package.json and package-lock.json files to scm
git add awx/ui_next_next/package.json awx/ui_next_next/package-lock.json
```

## Removing Dependencies
```shell
# remove a development or build dependency
npm --prefix awx/ui_next uninstall --save-dev dev-package

# remove a production dependency
npm --prefix awx/ui_next uninstall --save prod-package
```

## Building for Production
```shell
# built files are placed in awx/ui_next/build
npm --prefix awx/ui_next run build
```

## CI Container

To run:

```shell
cd awx/awx/ui_next
docker build -t awx-ui-next .
docker run --name tools_ui_next_1 --network tools_default --link 'tools_awx_1:awx' -e TARGET="https://awx:8043" -p '3001:3001' --rm -v $(pwd)/src:/ui_next/src awx-ui-next
```

**Note:** This is for CI, test systems, zuul, etc. For local development, see [usage](https://github.com/ansible/awx/blob/devel/awx/ui_next/README.md#Development)
