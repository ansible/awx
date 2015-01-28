var mergeTrees = require('broccoli-merge-trees');
var uglifyFiles = require('broccoli-uglify-sourcemap');
var concatFiles = require('broccoli-sourcemap-concat');
var pickFiles = require('broccoli-static-compiler');
var findBowerTrees = require('broccoli-bower');

var vendorMin = concatFiles('awx/ui/static/lib', {
  sourceMapConfig: {
    enabled: false
  },
  outputFile: '/out/vendor-min.js',
  inputFiles: [
    'jquery/dist/jquery.min.js',
    'angular/angular.min.js',
    'angular-route/angular-route.min.js',
    'angular-resource/angular-resource.min.js',
    'angular-cookies/angular-cookies.min.js',
    'angular-sanitize/angular-sanitize.min.js',
    'angular-md5/angular-md5.min.js',
    'jquery-ui/jquery-ui.min.js',
    'bootstrap/dist/js/bootstrap.min.js',
    'js-yaml/dist/js-yaml.min.js',
    'select2/select2.min.js',
    'angular-animate/angular-animate.min.js',
    'angular-tz-extensions/packages/jstimezonedetect/jstz.min.js',
    'socket.io-client/dist/socket.io.min.js',
    'd3js/build/d3.v3.min.js',
    'novus-nvd3/nv.d3.min.js'
  ]
});

var sourceMaps = pickFiles('awx/ui/static/lib', {
  srcDir: '/',
  destDir: 'out',
  files: [
    'angular-animate/angular-animate.min.js.map',
    '**/*.min.js.map',
    '**/*.min.map'
  ]
});

var vendorMaps = concatFiles(sourceMaps, {
  sourceMapConfig: {
    enabled: false
  },
  outputFile: '/out/vendor-min.js.map',
  inputFiles: ['out/**/*.map']
});

var vendorMinWithMaps = mergeTrees([vendorMin, vendorMaps]);

var vendorConcat = concatFiles('awx/ui/static/lib', {
  outputFile: 'out/vendor-concat.js',
  inputFiles: [
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
  ]
});

function uglifyFast(tree, opts) {
  opts = opts || {};
  opts.compress = false;
  opts.mangle = false;
  opts.sourceMapIncludeSources = false;
  return uglifyFiles(tree, opts);
}

function uglifySlow(tree) {
  return uglifyFiles(tree);
}

var ansibleLib = pickFiles('awx/ui/static/lib/ansible', {
  srcDir: '/',
  destDir: 'out'
});

var src = pickFiles('awx/ui/static/js', {
  srcDir: '/',
  destDir: 'out'
});

var filesToConcat = mergeTrees([vendorConcat, ansibleLib, src]);

console.log('here1');
var concated = concatFiles(filesToConcat, {
  outputFile: '/out/tower-concat.js',
  inputFiles: ['out/**/*.js']
});
var merged = mergeTrees([vendorMinWithMaps, concated], {
                                    description: "TreeMerge (vendor and sourcemaps)",
})
var minified = uglifyFast(merged, {
  outSourceMap: 'tower-concat.map'
});

var finalMap = pickFiles(minified, {
  srcDir: '/out',
  destDir: '',
  files: ['tower-concat.map']
});

var finalized = concatFiles(minified, {
  sourceMapConfig: {
    enabled: false
  },
  outputFile: '/tower-concat.js',
  inputFiles: ['out/vendor-min.js', 'out/tower-concat.js']
});

module.exports = mergeTrees([finalMap, finalized]);
