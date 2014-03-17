// Karma configuration
// Generated on Thu Feb 27 2014 22:39:50 GMT-0500 (EST)

module.exports = function(config) {
  config.set({

    // base path, that will be used to resolve files and exclude
    basePath: '../',


    // frameworks to use
    frameworks: ['jasmine'],

    // list of files / patterns to load in the browser
    files: [
    'bower_components/jquery/dist/jquery.min.js',
    'bower_components/jqueryui/ui/minified/jquery-ui.min.js',
    'bower_components/twitter/dist/js/bootstrap.min.js',
    'bower_components/timezone-js/src/date.js',
    'bower_components/angular-tz-extensions/packages/jstimezonedetect/jstz.min.js',
    'bower_components/underscore/underscore.js',
    'bower_components/rrule/lib/rrule.js',
    'bower_components/angular/angular.min.js',
    'bower_components/angular-mocks/angular-mocks.js',
    'bower_components/angular-route/angular-route.min.js',
    'bower_components/angular-tz-extensions/lib/angular-tz-extensions.js',
    'lib/angular-scheduler.js',
    'tests/GetRRule.js',

    // fixtures
    { pattern: 'bower_components/angular-tz-extensions/tz/data/*', watched: false, served: true, included: false }
    ],


    // list of files to exclude
    exclude: [
      
    ],


    // test results reporter to use
    // possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_DEBUG,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // Start these browsers, currently available:
    // - Chrome
    // - ChromeCanary
    // - Firefox
    // - Opera (has to be installed with `npm install karma-opera-launcher`)
    // - Safari (only Mac; has to be installed with `npm install karma-safari-launcher`)
    // - PhantomJS
    // - IE (only Windows; has to be installed with `npm install karma-ie-launcher`)
    browsers: ['Firefox','Chrome'],


    // If browser does not capture in given timeout [ms], kill it
    captureTimeout: 60000,


    // Continuous Integration mode
    // if true, it capture browsers, run tests and exit
    singleRun: false
  });
};
