# MAJOR REFACTOR

As of mid April, 2014, NVD3 is undergoing a major internal refactoring. While we wanted to make it in such a way that it would be a perfectly backwards compatible minor version release, we cannot do so. There are a half-dozen side and corner cases in the current code base, that, while we could call them "bugs", are just poorly implemented features. Because of this, we are announcing heavy development on the 2.0 NVD3 line, which will bring a sane internal structure and numerous API and development enhancements.

The code is on the branch at [refactor/2.0.0-dev](https://github.com/novus/nvd3/tree/refactor/2.0.0-dev). It is currently about 4/5ths functional, and we are working through finishing the tests for the last few parameters. The commonly used charts are there, and any outstanding or new pull requests will need to rebase and target that. Of course, if you want to implement some of those features, that would also be great!

For more information on the refactored architecture and approach, please see the recent blog posts on  [architecture](http://nvd3.org/blog/2014/03/architecture/) and [chart drawing lifecycle](http://nvd3.org/blog/2014/03/nvd3-chart-drawing-lifecycle/).

For now, any users of NVD3 still get 1.1.15-beta.

# NVD3 - v1.1.15-beta
## Release notes for version 1.1.15 beta
* Various fixes across the board

## Overview
A reusable chart library for d3.js.

NVD3 may change from its current state, but will always try to follow the style of d3.js.

You can also check out the [examples page](http://nvd3.org/ghpages/examples.html).
**Note:** The examples on nvd3.org are outdated.  For examples on how to use the latest NVD3, please checkout the **examples/** directory in the repository.

---

# Current development focus

- Getting documentation up.
- Unifying common API functions between charts.
- Bug fixes that come up.

---

# Installation Instructions

`d3.v3.js` is a dependency of `nv.d3.js`. Be sure to include in in your project, then:
Add a script tag to include `nv.d3.js` OR `nv.d3.min.js` in your project.
Also add a link to the `nv.d3.css` file.

See wiki -> Documentation for more detail

---

If one of [the existing models](https://github.com/novus/nvd3/tree/master/src/models) doesn't meet your needs, fork the project, implement the model and an example using it, send us a pull request, for consideration for inclusion in the project.

We cannot honor all pull requests, but we will review all of them.

Please do not aggregate pull requests. Aggregated pull requests are actually more difficult to review.

We are currently changing our branch structure so that master will be gauranteed stable. In addition, there is now a "development" branch. This branch reflects the latest changes to NVD3 and is not necessarily stable.

---

## Minifying your fork:

### Using Make
The Makefile requires [UglifyJS](https://github.com/mishoo/UglifyJS) and [CSSMin](https://github.com/jbleuzen/node-cssmin)

The easiest way to install UglifyJS and CSSMin is via npm. Run `npm install -g uglify-js cssmin`. After installing verify the setup by running `uglifyjs --version` and `cssmin --help`.

Once you have the `uglifyjs` and `cssmin` commands available, running `make` from your
fork's root directory will rebuild both `nv.d3.js` and `nv.d3.min.js`.

    make # build nv.d3.js and nv.d3.css and minify
    make nv.d3.js # Build nv.d3.js
    make nv.d3.min.js # Minify nv.d3.js into nv.d3.min.js
    make nv.d3.css # Build nv.d3.css
    make nv.d3.min.css # Minify nv.d3.css into nv.d3.min.css
    make clean # Delete nv.d3.*js and nv.d3.*css


*Without UglifyJS or CSSMin, you won't get the minified versions when running make.**

### Using Grunt

You can use grunt instead of makefile to build js file. See more about [grunt](http://gruntjs.com/).
***[Nodejs](http://nodejs.org/) must be installed before you can use grunt.***
Run `npm install` in root dir to install grunt and it's dependencies.

Then, you can use these commands:

    grunt # build nv.d3.js
    grunt production # build nv.d3.js and nv.d3.min.js
    grunt watch # watch file changes in src/, and rebuild nv.d3.js, it's very helpful when delevop NVD3
    grunt lint # run jshint on src/**/*.js

**We ask that you DO NOT minify pull requests...
If you need to minify please build pull request in separate branch, and
merge and minify in your master.

## Supported Browsers
NVD3 runs best on WebKit based browsers.

* **Google Chrome: latest version (preferred)**
* **Opera 15+ (preferred)**
* Safari: latest version
* Firefox: latest version
* Internet Explorer: 9 and 10
