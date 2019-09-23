# AWX UI

## Requirements
- node.js 10.x LTS
- npm >=6.x
- bzip2, gcc-c++, git, make

## Development
The API development server will need to be running. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

```shell
# Build ui for the devel environment - reachable at https://localhost:8043
make ui-devel

# Alternatively, start the ui development server. While running, the ui will be reachable
# at https://localhost:3000 and updated automatically when code changes.
make ui-docker

# When using docker machine, use this command to start the ui development server instead.
DOCKER_MACHINE_NAME=default make ui-docker-machine
```

## Development with an external server
If you normally run awx on an external host/server (in this example, `awx.local`),
you'll need to reconfigure the webpack proxy slightly for `make ui-docker` to
work:

```javascript
/awx/settings/development.py
+
+CSRF_TRUSTED_ORIGINS = ['awx.local:8043']

awx/ui/build/webpack.watch.js
-        host: '127.0.0.1',
+        host: '0.0.0.0',
+        disableHostCheck: true,

/awx/ui/package.json
@@ -7,7 +7,7 @@
   "config": {
     ...
+    "django_host": "awx.local"
   },
```

## Testing
```shell
# run linters
make jshint

# run unit tests
make ui-test-ci

# run e2e tests - see awx/ui/test/e2e for more information
npm --prefix awx/ui run e2e
```
**Note**: Unit tests are run on your host machine and not in the development containers.

## Adding dependencies
```shell
# add an exact development or build dependency
npm install --prefix awx/ui --save-dev --save-exact dev-package@1.2.3

# add an exact production dependency
npm install --prefix awx/ui --save --save-exact prod-package@1.23

# add the updated package.json and package-lock.json files to scm
git add awx/ui/package.json awx/ui/package-lock.json
```

## Removing dependencies
```shell
# remove a development or build dependency
npm uninstall --prefix awx/ui --save-dev dev-package

# remove a production dependency
npm uninstall --prefix awx/ui --save prod-package
```

## Building for Production
```shell
# built files are placed in awx/ui/static
make ui-release
```

## Internationalization
Application strings marked for translation are extracted and used to generate `.pot` files using the following command:
```shell
# extract strings and generate .pot files
make pot
```
To include the translations in the development environment, we compile them prior to building the ui:
```shell
# remove any prior ui builds
make clean-ui

# compile the .pot files to javascript files usable by the application
make languages

# build the ui with translations included
make ui-devel
```
**Note**: Python 3.6 is required to compile the `.pot` files.
