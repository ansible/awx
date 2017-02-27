# UI BUILD SYSTEM

### Table of Contents

1. [Care and Keeping of NodeJS + NPM](#nodejs-and-npm)
    1. [Pin NodeJS & NPM versions](#pin-nodejs-npm-versions)
    2. [Use NVM to manage multple Node/NPM installations](#use-nvm)
    3.. [Add, incremenet, remove a package](#add-upgrade-remove-npm-package)
    4. [dependency, devDependency, or optionalDependency?](#npm-dependency-types)

2. [Webpack](#webpack)
    1. [What does Webpack handle?](#webpack-what-do)
    2. [Add / remove a vendor module](#add-upgrade-remove-vendor-module)
    3. [Strategies: loading a module](#loading-modules)
    4. [Strategies: exposing a module to application code](#exposing-modules)


3. [Grunt](#grunt)
    1. [What does Grunt handle?](#grunt-what-do)
    2. [Add / remove a Grunt task](#add-remove-upgrade-grunt-task)
    3. [Task concurrency & process lifecycles](#grunt-task-concurrency)

4. [Karma](#karma)
    1. [Developer configuration](#karma-developer-config)
    2. [CI configuration](#karma-ci-config)

5. [Interfaces & Environments](#interfaces-and-environments)
    1. [NPM script targets](#npm-scripts)
    2. [Makefile targets](#make-targets)
    3. [NPM config variables](#npm-config-variables)
    4. [Other environment variables](#environment-variables)

6. References / Resources


# <a name="nodejs-and-npm">Care and Keeping of NodeJS + NPM</a>
## <a name="pin-nodejs-npm-versions">Pin NodeJS & NPM versions</a>

NodeJS began packaging their releases with a bundled version of NPM. Occasionally, the version of NPM that ships with a given NodeJS release can be unstable. For example, the v6 LTS of Node shipped with a version of NPM that introduced a regression that broke module installation for any package with platform-specific dependencies.

For this reason, it's strongly advised to pin development environments, CI, and release pipelines to vetted releases of NodeJS + NPM.

Pinned versions are best expressed through the engine field in `package.json`.

```json
 "engines": {
    "node": "^6.3.1",
    "npm": "=3.10.3"
  }
  ```

## <a name="use-nvm">Use NVM to manage multiple NodeJS + NPM installations</a>

A system installation of Node raises *many* challenges on a development or shared system: user permissions, shared (global) modules, and installation paths for multiple versions. `nvm` is a light executable that addresses all of these issues. In the context of Tower, we use nvm to quickly switch between versions of NodeJS + NPM. 

Version support per Tower release
3.0.* - NodeJS v0.12.17 & NPM v2.15.1
3.1.* - NodeJS 6.3.1 * & NPM 3.10.3

* [nvm installation guide](https://github.com/creationix/nvm#installation)
* [additional shell integrations](https://github.com/creationix/nvm#deeper-shell-integration)

```bash
$ nvm install 6.3
$ nvm use 6.3

```

## <a name="add-upgrade-remove-npm-package">Adding, incrementing, removing packages via NPM</a>

The Tower package utilizes an `npm-shrinkwrap.json` file to freeze dependency resolution. When `npm install` runs, it will prefer to resolve dependencies as frozen in the shrinkwrap file before it ingests versions in `package.json`. To update the shrinkwrap file with a new dependency, pass the `--save` argument e.g. `npm install fooify@1.2.3 --save`. 

*Do not run `npm shrinkwrap` when add/updating dependencies*. This will re-generate the entire conflict resolution tree, which will churn over time. Instead, depend on `--save`, `--save-dev` and `--save-optional` to create/update the shrinkwrapped package.

## <a name="npm-dependency-types">What's a dependency, devDependency, or optionalDependency</a>

`dependency` - Bundled in the Tower product. Customer-facing.
`devDependency` - Used in the development, build, and release pipelines
`optionalDependency` - Platform-specific dependencies, or dependencies which should not cause `npm install` to exit with an error if these modules fail to install. 

# <a name="webpack">Webpack</a>

## <a name="webpack-what-do">What does Webpack handle?</a>

Webpack ingests our vendor and application modules, and outputs bundled code optimized for development or production. Configuration lives in `webpack.config.js`.

Webpack is a highly pluggable framework ([list of vetted plugins](https://webpack.github.io/docs/list-of-plugins.html)) We make use of the following plugins:

* [ProvidePlugin](https://webpack.github.io/docs/list-of-plugins.html#provideplugin) - automatically loads and exports a module into specified namespace. A modular approach to loading modules that you would otherwise have to load into global namespace. Example:

```javascript
// webpack.config.js
plugins: {
    new webpack.ProvidePlugin({
        '$': 'jquery',
    })
}
```

```javascript
// some-application-module.js
// the following code:
$('.my-thingy').click();

// is transformed into:
var $ = require('jquery');
$('.my-thingy').click();
```

* [CommonChunksPlugin](https://webpack.github.io/docs/list-of-plugins.html#commonschunkplugin) - a [chunk](https://webpack.github.io/docs/code-splitting.html#chunk-content) is Webpack's unit of code-splitting. This plugin' chunk consolidation strategy helps us split our bundled vendor code from our bundled application code, which *dramatically reduces* rebuild and browser loading time in development.

Currently, Tower is split into two output bundles: `tower.vendor.js` and `tower.js`. This would be the plugin configuration to update to additionally split application code into more portable components (example: for usage in the Insights UI).

* [DefinePlugin](https://webpack.github.io/docs/list-of-plugins.html#defineplugin) - injects a module that behaves like a global constant, which can be defined/configured as compile time. Tower uses this plugin to allow command-line arguments passed in at build time to be consumed by application code. 

* [UglifyJSPlugin](https://webpack.github.io/docs/list-of-plugins.html#uglifyjsplugin) (production-only) - removes whitespace and minifies output. The mangle option can be used for an addiction layer of obfuscation, but it can also cause namespace issues.

## <a name="add-upgrade-remove-vendor-module">Add / remove a vendor module</a>

First, [install the package via npm](#add-upgrade-remove-npm-package). If the package doesn't export its contents as a CommonJS, AMD, or SystemJS module you will need to [write a module loader](https://webpack.github.io/docs/how-to-write-a-loader.html).

Not all packages correctly import their own dependencies. Some packages (notable: most jquery plugins) assume a certain dependency will already be in the global namespace. You will need to shim dependencies into these modules using Webpack's [export loader](https://webpack.github.io/docs/shimming-modules.html#exporting).

To bundle a new dependency in `tower.vendor.js`, add it to the `vendorPkgs` array in `webpack.config.js`. 

## <a name="loading-modules">Strategies: loading a module</a>

Webpack ingests code through a concept called a `loader`. [What is a loader?, exactly?](http://webpack.github.io/docs/using-loaders.html#what-are-loaders) 

Loaders can be chained together to perform a complex series of transformations and exports, or used in isolation to target a specific module. 

The Webpack loaders used by Tower:

[Babel loader](https://github.com/babel/babel-loader) - loads files matching a pattern
[imports loader](https://github.com/webpack/imports-loader) - shims dependency namespace, or constrains our own module loading strategies for this package (e.g. prefer to use CJS because AMD strategy is broken in package)



# <a name="grunt">Grunt</a>

[Grunt](http://gruntjs.com/) is a modular task runner. Functionally, it serves the same purpose as a Makefile or set of bash scripts. Grunt helps normalize the interfaces between disparate pieces of tooling. For purposes of Tower, Grunt also simplifies managing the lifecycle of concurrent child processes. 

## <a name="grunt-what-do">What does Grunt handle?</a>a>

Grunt cleans up build artifacts, copies source files, lints, runs 18n text extraction & compilation, and transforms LESS to CSS. 

Other development-only Grunt tasks will poll for file changes, run tasks when a subset of files changes, and raise an instance of BrowserSync (reloads browser on built changes) proxied to an instance of the Django API, running in a native Docker container or container inside of a Docker Machine. 

Grunt internally uses minimatch [file globbing patterns](http://gruntjs.com/configuring-tasks#globbing-patterns)

## <a name="add-remove-upgrade-grunt-tasks"> Add / change / remove a Grunt task</a>

Grunt tasks live in `awx/ui/grunt-tasks/` and are organized in a file-per-plugin pattern. 

The plugin `load-grunt-configs` will automatically load and register tasks read from the configuration files in `awx/ui/grunt-tasks`. This reduces the amount of boilerplate required to write, load, register, each task configuration.


FEach task may be configured with a set of default option, plus additional targets that inherit or override defaults. For example, all tasks in `grunt-tasks/clean.js` run with `-f` or `--force` flag. `grunt-contrib-clean`

```javascript
module.exports = {
    options: { force: true },
    static: 'static/*',
    coverage: 'coverage/*',
    tmp: '../../tmp',
    jshint: 'coverage/jshint.xml'
};
```

## <a name="grunt-task-concurrency">Grunt task concurrency</a>

By default, Grunt tasks are run in a series. [grunt-concurrent] is a plugin that allows us to parallelize certain tasks, to speed up the overall build process. 

Note: certain polling tasks *must always be run on a thread that remains alive*. For example, the `webpack` tasks interact with Webpack's API. Therefor when Webpack's `livereload` option is on, Grunt `webpack` tasks should be spawned in series prior to Grunt `watch` tasks.

# <a name="karma"> Karma </a>

`karma.conf.js` is a generic configuration shared between developer and CI unit test runs.

The base configuration is suitable for live development. Additional command-line arguments supplement this general config to suit CI systems. 

An [npm script](#npm-scripts) interface is provided to run either of these configurations: `npm test` (base) `npm test:ci`

# <a name="Interfaces & Environments">Interfaces & Environments</a>

The UI build system is intended for use through [NPM scripts](https://docs.npmjs.com/misc/scripts). NPM scripts are preferable to just running `grunt sometask` because `npm run` will look for `node_modules/.bin` executables, allowing us to manage CI/release executable versions through `package.json`. You would otherwise have to append these to the executor's $PATH. 

`npm run` targets are run in a shell, which makes them a flexible way of mixing together Python, Ruby, Node, or other CLI tooling in a project.

## <a name="npm-scripts">Tower's NPM script targets</a>

Below is a reference of what each script target does in human language, and then what you can expect the script to execute.

------- 

Builds a development version of the UI with a BrowserSync instance proxied to a Docker Machine
```bash
$ DOCKER_MACHINE_NAME=default npm run build-docker-machine
$ ip=$(docker-machine ip $DOCKER_MACHINE_NAME); npm set ansible-tower:django_host ${ip}; grunt dev;
```

Builds a development version of the UI with a BrowserSync instance proxied to a native Docker container
```bash
$ DOCKER_CID=1a2b3c4d5e npm run build-docker
$ ip=`docker inspect --format '{{ .NetworkSettings.IPAddress }}' $DOCkER_CID` | npm set config ansible-tower:django_host ${ip}; grunt dev;
```

Builds a development version of the UI. No filesystem polling. Re-run after each new revision.
```bash
$ npm run build-devel
```

Builds a production version of the UI.
```bash
$ npm run build-release
```

Launches unit test runners in assorted browsers. Alias for `npm run test`
```bash
$ npm test
```

Launches unit test runners headless in PhantomJS. Alias for `npm run test:ci`
```bash
$ npm test:ci
```

Extracts i18n string markers to a .pot template.
```bash
$ npm run pot
```

Builds i18n language files with regard to .pot.
```bash
$ npm run languages
```

