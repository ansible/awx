// Karma configuration
// Generated on Mon Aug 04 2014 21:17:04 GMT-0400 (EDT)

module.exports = function(config) {
    config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['mocha', 'chai', 'sinon-chai', 'chai-as-promised'],
    // list of files / patterns to load in the browser
    files: [
        '../static/dist/tower.concat.js',
        '../static/lib/angular-mocks/angular-mocks.js',
        '../static/lib/ember-cli-test-loader/test-loader.js',
        '../static/dist/tests/**/*.js',
        '../tests/unit.js'
    ],


    // list of files to exclude
    exclude: [
      '../static/js/awx.min.js'
    ],


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['dots', 'progress'],

    client: {
      mocha: {
        ui: 'bdd'
      }
    },


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Chrome'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false

    });
};
