### Table of Contents

1. [Requirements](#requirements)
2. [Usage](#usage)
3. [Testing](#testing)
4. [Adding new dependencies](#deps)
5. [Using libraries without modular exports/depedency management](#polyfill)
6. [Environment configuration](#environment)
7. [NPM scripts](#scripts)

### <a name="requirements">Requirements</a>

* A supported version of node + npm, constrained in `package.json`.
```json
"engines": {
  "node": "^6.3.1",
  "npm": "^3.10.3"
}
```
* C/C++ compiler tools, like GCC. Bundled in [Command Line Tools for Xcode](https://developer.apple.com/xcode/)
* [node-gyp](https://github.com/nodejs/node-gyp)
```
npm install -g node-gyp
```

### <a name="usage">Usage</a>

The following Makefile targets are available from the root dir of `ansible-tower`

**Native Docker**
Specify the container ID of a `tools_tower` instance.
`DOCKER_CID=containerID make ui-docker-cid`

**Docker Machine**
Specify the name of a docker-machine.
`DOCKER_MACHINE_NAME=default make ui-docker-machine`

Build a minified/uglified **release candidate**
`make ui-release`

### <a name="testing">Testing</a>

Run unit tests locally, poll for changes to both source and test files, launch tests in supported browser engines:
`make ui-test`

Run unit tests in a CI environment (Jenkins)
`make ui-test-ci`

Run Protractor (E2E) tests in Saucelabs:
`make ui-test-saucelabs`

### <a name="deps">Adding new dependencies</a>

From the root dir of `ansible-tower`:

#### Add/update a bundled vendor dependency
1. `npm install --prefix awx/ui --save some-frontend-package@1.2.3`
2. Add `'some-package'` to `var vendorFiles` in `./grunt-tasks/webpack.js`
3. `npm  --prefix awx/ui shrinkwrap` to freeze current dependency resolution

#### Add/update a dependecy in the build/test pipeline:
1. `npm install --prefix awx/ui --save-dev some-toolchain-package@1.2.3`
2. `npm  --prefix awx/ui shrinkwrap` to freeze current dependency resolution

### <a name="polyfill">Polyfills, shims, patches</a>

The Webpack pipeline will prefer module patterns in this order: CommonJS, AMD, UMD. For a comparison of supported patterns, refer to [https://webpack.github.io/docs/comparison.html](Webpack's docs).

Some javascript libraries do not export their contents as a module, or depend on other third-party components. If the library maintainer does not wrap their lib in a factory that provides a CommonJS or AMD module, you will need to provide dependencies with a shim.

1. Shim implicit dependencies using Webpack's [ProvidePlugin](https://github.com/webpack/webpack/blob/006d59500de0493c4096d5d4cecd64eb12db2b95/lib/ProvidePlugin.js). Example:

```js
// Tower source code depends on the lodash library being available as _
_.uniq([1,2,3,1]) // will throw error undefined
```
```js
// webpack.config.js
plugins: [
  new webpack.ProvidePlugin({
      '_': 'lodash',
  })
]
```
```js
// the following requirement is inserted by webpack at build time
var _ = require('lodash');
_.uniq([1,2,3,1])
```

2. Use [`imports-loader`](https://webpack.github.io/docs/shimming-modules.html#importing) to inject requirements into the namespace of vendor code at import time. Use [`exports-loader`](https://webpack.github.io/docs/shimming-modules.html#exporting) to conventionally export vendor code lacking a conventional export pattern.
3.  [Apply a functional patch](https://gist.github.com/leigh-johnson/070159d3fd780d6d8da6e13625234bb3). A webpack plugin is the correct choice for a functional patch if your patch needs to access events in a build's lifecycle. A webpack loader is preferable if you need to compile and export a custom pattern of library modules.
4.  [Submit patches to libraries without modular exports](https://github.com/leigh-johnson/ngToast/commit/fea95bb34d27687e414619b4f72c11735d909f93) - the internet will thank you

Some javascript libraries might only get one module pattern right.

### <a name="environment">Environment configuration</a> - used in development/test builds

Build tasks are parameterized with environment variables.

`package.json` contains default environment configuration. When `npm run myScriptName` is executed, these variables will be exported to your environment with the prefix `npm_package_config_`. For example, `my_variable` will be exported to `npm_package_config_my_variable`.

Environment variables can accessed in a Javascript via `PROCESS.env`.

``` json
  "config": {
    "django_port": "8013",
    "websocket_port": "8080",
    "django_host": "0.0.0.0"
  }
```

Example usage in `npm run build-docker-machine`:

```bash
docker-machine ssh $DOCKER_MACHINE_NAME -f -N -L ${npm_package_config_websocket_port}:localhost:${npm_package_config_websocket_port}; ip=$(docker-machine ip $DOCKER_MACHINE_NAME); echo npm set ansible-tower:django_host ${ip}; grunt dev
```

Example usage in an `npm test` script target:

```bash
npm_package_config_websocket_port=mock_websocket_port npm_package_config_django_port=mock_api_port npm_package_config_django_host=mock_api_host npm run test:someMockIntegration
```

You'll usually want to pipe and set vars prior to running a script target:
```bash
npm set ansible-tower:websocket_host ${mock_host}; npm run script-name
```

### <a name="scripts">NPM Scripts</a>

Examples:
```json
  "scripts": {
    "pretest": "echo I run immediately before 'npm test' executes",
    "posttest": "echo I run immediately after 'npm test' exits",
    "test": "karma start karma.conf.js"
  }
```

`npm test` is an alias for `npm run test`. Refer to [script field docs](https://docs.npmjs.com/misc/scripts) for a list of other runtime events.

