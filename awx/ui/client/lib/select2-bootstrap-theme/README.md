A Select2 v4 [Theme](https://select2.github.io/examples.html#themes) for Bootstrap 3

**Note: Work in progress – depending on your use case, select2-bootstrap-theme might not be production-ready yet!**

Demonstrations available at
http://select2.github.io/select2-bootstrap-theme/

Tested with Bootstrap v3.3.5 and Select2 v4.0.0
in latest Chrome.

##### Installation

The Select2 Bootstrap Theme only works with Select2 v4.x. Applying the theme requires `select2-bootstrap.css` referenced after the default `select2.css` that comes with Select2:

    <link rel="stylesheet" href="select2.css">
    <link rel="stylesheet" href="select2-bootstrap.css">

To apply the theme, tell Select2 to do so by passing `bootstrap` to the [`theme`](https://select2.github.io/examples.html#themes) option when initializing Select2:

    $( "#dropdown" ).select2({
        theme: "bootstrap"
    });

##### Changelog

###### 0.1.0-beta.4

 * Added missing styles for `.select2-container--focus`. [[#18](https://github.com/select2/select2-bootstrap-theme/issues/18)]
 * Added support for Bootstrap's [`.form-inline`](http://getbootstrap.com/css/#forms-inline). [[#13](https://github.com/select2/select2-bootstrap-theme/pull/13)]
 * Added basic styles for `.select2-selection__clear` in `.select2-selection--multiple`. [[#11](https://github.com/select2/select2-bootstrap-theme/issues/11)]
 * Brought Less source in line with the Sass version and fixed Less patch file and test. [[`3e86f34](https://github.com/select2/select2-bootstrap-theme/commit/3e86f34f6c94302cd8b4d6c3d751c5fb70fe61f6)]

###### 0.1.0-beta.3

 * Fixed specifity problems with `.form-control.select2-hidden-accessible`.

###### 0.1.0-beta.2

 * Added Less version.

###### 0.1.0-beta.1

##### Contributing

The project offers [Less](http://lesscss.org/) and [Sass](http://sass-lang.com/) sources for building `select2-bootstrap.css`; both make use of variables from either [Bootstrap](https://github.com/twbs/bootstrap) (Less) or [Bootstrap for Sass](https://github.com/twbs/bootstrap-sass). The demo pages are built using [Jekyll](http://jekyllrb.com/) and there are a bunch of [Grunt](http://gruntjs.com/) tasks to ease development.

With [Ruby](https://www.ruby-lang.org/en/downloads/) and [RubyGems](http://rubygems.org/pages/download), [Jekyll](http://jekyllrb.com/), [Bower](http://bower.io/), [node.js](http://nodejs.org/), [Less](http://lesscss.org/) and [Sass](http://sass-lang.com/) installed, run

    npm install && bower install

to install all necessary development dependencies.

 * `grunt copy` copies assets from `components` to `_jekyll` – use this in case a new version of Twitter Bootstrap or Select2 are out and need to be tested
 * `grunt build` builds `docs`
 * `grunt serve` builds `docs` and serves them via Jekyll's `--watch` flag on http://localhost:4000
 * `grunt watch` watches for changes in `src/select2-bootstrap.scss` ([livereload](https://github.com/gruntjs/grunt-contrib-watch#optionslivereload) is enabled)

Develop in `src/select2-bootstrap.scss` and test your changes using `grunt watch` and `grunt serve`. Ideally, port your changes to `lib/select2-bootstrap.less` and make sure tests are passing to verify that Less and Sass compile down to the target CSS via `npm test`.
