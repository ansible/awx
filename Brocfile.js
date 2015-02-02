/* jshint node: true */

var flatten = require('lodash/array/flatten');
var isUndefined = require('lodash/lang/isUndefined');
var path = require('path');
var parseArgs = require('minimist');
var mergeTrees = require('broccoli-merge-trees');
var uglifyFiles = require('broccoli-uglify-sourcemap');
var concatFiles = require('broccoli-sourcemap-concat');
var compileLess = require('broccoli-less-single');
var gzip = require('broccoli-gzip');
var debug = require('broccoli-stew').debug;

// Get extra args after '--'
var allArgs = parseArgs(process.argv.slice(2), { '--': true });
var args = parseArgs(allArgs['--']);

var shouldCompress = isUndefined(args.compress) ? false : args.compress;
var debugMode = isUndefined(args.debug) ? false : args.debug;
var silentMode = isUndefined(args.silent) ? false : args.silent;

var vendorFiles =
    [ 'jquery/dist/jquery.js',
      'angular/angular.js',
      'angular-route/angular-route.js',
      'angular-resource/angular-resource.js',
      'angular-cookies/angular-cookies.js',
      'angular-sanitize/angular-sanitize.js',
      'angular-md5/angular-md5.js',
      'jquery-ui/jquery-ui.js',
      'bootstrap/dist/js/bootstrap.js',
      'js-yaml/dist/js-yaml.js',
      'select2/select2.js',
      'angular-animate/angular-animate.js',
      'angular-tz-extensions/packages/jstimezonedetect/jstz.js',
      'socket.io-client/dist/socket.io.js',
      'd3js/build/d3.v3.js',
      'novus-nvd3/nv.d3.js',
      'angular-codemirror/lib/AngularCodeMirror.js',
      'timezone-js/src/date.js',
      'underscore/underscore.js',
      'rrule/lib/rrule.js',
      'rrule/lib/nlp.js',
      'angular-tz-extensions/lib/angular-tz-extensions.js',
      'angular-scheduler/lib/angular-scheduler.js',
      'angular-filters/dist/angular-filters.js',
      'bootstrap/dist/js/bootstrap.js',
      'codemirror/lib/codemirror.js',
      'd3Donut/d3Donut.js',
      'jPushMenu/jPushMenu.js',
      'jQuery.dotdotdot/src/js/jquery.dotdotdot.js',
      'jquery-ui/jquery-ui.js',
      'js-yaml/dist/js-yaml.js',
      'lrInfiniteScroll/lrInfiniteScroll.js',
      'scrollto/lib/jquery-scrollto.js',
      'select2/select2.js',
      'sizzle/dist/sizzle.js',
      'ansible/*.js'
    ];

function log() {
    var msgs = Array.prototype.splice.apply(arguments);

    if (!silentMode) {
        console.log.apply(null, msgs);
    }
}

function prependLibDir(file) {
    return path.join('lib', file);
}

vendorFiles = vendorFiles.map(prependLibDir);

var root = 'awx/ui/static';
var app = root;

function log(msg, obj) {
    console.log(msg + ":", obj);
    return obj;
}

app = concatFiles(app,
        {   outputFile: 'tower.concat.js',
            inputFiles: flatten([vendorFiles, ['js/**/*.js', 'js/app.js', 'js/config.js', 'js/local_config.js']])
        });

app = debug(app, {name: 'concat'});

var styles = compileLess(path.join(root, 'less'), 'ansible-ui.less', 'tower.min.css');

app = mergeTrees([app, styles]);

if (shouldCompress) {
    app = uglifyFiles(app);
    app = gzip(app,
                {   keepUncompressed: true,
                    extensions: ['js', 'css']
                });
}

module.exports = app;
