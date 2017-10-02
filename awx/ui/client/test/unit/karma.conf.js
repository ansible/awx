const webpackConfig = require('../../../build/webpack.test.js');

module.exports = config => {
    config.set({
        basePath: '',
        singleRun: true,
        autoWatch: false,
        colors: true,
        frameworks: ['jasmine'],
        browsers: ['PhantomJS'],
        reporters: ['progress'],
        files: [
            '../../../client/src/vendor.js',
            '../../../client/src/app.js',
            '../../../client/src/**/*.html',
            './index.js',
        ],
        plugins: [
            'karma-webpack',
            'karma-jasmine',
            'karma-phantomjs-launcher',
            'karma-html2js-preprocessor'
        ],
        preprocessors: {
            '../../../client/src/vendor.js': 'webpack',
            '../../../client/src/app.js': 'webpack',
            '../../../client/src/**/*.html': 'html2js',
            './index.js': 'webpack'
        },
        webpack: webpackConfig,
        webpackMiddleware: {
            noInfo: 'errors-only'
        }
    });
};