jQuery Sparklines
=================

This jQuery plugin makes it easy to generate a number of different types
of sparklines directly in the browser, using online a line of two of HTML 
and Javascript.

The plugin has no dependencies other than jQuery and works with all modern 
browsers and also Internet Explorer 6 and later (excanvas is not required
for IE support).

See the [jQuery Sparkline project page](http://omnipotent.net/jquery.sparkline/)
for live examples and documentation.

## License

Released under the New BSD License

(c) Splunk, Inc 2012


## About this fork

* The intent of this fork is to build the Javascript files with Grunt 0.4 and to check the built files into the repo.
* The min file is minified using [UglifyJS](https://github.com/mishoo/UglifyJS) with default settings.
* Checking in built files is [not what the original author wants](https://github.com/gwatts/jquery.sparkline/pull/77) in his repo.
* So why does this fork do that? Well, the built files will then be available to developers who use jquery.sparkline and use Bower for dependency management and Grunt to pluck the files they need in their project. This lets the developer avoid having to run Grunt in dependency directories (eg, node_modules) before running their own builds.
* In order to allow for tag level targeting via Bower, new tags will be made, starting at 2.1.3
